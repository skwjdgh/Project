import sounddevice as sd
from loguru import logger
import numpy as np
from typing import Dict, Any
import tempfile
import soundfile as sf
import torch
import asyncio
import subprocess

from .def_interface import ITTS
from .def_exceptions import TTSError
from melo.api import TTS

class TextToSpeech(ITTS):
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.model: TTS = None

    def initialize(self) -> None:
        if self.model is None:
            self.model = TTS(language=self.config['language'], device=self.config['device'])

    def is_initialized(self) -> bool:
        return self.model is not None

    def _blocking_speak(self, text: str):
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmpfile:
                # 음성 파일을 생성하는 부분은 기존과 동일
                self.model.tts_to_file(text, speaker_id=0, output_path=tmpfile.name, speed=1.0)
                
                # aplay -q 옵션은 재생 시작/종료 메시지를 숨겨줍니다.
                subprocess.run(["aplay", "-q", tmpfile.name], check=True)

        except FileNotFoundError:
            # aplay가 설치되지 않았을 경우를 대비한 예외 처리
            logger.error("aplay 명령을 찾을 수 없습니다. 'sudo apt-get install alsa-utils'로 설치해주세요.")
            raise TTSError("음성 재생에 필요한 aplay가 설치되지 않았습니다.")
        except subprocess.CalledProcessError as e:
            logger.error(f"aplay로 음성 재생 중 오류 발생: {e}")
            raise TTSError("aplay로 음성을 재생하는 데 실패했습니다.")
        except Exception as e:
            raise TTSError("음성 합성에 실패했습니다.") from e

    async def speak(self, text: str) -> None:
        if not self.is_initialized():
            raise RuntimeError("TTS 모델이 초기화되지 않았습니다.")
        logger.info(f"TTS 변환 시작: \"{text}\"")
        try:
            await asyncio.to_thread(self._blocking_speak, text)
        except Exception as e:
            if not isinstance(e, TTSError):
                raise TTSError("알 수 없는 TTS 오류") from e
            raise e

    def close(self) -> None:
        logger.info("MeloTTS 리소스가 정리되었습니다.")