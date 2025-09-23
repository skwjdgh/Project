# -*- coding: utf-8 -*-

"""
실험에 필요한 모든 설정을 정의하는 모듈입니다.
이 파일의 값을 수정하여 실험 환경을 쉽게 변경할 수 있습니다.
"""

# --- 디렉토리 설정 ---
# 입력 데이터가 위치한 최상위 폴더
INPUT_DIR = "Input_data"

# INPUT_DIR 내부에 자동으로 생성할 하위 폴더 목록
# 음성 파일 및 텍스트 데이터를 구분하여 관리합니다.
SUB_DIRS = ["test", "voice", "text"]

# 실험 결과(CSV, 이미지, 로그 등)가 저장될 폴더
RESULTS_DIR = "Results"


# --- 데이터 및 로그 파일 경로 ---
# 키워드와 문장이 포함된 CSV 파일 경로 (위치 변경)
TEXT_DATA_PATH = 'Input_data/text/united.csv'

# 로그 파일 경로
LOG_FILE_PATH = f'{RESULTS_DIR}/experiment_log.txt'


# --- Whisper 모델 설정 ---
# 사용할 Whisper 모델 이름 (옵션: "tiny", "base", "small", "medium", "large")
WHISPER_MODEL = "base"

# FP16(반정밀도 부동소수점) 사용 여부 (NVIDIA GPU 환경에서 True 권장)
USE_FP16 = False


# --- 노이즈 캔슬링 설정 ---
# noisereduce 라이브러리에서 노이즈 감소 강도 (0.0 ~ 1.0)
NOISE_REDUCTION_STRENGTH = 0.8

