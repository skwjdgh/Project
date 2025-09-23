# -*- coding: utf-8 -*-
import os

# ===== Whisper / STT =====
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
USE_FP16 = False  # GPU + small 이상이면 True 고려

# ===== 경로 =====
# 오디오 폴더
DATA_DIR = os.path.join("input_data", "voice")
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}

# 정답 CSV
GROUND_TRUTH_CSV = os.path.join("input_data", "text", "united.csv")

# 결과물
RESULTS_DIR = os.path.join("Results")
DETAIL_CSV_PATH = os.path.join(RESULTS_DIR, "detailed_results.csv")
PLOT_PATH = os.path.join(RESULTS_DIR, "accuracy_compare.png")
GENDER_PLOT_PATH = os.path.join(RESULTS_DIR, "gender_ratio.png")
AGE_PLOT_PATH = os.path.join(RESULTS_DIR, "age_distribution.png")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ===== 노이즈 제거 파라미터 =====
NOISE_REDUCE_STRENGTH = 0.5
TARGET_SR = 16000
TARGET_CHANNELS = 1

# ===== CSV 컬럼 지정 =====
# CSV 헤더가 ['지역','종류','내용']일 때, 정답으로 '종류' 사용
GT_KEYWORD_COL = "종류"
GT_FILE_COL = ""

# ===== 토큰 매칭/고도화 파라미터 (B/D만 영향) =====
# B/D 정확도 상향을 위해 기본 임계 완화 + 퍼지 허용 확대
TOKEN_RECALL_MIN = 0.50
FUZZY_RATIO_MIN = 0.84

# 앵커 토큰(가장 긴 상위 k개)에 가중치
ANCHOR_TOPK = 3
ANCHOR_WEIGHT = 2.5

# 문자 n-그램 백스톱(토큰화 실패 대비)
USE_CHARGRAM_BACKSTOP = True
CHARGRAM_N = 3
CHARGRAM_MIN = 0.16

# D가 항상 B 이상 되도록 B/C 토큰 유니온 사용
USE_D_UNION_TOKENS = True

# ===== 도메인 동의어/변형어 (첨부 united.csv 기반, 8개 카테고리) =====
# - 스페이싱/약칭/일반 구어체 포함
KEYWORD_ALIASES = {
    # 가족관계증명서 계열
    "가족관계증명서": [
        "가족관계 증명서", "가족 관계 증명서",
        "가족관계", "가족 관계", "가족관계 증명"
    ],
    # 건강보험자격득실확인서 계열
    "건강보험자격득실확인서": [
        "건강보험 자격득실 확인서", "건강 보험 자격 득실 확인서",
        "자격득실 확인서", "자격 득실 확인서",
        "건보 자격득실", "건강보험 자격득실", "자격득실"
    ],
    # 등본/초본은 주민등록 접두 변형이 빈번
    "등본": [
        "주민등록등본", "주민 등록 등본", "주민등록 등본",
        "주민등본", "등본 발급"
    ],
    "초본": [
        "주민등록초본", "주민 등록 초본", "주민등록 초본",
        "주민초본", "초본 발급"
    ],
    # 이벤트/공연/축제/행사/날씨/카테고리 일반 변형
    "축제": [
        "페스티벌", "축제 정보", "지역축제", "페스티벌 정보"
    ],
    "행사": [
        "이벤트", "공연", "행사 정보", "행사 일정"
    ],
    "날씨": [
        "일기예보", "날씨 예보", "기상", "날씨 정보"
    ],
    "카테고리": [
        "분류", "카테고리 설정", "카테고리 선택"
    ],
}

# ===== 로깅 =====
LOG_LEVEL = "INFO"


# 전처리 필터
HPF_CUTOFF_HZ = 80      # 100→80 (저역 훨씬 제거)
LPF_CUTOFF_HZ = 6500    # 7000→6500 (초고역 잡음 컷)
PREEMPHASIS   = 0.97    # s[n] - 0.97*s[n-1]

# VAD 기반 노이즈 프로파일 추정
USE_WEBRTCVAD = True    # webrtcvad 사용(미설치면 자동 폴백)
VAD_AGGR      = 1       # 0~3 (클수록 공격적)
MIN_NOISE_SEC = 0.5     # 최소 노이즈 구간 합계(부족하면 저에너지 프레임 보충)

# noisereduce 세부
NR_PROP_DECREASE         = 0.6   # 감쇠 비율(0.4→0.6)
NR_STATIONARY            = False # 비정상 잡음 가정
NR_WIN_SIZE              = 1024
NR_HOP_LENGTH            = 512
NR_FREQ_MASK_SMOOTH_HZ   = 600   # 주파수 마스크 스무딩
NR_TIME_MASK_SMOOTH_MS   = 64    # 시간 마스크 스무딩
NR_N_FFT = 2048        # noisereduce 신형 파라미터명
SNR_BYPASS_DB = 12.0    # 이 이상이면 NR 생략(= A와 유사 품질 보장)


# 노이즈 캔슬링 미세조정(선택)
NR_PROP_SOFT = 0.55
NR_PROP_HARD = 0.80
GATE_ATTN_SOFT = 0.45
GATE_ATTN_HARD = 0.35
SPEECH_BLEND = 0.70
SPEECH_GAIN  = 1.03

