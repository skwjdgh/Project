import yaml
import sys
from loguru import logger
from typing import Optional

# 각 모듈의 실제 구현 클래스를 가져옵니다.
from .imp_stt_openai import SpeechToText as OpenAiSTT
# 아래 줄의 클래스 이름을 TextToSpeech로 수정했습니다.
from .imp_tts_openai import TextToSpeech as OpenAiTTS
from .imp_vad_cobra import VoiceActivityDetector as CobraVAD

from .def_interface import ISTT, ITTS, IVAD
from .def_types import AppConfig

_stt_instance: Optional[ISTT] = None
_tts_instance: Optional[ITTS] = None

def load_config(config_path: str) -> AppConfig:
    """YAML 설정 파일을 로드하고 AppConfig 타입으로 반환합니다."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def create_stt(config: AppConfig) -> ISTT:
    """STT 모듈 인스턴스를 생성합니다. (싱글턴)"""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = OpenAiSTT(config['stt'])
    return _stt_instance

def create_tts(config: AppConfig) -> ITTS:
    """TTS 모듈 인스턴스를 생성합니다. (싱글턴)"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = OpenAiTTS(config['tts'])
    return _tts_instance

def create_vad(config: AppConfig, device_index: Optional[int] = None) -> IVAD:
    """VAD 모듈 인스턴스를 생성합니다."""
    return CobraVAD(config['vad'], device_index)

def setup_logging() -> None:
    """loguru 로거를 설정합니다."""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
    )