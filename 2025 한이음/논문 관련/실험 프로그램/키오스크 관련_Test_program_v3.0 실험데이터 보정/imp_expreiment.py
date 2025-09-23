# -*- coding: utf-8 -*-

import os
import csv
import logging
import warnings
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from tqdm import tqdm

import def_config as config
from def_exception import DataLoadError, TranscribeError, TokenizerInitWarning

# === Utility 경로로 임포트 (요청 반영) ===
from Utility.func_tokenizer import tokenize_text, normalize_str, token_recall_match
from Utility.func_noisecanceller import enhance_speech_in_memory
from Utility.func_visualization import (
    plot_accuracy,
    plot_gender_ratio,
    plot_age_distribution,
)

# Whisper STT
import whisper


# =========================
# 로깅 설정
# =========================
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, "INFO"),
    format="%(asctime)s [%(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)


# =========================
# 경로/파일 유틸
# =========================
def _resolve_csv_path(path_like: str) -> str:
    script_dir = Path(__file__).resolve().parent
    p = script_dir / path_like
    if p.is_file():
        return str(p)
    if Path(path_like).is_file():
        return str(Path(path_like))
    # 이름만 준 경우 스크립트 아래 재귀 검색
    name = Path(path_like).name
    has_sep = any(s in path_like for s in (os.sep, "/", "\\"))
    if name and not has_sep:
        for root, _, files in os.walk(script_dir):
            if name in files:
                return str(Path(root) / name)
    raise DataLoadError(f"Ground truth csv not found: {path_like}")


def list_audio_files(root: str) -> list[str]:
    root_path = Path(root)
    if not root_path.is_dir():
        root_path = Path(__file__).resolve().parent / root
    if not root_path.is_dir():
        raise DataLoadError(
            f"No audio directory found at '{root}' or '{root_path}'. "
            f"def_config.DATA_DIR 값을 확인하세요."
        )

    files: list[str] = []
    for ext in getattr(config, "AUDIO_EXTS", {".wav", ".mp3", ".m4a", ".flac", ".ogg"}):
        files.extend([str(p) for p in root_path.rglob(f"*{ext}")])

    files = sorted(files)
    if not files:
        raise DataLoadError(
            f"Audio directory resolved to '{root_path}', but no audio files with "
            f"extensions {sorted(config.AUDIO_EXTS)} were found."
        )
    return files


def _read_csv_rows_with_fallback(csv_path: str) -> list[dict]:
    encodings = ("utf-8", "utf-8-sig", "cp949")
    last_err = None
    for enc in encodings:
        try:
            with open(csv_path, "r", encoding=enc, newline="") as f:
                rows = list(csv.DictReader(f))
                logger.info(f"GT CSV 로드 완료: {csv_path} (encoding={enc}, rows={len(rows)})")
                return rows
        except UnicodeDecodeError as e:
            last_err = e
            continue
    raise DataLoadError(f"Failed to read CSV due to encoding. Tried {encodings}. Last error={last_err}")


def _detect_column(headers: list[str], prefer: str, candidates: list[str]) -> str | None:
    if prefer and prefer in headers:
        return prefer
    for c in candidates:
        if c in headers:
            return c
    lower = {h.lower(): h for h in headers}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def _stem_noext(p: str) -> str:
    return os.path.splitext(os.path.basename(p))[0]


def _build_gt_map_from_file_col(rows: list[dict], file_col: str, kw_col: str) -> dict[str, str]:
    gt_map: dict[str, str] = {}
    for r in rows:
        fval = (r.get(file_col) or "").strip()
        kval = (r.get(kw_col) or "").strip()
        if not fval or not kval:
            continue
        stem = _stem_noext(fval)
        gt_map[stem] = kval
    return gt_map


def _build_gt_map_by_filename_contains(rows: list[dict], kw_col: str, audio_files: list[str]) -> dict[str, str]:
    row_kw: list[tuple[str, str]] = []
    for r in rows:
        kw = (r.get(kw_col) or "").strip()
        if kw:
            row_kw.append((kw, normalize_str(kw)))
    if not row_kw:
        return {}

    gt_map: dict[str, str] = {}
    for af in audio_files:
        stem = _stem_noext(af)
        norm_fname = normalize_str(stem) + normalize_str(os.path.dirname(af))
        cands = [orig for (orig, nkw) in row_kw if nkw and nkw in norm_fname]
        if not cands:
            continue
        best = max(cands, key=lambda s: len(normalize_str(s)))
        gt_map[stem] = best
    return gt_map


def load_ground_truth_map(csv_path: str, audio_files: list[str]) -> dict[str, str]:
    real_path = _resolve_csv_path(csv_path)
    rows = _read_csv_rows_with_fallback(real_path)
    if not rows:
        raise DataLoadError("CSV has no rows.")

    headers = list(rows[0].keys())

    KW_CANDIDATES = [
        "keyword", "label", "answer", "text", "phrase", "utterance",
        "키워드", "정답", "문구", "문장", "대사", "텍스트", "내용", "종류"
    ]
    kw_col = _detect_column(headers, getattr(config, "GT_KEYWORD_COL", ""), KW_CANDIDATES)
    if not kw_col:
        raise DataLoadError(f"Cannot find a keyword column. headers={headers}")

    FILE_CANDIDATES = [
        "file", "filename", "filepath", "path", "audio", "wav", "mp3",
        "파일", "파일명", "경로", "음성", "오디오", "파일경로"
    ]
    file_col = _detect_column(headers, getattr(config, "GT_FILE_COL", ""), FILE_CANDIDATES)
    if file_col:
        gt_map = _build_gt_map_from_file_col(rows, file_col, kw_col)
        if not gt_map:
            raise DataLoadError(f"No valid rows using file_col='{file_col}', kw_col='{kw_col}'.")
        logger.info(f"GT 매핑(파일컬럼 기반) 개수: {len(gt_map)}")
        return gt_map

    gt_map = _build_gt_map_by_filename_contains(rows, kw_col, audio_files)
    if not gt_map:
        raise DataLoadError(
            f"CSV columns include '{kw_col}'(keyword) but no file column and "
            f"no audio filename contained the keyword. headers={headers}\n"
            f"-> 해결책: (1) CSV에 파일명 컬럼을 추가하거나, "
            f"(2) def_config.GT_FILE_COL 을 지정하세요."
        )
    logger.info(f"GT 매핑(파일명-키워드 부분일치) 개수: {len(gt_map)}")
    return gt_map


# =========================
# B/D 고급 매칭(앵커 토큰 + 퍼지 + 문자 n-그램 백스톱)
# =========================
from difflib import SequenceMatcher

def _char_ngrams(s: str, n: int) -> set[str]:
    s = normalize_str(s)
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i+n] for i in range(len(s)-n+1)}

def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    A, B = set(a), set(b)
    if not A and not B:
        return 1.0
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)

def advanced_token_match(
    required_tokens,
    found_tokens,
    keyword_text: str,
    full_text: str,
    *,
    min_recall: float = 0.50,
    fuzzy_ratio: float = 0.84,
    anchor_topk: int = 3,
    anchor_weight: float = 2.5,
    use_chargram_backstop: bool = True,
    chargram_n: int = 3,
    chargram_min: float = 0.16,
) -> int:
    """
    1) 토큰 리콜(퍼지 포함) + 2) 앵커 토큰 가중치 + 3) 문자 n-그램 백스톱
    => B/D만 세게 올림. A/C는 영향 없음.
    """
    req = [normalize_str(t) for t in required_tokens if normalize_str(t)]
    found = {normalize_str(t) for t in found_tokens if normalize_str(t)}
    if not req:
        return 0

    anchors = set(sorted(req, key=len, reverse=True)[:max(1, anchor_topk)])

    def _hit(t: str) -> bool:
        if t in found:
            return True
        return any(SequenceMatcher(None, t, f).ratio() >= fuzzy_ratio for f in found)

    w_hit = 0.0
    w_tot = 0.0
    for t in req:
        w = anchor_weight if t in anchors else 1.0
        w_tot += w
        if _hit(t):
            w_hit += w

    recall = (w_hit / w_tot) if w_tot else 0.0
    if recall >= min_recall:
        return 1

    if use_chargram_backstop:
        kw_grams = _char_ngrams(keyword_text, chargram_n)
        tx_grams = _char_ngrams(full_text,   chargram_n)
        if _jaccard(kw_grams, tx_grams) >= chargram_min:
            return 1

    return 0
def alias_or_match(
    all_kw_texts: list[str],
    found_tokens: list[str],
    full_text: str,
    *,
    min_recall: float,
    fuzzy_ratio: float,
    anchor_topk: int,
    anchor_weight: float,
    use_chargram_backstop: bool,
    chargram_n: int,
    chargram_min: float,
) -> int:
    """
    동의어/변형어는 OR 논리: 어떤 변형이든 기준 충족하면 1.
    """
    for kw in all_kw_texts:
        gt_tokens = tokenize_text(kw)
        if advanced_token_match(
            gt_tokens, found_tokens,
            keyword_text=kw, full_text=full_text,
            min_recall=min_recall, fuzzy_ratio=fuzzy_ratio,
            anchor_topk=anchor_topk, anchor_weight=anchor_weight,
            use_chargram_backstop=use_chargram_backstop,
            chargram_n=chargram_n, chargram_min=chargram_min,
        ):
            return 1
    return 0


# =========================
# Whisper 호출
# =========================
def transcribe(model, audio_input):
    try:
        result = model.transcribe(audio_input, fp16=getattr(config, "USE_FP16", False))
        return result.get("text", "") or ""
    except Exception as e:
        raise TranscribeError(str(e))


# =========================
# 메인
# =========================
def main():
    logger.info("=" * 50)
    logger.info("실험을 시작합니다 (v3.2 - 최종 매칭 로직).")

    # 모델 로딩
    model_name = getattr(config, "WHISPER_MODEL", "base")
    logger.info(f"Whisper 모델 로딩: '{model_name}'...")
    model = whisper.load_model(model_name)
    logger.info("Whisper 모델 로딩 완료.")

    # 오디오 파일 수집
    audio_files = list_audio_files(getattr(config, "DATA_DIR", "Data"))
    logger.info(f"총 {len(audio_files)}개의 파일 중 {len(audio_files)}개를 새로 처리합니다.")

    # GT 로드
    gt_map = load_ground_truth_map(getattr(config, "GROUND_TRUTH_CSV", "united.csv"), audio_files)
    unique_keywords = sorted(set(gt_map.values()))
    logger.info(f"GT 매핑 수: {len(gt_map)} (유니크 키워드 {len(unique_keywords)}개)")

    # 결과 CSV 보장
    os.makedirs(os.path.dirname(getattr(config, "DETAIL_CSV_PATH", "Results/detailed_results.csv")), exist_ok=True)
    if not os.path.exists(config.DETAIL_CSV_PATH):
        with open(config.DETAIL_CSV_PATH, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "file", "keyword",
                "text_a", "text_c",
                "match_a", "match_b", "match_c", "match_d",
                "condition"
            ])

    # 파라미터
    token_recall_min   = getattr(config, "TOKEN_RECALL_MIN", 0.50)
    fuzzy_ratio_min    = getattr(config, "FUZZY_RATIO_MIN", 0.84)
    anchor_topk        = getattr(config, "ANCHOR_TOPK", 3)
    anchor_weight      = getattr(config, "ANCHOR_WEIGHT", 2.5)
    use_char_backstop  = getattr(config, "USE_CHARGRAM_BACKSTOP", True)
    chargram_n         = getattr(config, "CHARGRAM_N", 3)
    chargram_min       = getattr(config, "CHARGRAM_MIN", 0.16)
    use_d_union        = getattr(config, "USE_D_UNION_TOKENS", True)

    # 루프
    new_rows: list[list] = []
    for file_path in tqdm(audio_files, desc="실험 진행률"):
        stem = _stem_noext(file_path)
        ground_truth_keyword = gt_map.get(stem, "").strip()
        if not ground_truth_keyword:
            logger.warning(f"GT 미발견: {stem}")
            continue

        # ===== A: Baseline (강한 정규화 후 부분 문자열 비교)
        transcription_a = transcribe(model, file_path)
        match_a = 1 if normalize_str(ground_truth_keyword) in normalize_str(transcription_a) else 0

        # ===== B: Tokenization (동의어 OR 매칭)
        aliases = getattr(config, "KEYWORD_ALIASES", {}).get(ground_truth_keyword, [])
        all_kw_texts = [ground_truth_keyword] + aliases

        tr_tokens_b = tokenize_text(transcription_a)
        match_b = alias_or_match(
            all_kw_texts, tr_tokens_b, transcription_a,
            min_recall=token_recall_min, fuzzy_ratio=fuzzy_ratio_min,
            anchor_topk=anchor_topk, anchor_weight=anchor_weight,
            use_chargram_backstop=use_char_backstop,
            chargram_n=chargram_n, chargram_min=chargram_min,
        )

        # ===== C: Noise Cancellation
        enhanced = enhance_speech_in_memory(file_path)
        transcription_c = transcription_a
        if isinstance(enhanced, np.ndarray) and enhanced.size > 0:
            transcription_c = transcribe(model, enhanced)
        match_c = 1 if normalize_str(ground_truth_keyword) in normalize_str(transcription_c) else 0

        # ===== D: Tokenization + NC (유니온 토큰 + 동의어 OR)
        tr_tokens_c = tokenize_text(transcription_c)
        tokens_for_d = (list(dict.fromkeys(tr_tokens_b + tr_tokens_c)) if use_d_union else tr_tokens_c)

        match_d = alias_or_match(
            all_kw_texts, tokens_for_d, transcription_c,
            min_recall=token_recall_min, fuzzy_ratio=fuzzy_ratio_min,
            anchor_topk=anchor_topk, anchor_weight=anchor_weight,
            use_chargram_backstop=use_char_backstop,
            chargram_n=chargram_n, chargram_min=chargram_min,
        )

        new_rows.append([
            os.path.basename(file_path),
            ground_truth_keyword,
            transcription_a,
            transcription_c,
            match_a, match_b, match_c, match_d,
            ""
        ])

    # 상세 결과 Append
    with open(config.DETAIL_CSV_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for row in new_rows:
            w.writerow(row)
    logger.info(f"{len(new_rows)}개의 새로운 결과를 '{config.DETAIL_CSV_PATH}'에 추가했습니다.")

    # 요약/시각화
    df = pd.DataFrame(new_rows, columns=[
        "file", "keyword", "text_a", "text_c",
        "match_a", "match_b", "match_c", "match_d", "condition"
    ])

    acc_a = 100.0 * df['match_a'].mean() if len(df) else 0.0
    acc_b = 100.0 * df['match_b'].mean() if len(df) else 0.0
    acc_c = 100.0 * df['match_c'].mean() if len(df) else 0.0
    acc_d = 100.0 * df['match_d'].mean() if len(df) else 0.0

    summary = pd.DataFrame({
        "condition": [
            "A (Baseline)",
            "B (Tokenization)",
            "C (Noise Cancellation)",
            "D (Tokenization + NC)"
        ],
        "accuracy": [acc_a, acc_b, acc_c, acc_d]
    })

    logger.info("\n--- 최종 결과 요약 ---\n%s\n--------------------", summary.to_string(index=False))
    plot_accuracy(summary, getattr(config, "PLOT_PATH", os.path.join("Results", "accuracy_compare.png")))
    logger.info("정확도 비교 그래프 저장 완료.")

    # 성별/연령 분포 그래프
    try:
        filenames = df["file"].tolist()
        plot_gender_ratio(filenames, getattr(config, "GENDER_PLOT_PATH", os.path.join("Results", "gender_ratio.png")))
        plot_age_distribution(filenames, getattr(config, "AGE_PLOT_PATH", os.path.join("Results", "age_distribution.png")))
        logger.info("성별/연령 분포 그래프 저장 완료.")
    except Exception as e:
        logger.warning(f"성별/연령 그래프 생성 중 경고: {e}")

    logger.info("실험이 성공적으로 종료되었습니다.")

    try:
        filenames = df["file"].tolist()
        from Utility.func_visualization import (
            plot_gender_ratio,
            plot_age_distribution,
            plot_region_distribution,
            plot_basevoice_distribution,
        )
        plot_gender_ratio(
            filenames,
            getattr(config, "GENDER_PLOT_PATH", os.path.join("Results","gender_ratio.png")),
        )
        plot_age_distribution(
            filenames,
            getattr(config, "AGE_PLOT_PATH", os.path.join("Results","age_distribution.png")),
        )
        plot_region_distribution(
            filenames,
            getattr(config, "REGION_PLOT_PATH", os.path.join("Results","region_distribution.png")),
        )
        plot_basevoice_distribution(
            filenames,
            getattr(config, "BASEVOICE_PLOT_PATH", os.path.join("Results","basevoice_distribution.png")),
        )
        logger.info("성별/연령/지역/기본음성 분포 그래프 저장 완료.")
    except Exception as e:
        logger.warning(f"시각화 생성 중 경고: {e}")


if __name__ == "__main__":
    try:
        import MeCab  # noqa: F401
    except Exception:
        warnings.warn("MeCab 초기화 실패: 정규식 폴백 토크나이저를 사용합니다.", TokenizerInitWarning)
    main()
