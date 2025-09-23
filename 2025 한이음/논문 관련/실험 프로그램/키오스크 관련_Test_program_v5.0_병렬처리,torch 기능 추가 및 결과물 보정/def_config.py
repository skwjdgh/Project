# -*- coding: utf-8 -*-
import os

# ===== Whisper / STT =====
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
USE_FP16 = True

# ===== 경로 =====
DATA_DIR = os.path.join("input_data", "voice")        # Windows는 대소문자 무시
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
GROUND_TRUTH_CSV = os.path.join("input_data", "text", "united.csv")

# ===== 결과물 경로 =====
RESULTS_DIR = os.path.join("Results")
DETAIL_CSV_PATH = os.path.join(RESULTS_DIR, "detailed_results.csv")
PLOT_PATH = os.path.join(RESULTS_DIR, "accuracy_compare.png")
GENDER_PLOT_PATH = os.path.join(RESULTS_DIR, "gender_ratio.png")
AGE_PLOT_PATH = os.path.join(RESULTS_DIR, "age_distribution.png")
REGION_PLOT_PATH = os.path.join(RESULTS_DIR, "region_distribution.png")
BASEVOICE_PLOT_PATH = os.path.join(RESULTS_DIR, "basevoice_distribution.png")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ===== CSV 컬럼 =====
GT_KEYWORD_COL = "종류"
GT_FILE_COL = ""

# ===== B/D 토큰 매칭 파라미터 =====
TOKEN_RECALL_MIN = 0.50
FUZZY_RATIO_MIN = 0.84
ANCHOR_TOPK = 3
ANCHOR_WEIGHT = 2.5
USE_CHARGRAM_BACKSTOP = True
CHARGRAM_N = 3
CHARGRAM_MIN = 0.16
USE_D_UNION_TOKENS = True   # D에서 A·C 토큰 유니온

# ===== 도메인 동의어 (8개 카테고리) =====
KEYWORD_ALIASES = {
    "가족관계증명서": ["가족관계 증명서","가족 관계 증명서","가족관계","가족 관계","가족관계 증명"],
    "건강보험자격득실확인서": ["건강보험 자격득실 확인서","건강 보험 자격 득실 확인서","자격득실 확인서","자격 득실 확인서","건보 자격득실","건강보험 자격득실","자격득실"],
    "등본": ["주민등록등본","주민 등록 등본","주민등록 등본","주민등본","등본 발급"],
    "초본": ["주민등록초본","주민 등록 초본","주민등록 초본","주민초본","초본 발급"],
    "축제": ["페스티벌","축제 정보","지역축제","페스티벌 정보"],
    "행사": ["이벤트","공연","행사 정보","행사 일정"],
    "날씨": ["일기예보","날씨 예보","기상","날씨 정보"],
    "카테고리": ["분류","카테고리 설정","카테고리 선택"],
}

# ===== 노이즈 캔슬링 파라미터 =====
HPF_CUTOFF_HZ = 80
LPF_CUTOFF_HZ = 6500
PREEMPHASIS = 0.97
TARGET_SR = 16000
TARGET_CHANNELS = 1

USE_WEBRTCVAD = True
VAD_AGGR = 1
MIN_NOISE_SEC = 0.5
SNR_BYPASS_DB = 12.0

NR_PROP_DECREASE = 0.6
NR_STATIONARY = False
NR_WIN_SIZE = 1024
NR_HOP_LENGTH = 512
NR_FREQ_MASK_SMOOTH_HZ = 600
NR_TIME_MASK_SMOOTH_MS = 64
NR_N_FFT = 2048

# 튜닝(선택)
NR_PROP_SOFT = 0.55
NR_PROP_HARD = 0.80
GATE_ATTN_SOFT = 0.45
GATE_ATTN_HARD = 0.35
SPEECH_BLEND = 0.70
SPEECH_GAIN  = 1.03

# ===== 로깅 =====
LOG_LEVEL = "INFO"


EXECUTOR_KIND = "thread"   # "process" | "thread" | "serial"
NUM_WORKERS   =  4 # max(1, os.cpu_count() // 2)  # 코어 절반 정도 권장
