# /Backend/Utility/STT_TTS/tts.py

# #################################################
#   텍스트-음성 변환 모듈 (MeloTTS - 최종 수정판)
# #################################################

import sounddevice as sd
from loguru import logger
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any
import tempfile
import soundfile as sf

from .interface import ITTS
from .exceptions import TTSError
from melo.api import TTS

class TextToSpeech(ITTS):
    """MeloTTS를 사용하여 텍스트를 음성으로 변환하는 클래스 (임시 파일 방식)"""

    # ####################################
    #   TTS 객체 초기화
    # ####################################
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.model: TTS = None
        self.sample_rate = config['sample_rate']
        self.executor = ThreadPoolExecutor(max_workers=1)

    # ####################################
    #   MeloTTS 모델 로드
    # ####################################
    def initialize(self) -> None:
        if self.model is None:
            device = self.config['device']
            logger.info(f"MeloTTS 모델 로딩 시작 (장치: {device})")
            self.model = TTS(language=self.config['language'], device=device)
            logger.info("✅ MeloTTS 모델 로딩 완료.")

    # ####################################
    #   초기화 상태 확인
    # ####################################
    def is_initialized(self) -> bool:
        return self.model is not None

    # ####################################
    #   텍스트 -> 음성 변환 및 재생
    # ####################################
    def speak(self, text: str) -> None:
        if not self.is_initialized():
            raise RuntimeError("TTS 모델이 초기화되지 않았습니다.")

        def play_audio(wav_data: np.ndarray, samplerate: int) -> None:
            """스레드에서 오디오를 재생하는 내부 함수"""
            try:
                sd.play(wav_data, samplerate)
                sd.wait()
                logger.debug("오디오 재생 완료.")
            except Exception as e:
                logger.error(f"오디오 재생 중 예외 발생: {e}", exc_info=True)

        try:
            logger.info(f"TTS 변환 시작: \"{text}\"")

            # 1. 임시 WAV 파일 생성 (with 블록 종료 시 자동 삭제)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmpfile:
                tmp_filename = tmpfile.name
                
                # 2. tts_to_file 메서드를 사용하여 임시 파일에 음성 저장
                self.model.tts_to_file(
                    text,
                    speaker_id=0,
                    output_path=tmp_filename,
                    speed=1.0
                )
                
                # 3. 저장된 임시 파일을 다시 읽어 메모리로 로드
                wav_data, samplerate = sf.read(tmp_filename)

            # 4. 스레드 풀에 오디오 재생 작업을 제출
            self.executor.submit(play_audio, wav_data, samplerate)

        except Exception as e:
            logger.error(f"MeloTTS 변환/재생 중 예외 발생: {e}", exc_info=True)
            raise TTSError("음성 합성에 실패했습니다.") from e

    # ####################################
    #   리소스 정리
    # ####################################
    def close(self) -> None:
        """오디오 재생에 사용된 스레드 풀을 안전하게 종료합니다."""
        logger.info("TTS 스레드 풀을 종료합니다.")
        self.executor.shutdown(wait=True)