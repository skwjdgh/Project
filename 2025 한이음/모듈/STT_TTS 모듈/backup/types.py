# /Backend/Utility/STT_TTS/types.py

# #################################################
#   설정(Config) 구조 타입 정의
# #################################################

from typing import TypedDict

# 이 파일은 config.yaml 파일의 구조를 파이썬 타입으로 명시하여,
# 코드 자동 완성, 타입 체크 등 개발 편의성과 안정성을 높입니다.

# ####################################
#   STT 설정 타입
# ####################################
class STTConfig(TypedDict):
    model_name: str
    language: str
    device: str

# ####################################
#   TTS 설정 타입
# ####################################
class TTSConfig(TypedDict):
    language: str
    speaker_id: int
    sample_rate: int
    device: str

# ####################################
#   VAD 설정 타입
# ####################################
class VADConfig(TypedDict):
    aggressiveness: int
    rate: int
    frame_duration_ms: int
    timeout_seconds: int
    min_speech_frames: int
    session_timeout_seconds: int

# ####################################
#   일반 설정 타입
# ####################################
class GeneralConfig(TypedDict):
    timezone: str

# ####################################
#   전체 설정 구조 타입
# ####################################
class AppConfig(TypedDict):
    stt: STTConfig
    tts: TTSConfig
    vad: VADConfig
    general: GeneralConfig