import asyncio
import collections
from typing import Dict, Any, Optional

import numpy as np
import sounddevice as sd
import webrtcvad
from loguru import logger

from .def_interface import IVAD
from .def_exceptions import VADStreamError

class VoiceActivityDetector(IVAD):
    def __init__(self, config: Dict[str, Any], device_index: Optional[int] = None) -> None:
        self.device_index = device_index
        # WebRTC VAD는 8000, 16000, 32000, 48000Hz만 지원합니다.
        self.HARDWARE_RATE = config.get('hardware_rate', 32000)
        # WebRTC VAD는 10, 20, 30ms 길이의 프레임만 지원합니다.
        self.frame_duration_ms = config.get('frame_duration_ms', 30)
        self.CHUNK_SAMPLES = int(self.HARDWARE_RATE * self.frame_duration_ms / 1000)
        
        # VAD 민감도 설정 (0=느슨함, 3=가장 민감함)
        aggressiveness = config.get('aggressiveness', 3)
        self.vad = webrtcvad.Vad(aggressiveness)

        # 음성 앞/뒤에 추가할 여백(padding) 설정
        self.padding_duration_ms = config.get('padding_duration_ms', 300)
        num_padding_frames = self.padding_duration_ms // self.frame_duration_ms
        
        self.min_silence_duration_ms = config.get('min_silence_duration_ms', 1000)
        
        # 패딩을 위한 링 버퍼(ring buffer)
        self.ring_buffer = collections.deque(maxlen=num_padding_frames)
        self.is_listening = False

    async def listen(self) -> Optional[bytes]:
        if self.is_listening:
            return None
        self.is_listening = True
        
        loop = asyncio.get_running_loop()
        audio_queue = asyncio.Queue()
        
        def audio_callback(indata, frames, time, status):
            if status: logger.warning(status)
            loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

        triggered = False
        speech_buffer = []
        
        num_silence_frames = 0
        min_silence_frames = self.min_silence_duration_ms // self.frame_duration_ms

        logger.info("🎤 음성 입력을 기다립니다...")
        stream = sd.InputStream(
            samplerate=self.HARDWARE_RATE, channels=1, dtype='int16', 
            blocksize=self.CHUNK_SAMPLES, device=self.device_index, 
            callback=audio_callback
        )
        with stream:
            try:
                while True:
                    frame = await audio_queue.get()
                    if len(frame) < (2 * self.CHUNK_SAMPLES):
                        continue

                    is_speech = self.vad.is_speech(frame, self.HARDWARE_RATE)
                    
                    if not triggered:
                        self.ring_buffer.append(frame)
                        if is_speech:
                            triggered = True
                            # 버퍼에 있던 패딩용 오디오를 실제 음성 버퍼에 추가
                            speech_buffer.extend(list(self.ring_buffer))
                            self.ring_buffer.clear()
                            num_silence_frames = 0
                    else:
                        speech_buffer.append(frame)
                        if not is_speech:
                            num_silence_frames += 1
                            if num_silence_frames > min_silence_frames:
                                return b''.join(speech_buffer)
                        else:
                            num_silence_frames = 0
            
            except asyncio.CancelledError:
                 logger.info("리스닝 작업이 취소되었습니다.")
            except Exception as e:
                logger.error(f"오디오 스트림 내부에서 실제 오류 발생: {e}", exc_info=True)
                raise VADStreamError("마이크 입력 처리 중 문제가 발생했습니다.") from e
            finally:
                self.is_listening = False
        return None

    def initialize(self) -> None: pass
    def is_initialized(self) -> bool: return True
    def close(self) -> None: logger.info("VAD 모듈이 정리되었습니다.")