# #################################################
#   객체 생성 및 설정 팩토리 (Object Creation & Setup Factory)
# #################################################

import yaml
import sys
import os
from loguru import logger
from typing import Optional, Dict, Any

# 각 모듈의 클래스를 임포트
from .stt import SpeechToText
from .tts import TextToSpeech
from .vad import VoiceActivityDetector
from .interface import ISTT, ITTS, IVAD

# ################################
#   싱글턴 인스턴스 캐시
# ################################
# STT와 TTS 모델은 메모리를 많이 차지하므로, 프로그램 전체에서 단 하나만 생성하여 공유 (싱글턴 패턴)
_stt_instance: Optional[ISTT] = None
_tts_instance: Optional[ITTS] = None


# ####################################
#   설정 파일 로드
# ####################################
def load_config(config_path: str = 'config.yaml') -> Dict[str, Any]:
    """
    config.yaml 설정 파일을 읽어 딕셔너리 형태로 반환합니다.
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


# ####################################
#   STT 인스턴스 생성/반환
# ####################################
def create_stt(config: Dict[str, Any]) -> ISTT:
    """
    STT 인스턴스를 생성하거나, 이미 존재하면 캐시된 인스턴스를 반환합니다.
    """
    global _stt_instance
    # 캐시된 인스턴스가 없으면 새로 생성
    if _stt_instance is None:
        logger.info("STT 인스턴스를 새로 생성합니다.")
        _stt_instance = SpeechToText(config['stt'])
    # 캐시된 인스턴스 반환
    return _stt_instance


# ####################################
#   TTS 인스턴스 생성/반환
# ####################################
def create_tts(config: Dict[str, Any]) -> ITTS:
    """
    TTS 인스턴스를 생성하거나, 이미 존재하면 캐시된 인스턴스를 반환합니다.
    """
    global _tts_instance
    # 캐시된 인스턴스가 없으면 새로 생성
    if _tts_instance is None:
        logger.info("TTS 인스턴스를 새로 생성합니다.")
        _tts_instance = TextToSpeech(config['tts'])
    # 캐시된 인스턴스 반환
    return _tts_instance


# ####################################
#   VAD 인스턴스 생성
# ####################################
def create_vad(config: Dict[str, Any], device_index: Optional[int] = None) -> IVAD:
    """
    VAD 인스턴스를 생성합니다. VAD는 상태를 가지지 않으므로 매번 새로 생성해도 무방합니다.
    """
    return VoiceActivityDetector(config['vad'], device_index)


# ####################################
#   로깅 시스템 설정
# ####################################
def setup_logging() -> None:
    """
    Loguru를 사용해 애플리케이션 전체의 로깅 시스템을 설정합니다.
    """
    # 기본 핸들러를 제거하여 중복 로깅 방지
    logger.remove()
    # 새로운 핸들러 추가 (표준 에러 출력)
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
    )


# ####################################
#   타임존 설정
# ####################################
def setup_timezone(config: Dict[str, Any]) -> None:
    """
    설정 파일에 명시된 타임존으로 시스템 타임존을 설정합니다.
    """
    try:
        # 설정 파일에서 타임존 정보 가져오기
        tz = config['general']['timezone']
        # 환경 변수 설정
        os.environ['TZ'] = tz
        # Unix-like 시스템에서 타임존 변경 적용
        if hasattr(os, 'tzset'):
            os.tzset()
        logger.info(f"타임존이 '{tz}'(으)로 설정되었습니다.")
    except Exception as e:
        logger.warning(f"타임존 설정에 실패했습니다: {e}")