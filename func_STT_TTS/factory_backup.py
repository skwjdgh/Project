import yaml
import sys
from loguru import logger
from typing import Optional

# 각 모듈의 실제 구현 클래스를 가져옵니다.
from .imp_stt_etri import SpeechToText as EtriSTT
# from .imp_tts_melotts import TextToSpeech as MeloTTS # ✅ 이 부분을 주석 처리
from .imp_tts_gtts import TextToSpeech as GttsTTS # ✅ gTTS 구현을 import 합니다.
from .imp_vad_cobra import VoiceActivityDetector as CobraVAD
from .def_interface import ISTT, ITTS, IVAD
from .def_types import AppConfig

_stt_instance: Optional[ISTT] = None
_tts_instance: Optional[ITTS] = None

def load_config(config_path: str) -> AppConfig:
    # ... (기존 코드 유지)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def create_stt(config: AppConfig) -> ISTT:
    # ... (기존 코드 유지)
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = EtriSTT(config['stt'])
    return _stt_instance

def create_tts(config: AppConfig) -> ITTS:
    """TTS 모듈 인스턴스를 생성합니다. 이미 생성된 인스턴스가 있으면 그것을 반환합니다."""
    global _tts_instance
    if _tts_instance is None:
        # ✅ MeloTTS 대신 GttsTTS를 사용하도록 변경
        _tts_instance = GttsTTS(config['tts'])
    return _tts_instance

def create_vad(config: AppConfig, device_index: Optional[int] = None) -> IVAD:
    # ... (기존 코드 유지)
    return CobraVAD(config['vad'], device_index)

def setup_logging() -> None:
    # ... (기존 코드 유지)
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
    )