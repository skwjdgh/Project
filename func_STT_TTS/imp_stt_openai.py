# Backend/Utility/STT_TTS/imp_stt_openai.py

import os
from openai import OpenAI
from loguru import logger
from typing import Dict, Any
import io

from .def_interface import ISTT
from .def_exceptions import TranscriptionError

class SpeechToText(ISTT):
    """OpenAI Whisper API를 사용하여 오디오를 텍스트로 변환하는 클래스."""
    def __init__(self, config: Dict[str, Any]) -> None:
        # .env 파일에서 OPENAI_API_KEY를 불러옵니다.
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("환경 변수 OPENAI_API_KEY가 설정되지 않았습니다.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = config.get('model', 'whisper-1')
        self.language = config.get('language_code', 'ko')
        self._is_initialized = False

    def initialize(self) -> None:
        """API 방식이므로 별도 모델 로딩 없이 초기화 상태만 설정합니다."""
        self._is_initialized = True
        logger.info("OpenAI STT (Whisper) 모듈이 초기화되었습니다.")

    def is_initialized(self) -> bool:
        """초기화 여부를 반환합니다."""
        return self._is_initialized

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        오디오 데이터를 OpenAI Whisper API로 전송하고, 인식된 텍스트를 받아옵니다.
        """
        if not self.is_initialized():
            raise RuntimeError("STT 모듈이 초기화되지 않았습니다.")
        
        try:
            # OpenAI 라이브러리는 파일 객체를 요구하므로, bytes를 메모리 내 파일처럼 만듭니다.
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav" # Whisper가 파일 형식을 식별할 수 있도록 이름 부여

            logger.info(f"OpenAI Whisper API({self.model})로 음성 인식 시작...")
            
            transcript = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=self.language
            )
            
            recognized_text = transcript.text
            
            if not recognized_text:
                logger.warning("API가 음성을 인식하지 못했습니다.")
                return ""
            
            logger.info(f"OpenAI API 변환 완료 -> '{recognized_text}'")
            return recognized_text

        except Exception as e:
            logger.error(f"OpenAI STT API 처리 중 오류 발생: {e}")
            raise TranscriptionError("OpenAI 음성 변환에 실패했습니다.") from e

    def close(self) -> None:
        """API 방식이므로 특별히 해제할 리소스가 없습니다."""
        pass