# -*- coding: utf-8 -*-
import os, csv, logging, warnings
import pandas as pd
from tqdm import tqdm

import def_config as config
from def_exception import DataLoadError, TranscribeError, TokenizerInitWarning

# 조건(실험)
from Condition.def_condition1 import run as run_cond1
from Condition.def_condition2 import run as run_cond2
from Condition.def_condition3 import run as run_cond3
from Condition.def_condition4 import run as run_cond4

# 시각화
from Utility.Visualization.func_visualization import (
    plot_accuracy, plot_gender_ratio, plot_age_distribution,
    plot_region_distribution, plot_basevoice_distribution
)

# 파일/경로 유틸
from Utility.Filemanager import (
    stem_noext,
    list_audio_files,
    build_ground_truth_map,
)

import whisper

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, "INFO"),
    format="%(asctime)s [%(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    logger.info("="*50); logger.info("실험을 시작합니다 (v4.1 - Filemanager 분리).")

    # Whisper
    model = whisper.load_model(getattr(config, "WHISPER_MODEL", "base"))
    logger.info("Whisper 모델 로딩 완료.")

    # 데이터
    audio_files = list_audio_files(config.DATA_DIR)
    logger.info(f"총 {len(audio_files)}개 파일 처리.")

    # GT 매핑
    gt_map = build_ground_truth_map(
        config.GROUND_TRUTH_CSV,
        audio_files,
        kw_col_hint=getattr(config, "GT_KEYWORD_COL", ""),
        file_col_hint=getattr(config, "GT_FILE_COL", ""),
    )
    unique_keywords = sorted(set(gt_map.values()))
    logger.info(f"유니크 키워드({len(unique_keywords)}개): {unique_keywords}")

    # 결과 CSV 헤더 보장
    os.makedirs(os.path.dirname(config.DETAIL_CSV_PATH), exist_ok=True)
    if not os.path.exists(config.DETAIL_CSV_PATH):
        with open(config.DETAIL_CSV_PATH, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(
                ["file","keyword","text_a","text_c","match_a","match_b","match_c","match_d","condition"]
            )

    # 실험 루프 (tqdm 진행률 + 파일 단위 예외 방지)
    rows = []
    for file_path in tqdm(audio_files, desc="실험 진행률", ncols=100):
        try:
            stem = stem_noext(file_path)
            gt = (gt_map.get(stem) or "").strip()
            if not gt:
                logger.warning(f"GT 없음: {stem}")
                continue

            text_a, match_a = run_cond1(model, file_path, gt, config)                   # A
            match_b = run_cond2(model, file_path, gt, config, base_text=text_a)         # B
            text_c, match_c = run_cond3(model, file_path, gt, config, base_text=text_a) # C
            match_d = run_cond4(model, file_path, gt, config, text_a=text_a, text_c=text_c) # D

            rows.append([os.path.basename(file_path), gt, text_a, text_c,
                         match_a, match_b, match_c, match_d, ""])
        except Exception as e:
            logger.exception(f"파일 처리 실패: {file_path} → {e}")
            continue

    # 저장
    with open(config.DETAIL_CSV_PATH, "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)
    logger.info(f"{len(rows)}개 결과 저장: {config.DETAIL_CSV_PATH}")

    # 요약/시각화
    df = pd.DataFrame(rows, columns=["file","keyword","text_a","text_c","match_a","match_b","match_c","match_d","condition"])
    acc = lambda col: 100.0 * df[col].mean() if len(df) else 0.0
    summary = pd.DataFrame({
        "condition": ["A (Baseline)","B (Tokenization)","C (Noise Cancellation)","D (Tokenization + NC)"],
        "accuracy": [acc("match_a"), acc("match_b"), acc("match_c"), acc("match_d")],
    })
    logger.info("\n--- 최종 결과 요약 ---\n%s\n--------------------", summary.to_string(index=False))
    plot_accuracy(summary, config.PLOT_PATH)

    try:
        fn = df["file"].tolist()
        plot_gender_ratio(fn, config.GENDER_PLOT_PATH)
        plot_age_distribution(fn, config.AGE_PLOT_PATH)
        plot_region_distribution(fn, config.REGION_PLOT_PATH)
        plot_basevoice_distribution(fn, config.BASEVOICE_PLOT_PATH)
        logger.info("성별/연령/지역/기본음성 분포 그래프 저장 완료.")
    except Exception as e:
        logger.warning(f"시각화 경고: {e}")

if __name__ == "__main__":
    try:
        import MeCab  # noqa
    except Exception:
        warnings.warn("MeCab 초기화 실패: 정규식 폴백 토크나이저 사용", TokenizerInitWarning)
    main()
