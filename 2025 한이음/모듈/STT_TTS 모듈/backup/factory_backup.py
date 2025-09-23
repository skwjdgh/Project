import yaml
import sys
from loguru import logger
from typing import Optional

# 각 모듈의 실제 구현 클래스를 가져옵니다.
from .imp_stt_etri import SpeechToText as EtriSTT
from .imp_tts_melotts_backup import TextToSpeech as MeloTTS
from .imp_vad_cobra import VoiceActivityDetector as CobraVAD
# 모듈들의 설계도(인터페이스)와 타입 정의를 가져옵니다.
from .def_interface import ISTT, ITTS, IVAD
from .def_types import AppConfig

# STT와 TTS 모듈은 무겁기 때문에, 한 번만 생성해서 공유하는 싱글톤(Singleton) 패턴을 사용합니다.
_stt_instance: Optional[ISTT] = None
_tts_instance: Optional[ITTS] = None

def load_config(config_path: str) -> AppConfig:
    """YAML 설정 파일을 읽어서 파이썬 딕셔너리로 변환합니다."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def create_stt(config: AppConfig) -> ISTT:
    """STT 모듈 인스턴스를 생성합니다. 이미 생성된 인스턴스가 있으면 그것을 반환합니다."""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = EtriSTT(config['stt'])
    return _stt_instance

def create_tts(config: AppConfig) -> ITTS:
    """TTS 모듈 인스턴스를 생성합니다. 이미 생성된 인스턴스가 있으면 그것을 반환합니다."""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = MeloTTS(config['tts'])
    return _tts_instance

def create_vad(config: AppConfig, device_index: Optional[int] = None) -> IVAD:
    """
    VAD 모듈 인스턴스를 생성합니다.
    VAD는 상태를 가지므로 매번 새로 생성할 수 있습니다.
    """
    return CobraVAD(config['vad'], device_index)

def setup_logging() -> None:
    """
    애플리케이션 전체에서 사용할 로거(Logger)를 설정합니다.
    Loguru 라이브러리를 사용해 시간, 레벨, 파일명 등을 예쁘게 출력합니다.
    """
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
    )