# /Backend/Utility/STT_TTS/stt.py

# #################################################
#   음성-텍스트 변환 모듈 (Speech-to-Text Module)
# #################################################

import whisper
import numpy as np
import torch
import gc
from loguru import logger
from typing import Dict, Any

from .interface import ISTT
from .exceptions import TranscriptionError

class SpeechToText(ISTT):
    """Whisper 모델을 사용하여 음성을 텍스트로 변환하는 클래스"""

    # ####################################
    #   STT 객체 초기화
    # ####################################
    def __init__(self, config: Dict[str, Any]) -> None:
        """설정을 저장하고 모델을 나중에 로드(Lazy Loading)하도록 초기화합니다."""
        self.config = config
        self.model: whisper.Whisper = None

    # ####################################
    #   Whisper 모델 로드
    # ####################################
    def initialize(self) -> None:
        """Whisper 모델을 메모리에 명시적으로 로드합니다."""
        if self.model is None:
            device = self.config['device']
            model_name = self.config['model_name']
            logger.info(f"Whisper 모델 로딩 시작 (모델: {model_name}, 장치: {device})")
            self.model = whisper.load_model(model_name, device=device)
            logger.info("✅ Whisper 모델 로딩 완료.")

    # ####################################
    #   초기화 상태 확인
    # ####################################
    def is_initialized(self) -> bool:
        """모델 객체가 None이 아니면 초기화된 것으로 간주합니다."""
        return self.model is not None

    # ####################################
    #   음성 -> 텍스트 변환
    # ####################################
    def transcribe(self, audio_bytes: bytes) -> str:
        """오디오 바이트 스트림을 받아 텍스트로 변환합니다."""
        if not self.is_initialized():
            raise RuntimeError("STT 모델이 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        
        try:
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            logger.debug(f"STT 변환할 오디오 데이터 길이: {len(audio_np)}")
            result = self.model.transcribe(audio_np, language=self.config['language'], fp16=False)
            text = result['text']
            logger.info(f"변환 완료 -> '{text}'")
            return text
        except Exception as e:
            logger.error("STT 변환 중 예외 발생.", exc_info=True)
            raise TranscriptionError("음성 변환에 실패했습니다.") from e

    # ####################################
    #   리소스 정리
    # ####################################
    def close(self) -> None:
        """Whisper 모델을 메모리에서 명시적으로 해제하여 RAM을 확보합니다."""
        if self.model:
            logger.info("Whisper 모델을 메모리에서 해제합니다.")
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()