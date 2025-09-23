# -*- coding: utf-8 -*-
"""
imp_experiment.py  (v3.2 - 최종 매칭 로직)
- A: 베이스라인(강한 정규화 후 부분 포함)
- B: 토큰화 + 동의어 OR + 퍼지매칭 + (선택) n-그램 백스톱
- C: NC 후 A와 동일
- D: C의 텍스트 토큰 ∪ A의 텍스트 토큰 + B와 동일 매칭
"""
import os, csv, logging, warnings
import numpy as np
import pandas as pd
from tqdm import tqdm

import def_config as config
from def_exception import TranscribeError, TokenizerInitWarning

import whisper

# ---- 유틸 모듈 ----
from Utility.Filemanager import list_audio_files as _list_audio_files
from Utility.Filemanager import build_ground_truth_map as _build_gt_map
from Utility.Tokenizer.func_tokenizer import tokenize_text, normalize_str
from Utility.Noisecanceller.func_noisecanceller import enhance_speech_in_memory
from Utility.Visualization.func_visualization import (
    plot_accuracy, plot_gender_ratio, plot_age_distribution,
    plot_region_distribution, plot_basevoice_distribution
)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, "INFO"),
    format="%(asctime)s [%(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)

# =========================
# 매칭 유틸
# =========================
def _alias_list(kw: str) -> list[str]:
    aliases = getattr(config, "KEYWORD_ALIASES", {}).get(kw, [])
    return [kw] + list(dict.fromkeys([a for a in aliases if a and a != kw]))

def _advanced_token_match(
    required_tokens: list[str],
    found_tokens: list[str],
    *,
    keyword_text: str,
    full_text: str,
    min_recall: float,
    fuzzy_ratio: float,
    anchor_topk: int,
    anchor_weight: float,
    use_chargram_backstop: bool,
    chargram_n: int,
    chargram_min: float,
) -> bool:
    """
    - 토큰 단위 recall 가중치(긴 토큰 앵커 가중)
    - 퍼지 매칭(SequenceMatcher)
    - (선택) 문자 n-그램 자카드 백스톱 (토큰화가 깨진 샘플 보강)
    """
    from difflib import SequenceMatcher

    req = [normalize_str(t) for t in required_tokens if normalize_str(t)]
    found = {normalize_str(t) for t in found_tokens if normalize_str(t)}
    if not req:
        return False

    anchors = set(sorted(req, key=len, reverse=True)[:max(1, anchor_topk)])

    def _hit(t: str) -> bool:
        if t in found:
            return True
        # fuzzy
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
        return True

    if use_chargram_backstop:
        # 문자 n-그램 자카드 (아주 느슨한 백스톱)
        def _ngrams(s: str, n: int) -> set[str]:
            s = normalize_str(s)
            if len(s) < n:
                return {s} if s else set()
            return {s[i:i+n] for i in range(len(s)-n+1)}
        A = _ngrams(keyword_text, chargram_n)
        B = _ngrams(full_text, chargram_n)
        if A and B:
            j = len(A & B) / len(A | B)
            if j >= chargram_min:
                return True
    return False

def _alias_or_match(
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
    # 동의어/변형어는 OR: 하나라도 기준 통과하면 1
    for kw in all_kw_texts:
        gt_tokens = tokenize_text(kw)
        if _advanced_token_match(
            gt_tokens, found_tokens,
            keyword_text=kw, full_text=full_text,
            min_recall=min_recall, fuzzy_ratio=fuzzy_ratio,
            anchor_topk=anchor_topk, anchor_weight=anchor_weight,
            use_chargram_backstop=use_chargram_backstop,
            chargram_n=chargram_n, chargram_min=chargram_min,
        ):
            return 1
    return 0

def _contains_baseline(text: str, kw: str) -> int:
    # A와 동일: 강한 정규화 후 부분문자열 포함
    return 1 if normalize_str(kw) in normalize_str(text) else 0

def _stem_noext(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]

# =========================
# Whisper
# =========================
def _transcribe(model, audio_input):
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

    # 입력 파일
    audio_files = _list_audio_files(getattr(config, "DATA_DIR", "Data"))
    logger.info(f"총 {len(audio_files)}개의 파일을 처리합니다.")

    # GT 매핑
    gt_map = _build_gt_map(
        getattr(config, "GROUND_TRUTH_CSV", "united.csv"),
        audio_files,
        kw_col_hint=getattr(config, "GT_KEYWORD_COL", ""),
        file_col_hint=getattr(config, "GT_FILE_COL", ""),
    )
    unique_keywords = sorted(set(gt_map.values()))
    logger.info(f"GT 매핑 수: {len(gt_map)} (유니크 키워드 {len(unique_keywords)}개)")

    # 결과 CSV 준비
    os.makedirs(os.path.dirname(getattr(config, "DETAIL_CSV_PATH", "Results/detailed_results.csv")), exist_ok=True)
    if not os.path.exists(config.DETAIL_CSV_PATH):
        with open(config.DETAIL_CSV_PATH, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow([
                "file", "keyword",
                "text_a", "text_c",
                "match_a", "match_b", "match_c", "match_d",
                "condition"
            ])

    # 하이퍼파라미터
    token_recall_min   = getattr(config, "TOKEN_RECALL_MIN", 0.50)
    fuzzy_ratio_min    = getattr(config, "FUZZY_RATIO_MIN", 0.84)
    anchor_topk        = getattr(config, "ANCHOR_TOPK", 3)
    anchor_weight      = getattr(config, "ANCHOR_WEIGHT", 2.5)
    use_char_backstop  = getattr(config, "USE_CHARGRAM_BACKSTOP", True)
    chargram_n         = getattr(config, "CHARGRAM_N", 3)
    chargram_min       = getattr(config, "CHARGRAM_MIN", 0.16)
    use_d_union        = getattr(config, "USE_D_UNION_TOKENS", True)

    new_rows = []
    for file_path in tqdm(audio_files, desc="실험 진행률"):
        stem = _stem_noext(file_path)
        gt_kw = (gt_map.get(stem, "") or "").strip()
        if not gt_kw:
            logger.warning(f"GT 미발견: {stem}")
            continue

        # ===== A: Baseline
        text_a = _transcribe(model, file_path)
        match_a = _contains_baseline(text_a, gt_kw)

        # ===== B: Tokenization + 동의어 OR + 퍼지 + (옵션)백스톱
        kw_texts = _alias_list(gt_kw)
        tokens_a = tokenize_text(text_a)
        match_b = _alias_or_match(
            kw_texts, tokens_a, text_a,
            min_recall=token_recall_min, fuzzy_ratio=fuzzy_ratio_min,
            anchor_topk=anchor_topk, anchor_weight=anchor_weight,
            use_chargram_backstop=use_char_backstop,
            chargram_n=chargram_n, chargram_min=chargram_min,
        )

        # ===== C: Noise Cancellation
        enhanced = enhance_speech_in_memory(file_path)
        text_c = text_a
        if isinstance(enhanced, np.ndarray) and enhanced.size > 0:
            text_c = _transcribe(model, enhanced)
        match_c = _contains_baseline(text_c, gt_kw)

        # ===== D: Tokenization + NC (A∪C 토큰 + B와 동일 매칭)
        tokens_c = tokenize_text(text_c)
        tokens_d = list(dict.fromkeys(tokens_a + tokens_c)) if use_d_union else tokens_c
        match_d = _alias_or_match(
            kw_texts, tokens_d, text_c,
            min_recall=token_recall_min, fuzzy_ratio=fuzzy_ratio_min,
            anchor_topk=anchor_topk, anchor_weight=anchor_weight,
            use_chargram_backstop=use_char_backstop,
            chargram_n=chargram_n, chargram_min=chargram_min,
        )

        new_rows.append([
            os.path.basename(file_path),
            gt_kw,
            text_a,
            text_c,
            match_a, match_b, match_c, match_d,
            ""
        ])

    # 상세 결과 저장(append)
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

    # 분포 플롯(선택)
    try:
        filenames = df["file"].tolist()
        plot_gender_ratio(filenames, getattr(config, "GENDER_PLOT_PATH", os.path.join("Results", "gender_ratio.png")))
        plot_age_distribution(filenames, getattr(config, "AGE_PLOT_PATH", os.path.join("Results", "age_distribution.png")))
        plot_region_distribution(filenames, getattr(config, "REGION_PLOT_PATH", os.path.join("Results", "region_distribution.png")))
        plot_basevoice_distribution(filenames, getattr(config, "BASEVOICE_PLOT_PATH", os.path.join("Results", "basevoice_distribution.png")))
        logger.info("성별/연령/지역/기본음성 분포 그래프 저장 완료.")
    except Exception as e:
        logger.warning(f"분포 그래프 생성 경고: {e}")

if __name__ == "__main__":
    try:
        import MeCab  # noqa: F401
    except Exception:
        warnings.warn("MeCab 초기화 실패: 정규식 폴백 토크나이저를 사용합니다.", TokenizerInitWarning)
    main()
