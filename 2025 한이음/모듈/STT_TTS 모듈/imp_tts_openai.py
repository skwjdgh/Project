# Backend/Utility/STT_TTS/imp_tts_openai.py

import os
from openai import OpenAI
from loguru import logger
from typing import Dict, Any

from .def_interface import ITTS
from .def_exceptions import TTSError

class TextToSpeech(ITTS):
    """OpenAI TTS API를 사용하여 텍스트를 음성으로 변환하는 클래스."""
    def __init__(self, config: Dict[str, Any]) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("환경 변수 OPENAI_API_KEY가 설정되지 않았습니다.")
            
        self.client = OpenAI(api_key=api_key)
        self.model = config.get('model', 'tts-1')
        self.voice = config.get('voice', 'fable')
        self._is_initialized = False

    def initialize(self) -> None:
        """API 방식이므로 별도 모델 로딩 없이 초기화 상태만 설정합니다."""
        self._is_initialized = True
        logger.info("OpenAI TTS 모듈이 초기화되었습니다.")

    def is_initialized(self) -> bool:
        """초기화 여부를 반환합니다."""
        return self._is_initialized

    def synthesize(self, text: str) -> bytes:
        """
        텍스트를 MP3 형식의 음성 데이터(bytes)로 변환하여 반환합니다.
        """
        if not self.is_initialized():
            raise RuntimeError("TTS 모듈이 초기화되지 않았습니다.")
        
        logger.info(f"OpenAI TTS 변환 시작: \"{text}\"")
        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text
            )
            
            # 응답에서 오디오 데이터를 bytes로 직접 읽어옵니다.
            audio_bytes = response.read()
            logger.info(f"OpenAI TTS 변환 완료: {len(audio_bytes)} bytes 생성됨.")
            return audio_bytes

        except Exception as e:
            logger.error(f"OpenAI TTS 음성 합성 중 오류 발생: {e}")
            raise TTSError("OpenAI 음성 합성에 실패했습니다.") from e

    def close(self) -> None:
        """API 방식이므로 특별히 해제할 리소스가 없습니다."""
        pass