import os
import logging

# --- 경로 설정 ---
DATA_DIR = "text_data"
OUTPUT_DIR = "voice"

# --- 음성 생성 옵션 ---
AGES = ["child", "young_adult", "middle_aged", "senior"]
GENDERS = ["male", "female"]
TONES = ["neutral", "happy", "sad", "angry"]
EMOTIONS = ["calm", "energetic", "thoughtful", "excited"]

# --- OpenAI API 설정 (TTS 전용 모델/음성 리스트) ---
OPENAI_MODEL = "gpt-4o-mini-tts"
# 실제 지원 음성 이름들로 갱신해 사용 (예시는 자리표시자)
OPENAI_VOICES = ["alloy", "echo", "onyx", "nova", "shimmer"]

# --- 샘플링 및 형식 설정 ---
TOTAL_SAMPLES = 800
AUDIO_FORMAT = "mp3"
RANDOM_SEED = 0

# --- CSV 컬럼 이름 (사용자 CSV 형식 반영) ---
CSV_REGION_COL = "지역"
CSV_TYPE_COL = "종류"
CSV_SENTENCE_COL = "내용"

# --- 노이즈 추가 설정 ---
# 0에서 100 사이의 값. 5로 설정 시, 전체 샘플의 약 5%에 메타데이터 노이즈가 추가됩니다.
NOISE_PERCENTAGE = 20

# --- 실행 및 로깅 설정 ---
LOG_FILE = "voice_generation.log"
VERBOSE = True           # 콘솔 출력 여부
CLEAN_FILENAME = True    # 파일명 특수문자 정리 여부

# --- 성능 및 안정성 설정 ---
RETRY_COUNT = 3
RETRY_DELAY = 2  # 초
MAX_WORKERS = 4  # 동시 작업 수

# --- 함수 ---
def calc_samples_per_keyword(num_keywords: int) -> int:
    """키워드 개수에 따라 키워드당 샘플 수를 계산합니다."""
    if num_keywords <= 0:
        return 0
    return TOTAL_SAMPLES // num_keywords

# --- 초기 설정 ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

handlers = [logging.FileHandler(LOG_FILE, encoding="utf-8")]
if VERBOSE:
    handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=handlers,
)