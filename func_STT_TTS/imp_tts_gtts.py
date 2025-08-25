from loguru import logger
from typing import Dict, Any
import io

# gTTS 라이브러리 import
from gtts import gTTS

# --- STT/TTS 통합: 인터페이스 및 예외 클래스 import ---
from .def_interface import ITTS
from .def_exceptions import TTSError
# ----------------------------------------------------

class TextToSpeech(ITTS):
    """
    gTTS(Google Text-to-Speech) 라이브러리를 사용하여 텍스트를 음성으로 변환하는 클래스.
    웹 서버 환경에 맞게, 음성을 직접 재생하는 대신 MP3 데이터 바이트를 생성하여 반환합니다.
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        # config.yaml에서 언어 설정 등을 가져옵니다.
        self.config = config
        self._is_initialized = False

    def initialize(self) -> None:
        """gTTS는 별도의 모델 로딩이 필요 없으므로, 초기화 상태 플래그만 설정합니다."""
        self._is_initialized = True
        logger.info("gTTS 모듈이 초기화되었습니다.")

    def is_initialized(self) -> bool:
        """초기화 여부를 반환합니다."""
        return self._is_initialized

    # --- STT/TTS 통합: synthesize 메서드 구현 ---
    def synthesize(self, text: str) -> bytes:
        """
        텍스트를 MP3 형식의 음성 데이터(bytes)로 변환하여 반환합니다.
        gTTS를 사용하여 메모리 내에서 직접 오디오 데이터를 생성합니다.
        """
        if not self.is_initialized():
            raise RuntimeError("TTS 모듈이 초기화되지 않았습니다.")
        
        logger.info(f"gTTS 변환 시작: \"{text}\"")
        try:
            # BytesIO를 사용하여 파일 시스템을 거치지 않고 메모리에서 바로 작업합니다.
            mp3_fp = io.BytesIO()
            
            # gTTS 객체 생성 및 음성 데이터 쓰기
            tts = gTTS(text=text, lang=self.config.get('language', 'ko'), slow=False)
            tts.write_to_fp(mp3_fp)
            
            # 스트림의 시작으로 포인터를 이동시켜 전체 데이터를 읽을 준비를 합니다.
            mp3_fp.seek(0)
            
            # 바이트 데이터를 읽어서 반환합니다.
            audio_bytes = mp3_fp.read()
            logger.info(f"gTTS 변환 완료: {len(audio_bytes)} bytes 생성됨.")
            return audio_bytes

        except Exception as e:
            logger.error(f"gTTS 음성 합성 중 오류 발생: {e}")
            # TTSError 예외를 발생시켜 API 엔드포인트에서 일관되게 처리하도록 합니다.
            raise TTSError("gTTS 음성 합성에 실패했습니다.") from e
    # -------------------------------------------

    def close(self) -> None:
        """gTTS는 별도로 해제할 리소스가 없으므로 pass 처리합니다."""
        logger.info("gTTS 리소스가 정리되었습니다.")
        pass