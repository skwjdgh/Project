from typing import TypedDict, Optional

# class STTConfig(TypedDict):
#     api_url: str
#     language_code: str

# class TTSConfig(TypedDict):
#     language: str
#     speaker_id: int
#     sample_rate: int
#     device: str

# STT 설정 타입을 OpenAI Whisper 모델에 맞게 수정합니다.
class STTConfig(TypedDict):
    model: str
    language_code: str

# TTS 설정 타입을 OpenAI TTS 모델에 맞게 수정합니다.
class TTSConfig(TypedDict):
    model: str
    voice: str
    
class VADConfig(TypedDict):
    threshold: float
    min_silence_duration_ms: int
    hardware_rate: int
    # rate: int

class GeneralConfig(TypedDict):
    timezone: str

class AppConfig(TypedDict):
    stt: STTConfig
    tts: TTSConfig
    vad: VADConfig
    general: GeneralConfig