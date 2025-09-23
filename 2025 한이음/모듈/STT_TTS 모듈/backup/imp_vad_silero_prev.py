import torch
import sounddevice as sd
import numpy as np
from loguru import logger
from typing import Dict, Any, Optional
import asyncio

from ..def_interface import IVAD
from ..def_exceptions import VADStreamError

class VoiceActivityDetector(IVAD):
    def __init__(self, config: Dict[str, Any], device_index: Optional[int] = None) -> None:
        self.model, _ = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False)
        self.model.eval()
        # config 딕셔너리에서 'rate' 값을 가져오고, 없으면 16000을 기본값으로 사용
        self.VAD_RATE = config.get('rate', 16000) 
        self.HARDWARE_RATE = config.get('hardware_rate', 44100)
        self.threshold = config['threshold']
        self.min_silence_duration_ms = config['min_silence_duration_ms']
        self.device_index = device_index
        self.CHUNK_SAMPLES = 512
        self.block_size = int(self.CHUNK_SAMPLES * self.HARDWARE_RATE / self.VAD_RATE)
        self.is_listening = False

    def _resample(self, audio_data: np.ndarray) -> np.ndarray:
        if self.HARDWARE_RATE == self.VAD_RATE:
            return audio_data
        try:
            from scipy.signal import resample
            num_samples = round(len(audio_data) * float(self.VAD_RATE) / self.HARDWARE_RATE)
            return resample(audio_data, num_samples)
        except ImportError:
            raise ImportError("'scipy'가 필요합니다.")

    async def listen(self) -> Optional[bytes]:
        if self.is_listening:
            return None
        self.is_listening = True
        loop = asyncio.get_running_loop()
        audio_queue = asyncio.Queue()
        
        def audio_callback(indata, frames, time, status):
            if status: logger.warning(status)
            loop.call_soon_threadsafe(audio_queue.put_nowait, indata.copy())

        speech_buffer = []
        is_speaking = False
        silence_chunks = 0
        min_silence_chunks = self.min_silence_duration_ms / (1000 * self.CHUNK_SAMPLES / self.VAD_RATE)

        logger.info("🎤 음성 입력을 기다립니다...")
        stream = sd.InputStream(
            samplerate=self.HARDWARE_RATE, channels=1, dtype='int16', 
            blocksize=self.block_size, device=self.device_index, 
            callback=audio_callback
        )
        with stream:
            try:
                while True:
                    audio_chunk = await audio_queue.get()
                    audio_float32 = audio_chunk.flatten().astype(np.float32) / 32768.0
                    audio_resampled = self._resample(audio_float32)
                    audio_tensor = torch.from_numpy(audio_resampled)
                    speech_prob = self.model(audio_tensor, self.VAD_RATE).item()

                    if speech_prob > self.threshold:
                        if not is_speaking:
                            is_speaking = True
                        speech_buffer.append(audio_chunk.tobytes())
                        silence_chunks = 0
                    else:
                        if is_speaking:
                            silence_chunks += 1
                            if silence_chunks > min_silence_chunks:
                                return b''.join(speech_buffer)
            except asyncio.CancelledError:
                 logger.info("리스닝 작업이 취소되었습니다.")
            except Exception as e:
                # ❗❗ 이 줄을 반드시 추가해야 합니다 ❗❗
                logger.error(f"오디오 스트림 내부에서 실제 오류 발생: {e}", exc_info=True)
                raise VADStreamError("마이크 입력 처리 중 문제가 발생했습니다.") from e
            finally:
                self.is_listening = False
        return None
            
    def close(self) -> None:
        logger.info("VAD 모듈이 정리되었습니다.")
    
    def initialize(self) -> None: pass
    def is_initialized(self) -> bool: return True