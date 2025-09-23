import asyncio
import os
import queue
import threading
from typing import Dict, Any, Optional

import numpy as np
import pvcobra
import resampy
import sounddevice as sd
from loguru import logger

from .def_interface import IVAD
from .def_exceptions import VADStreamError

class VoiceActivityDetector(IVAD):
    """
    Picovoice Cobra VAD를 사용하여 음성 활동을 감지하는 클래스.
    라즈베리파이 같은 저전력 장치에서의 성능 문제를 해결하기 위해,
    오디오 입력과 VAD 처리를 별도의 스레드로 분리한 구조를 가집니다.
    """
    def __init__(self, config: Dict[str, Any], device_index: Optional[int] = None) -> None:
        try:
            # 환경변수에서 Picovoice AccessKey를 가져옵니다.
            access_key = os.environ["PICOVOICE_ACCESS_KEY"]
            # AccessKey로 Cobra VAD 인스턴스를 생성합니다.
            self.cobra = pvcobra.create(access_key=access_key)
        except (KeyError, pvcobra.PvError) as e:
            raise VADStreamError(f"Cobra VAD 초기화 실패: {e}")

        # 하드웨어 및 VAD 설정 초기화
        self.device_index = device_index
        self.HARDWARE_RATE = config.get('hardware_rate', 48000)
        self.VAD_RATE = self.cobra.sample_rate  # Cobra는 16000Hz를 사용
        self.CHUNK_SAMPLES = self.cobra.frame_length  # Cobra는 512 샘플 단위를 사용

        # 실제 마이크에서 읽어올 블록 크기를 리샘플링 비율에 맞춰 계산합니다.
        self.block_size = int(self.CHUNK_SAMPLES * self.HARDWARE_RATE / self.VAD_RATE)

        self.threshold = config.get('threshold', 0.6)
        self.min_silence_duration_ms = config.get('min_silence_duration_ms', 1000)

        # 스레드 간 데이터 통신을 위한 큐(Queue)
        self.input_queue = queue.Queue()  # 오디오 입력 스레드 -> 처리 스레드
        self.output_queue = queue.Queue() # 처리 스레드 -> 메인 스레드

        # 처리 스레드를 제어하기 위한 이벤트 객체와 스레드 객체
        self.stop_event = threading.Event()
        self.processing_thread = threading.Thread(target=self._processing_loop)

    def _resample(self, audio_data: np.ndarray) -> np.ndarray:
        """오디오 샘플링 레이트를 변환합니다. (예: 48000Hz -> 16000Hz)"""
        return resampy.resample(audio_data, self.HARDWARE_RATE, self.VAD_RATE)

    def _processing_loop(self):
        """
        별도의 스레드에서 실행되는 VAD 처리 루프.
        메인 스레드의 부담을 줄여 'input overflow'를 방지합니다.
        """
        is_speaking = False
        speech_buffer = []
        silence_frames = 0
        min_silence_frames = self.min_silence_duration_ms // (1000 * self.CHUNK_SAMPLES / self.VAD_RATE)

        while not self.stop_event.is_set():
            try:
                # 입력 큐에서 오디오 데이터를 가져옵니다. 데이터가 없으면 잠시 대기.
                indata = self.input_queue.get(timeout=0.1)

                # VAD 처리를 위한 데이터 형식 변환
                audio_float32 = indata.flatten().astype(np.float32) / 32768.0
                audio_resampled = self._resample(audio_float32)
                audio_int16 = (audio_resampled * 32767).astype(np.int16)

                # Cobra는 512 샘플 단위로만 처리 가능하므로, 받은 데이터를 잘라서 처리합니다.
                num_frames = len(audio_int16) // self.CHUNK_SAMPLES
                for i in range(num_frames):
                    frame = audio_int16[i * self.CHUNK_SAMPLES : (i + 1) * self.CHUNK_SAMPLES]
                    voice_probability = self.cobra.process(frame)

                    # 음성 감지 로직
                    if voice_probability > self.threshold:
                        if not is_speaking: is_speaking = True
                        speech_buffer.append(frame.tobytes())
                        silence_frames = 0
                    elif is_speaking:
                        silence_frames += 1
                        if silence_frames > min_silence_frames:
                            # 음성 구간이 끝나면, 감지된 전체 음성 데이터를 출력 큐에 넣습니다.
                            utterance = b''.join(speech_buffer)
                            self.output_queue.put(utterance)
                            is_speaking = False
                            speech_buffer = []
                            silence_frames = 0
            except queue.Empty:
                # 큐가 비어있으면 루프를 계속 진행합니다.
                continue

    async def listen(self) -> Optional[bytes]:
        """
        메인 스레드에서 호출하는 비동기 메서드.
        오디오 스트림을 시작하고, 처리 스레드가 결과를 내놓을 때까지 기다립니다.
        """
        logger.info("🎤 음성 입력을 기다립니다 (Cobra VAD - Threaded)...")

        # 이전 작업의 스레드가 살아있으면 안전하게 종료시킵니다.
        if self.processing_thread.is_alive():
            self.stop_event.set()
            self.processing_thread.join()

        # 새 리스닝을 위해 큐와 이벤트를 초기화하고 처리 스레드를 시작합니다.
        self._clear_queues()
        self.stop_event.clear()
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.start()

        def audio_callback(indata, frames, time, status):
            """마이크에서 오디오 데이터가 들어올 때마다 호출되는 함수."""
            if status: logger.warning(status)
            self.input_queue.put(indata.copy())

        # 마이크 입력 스트림 시작
        stream = sd.InputStream(
            samplerate=self.HARDWARE_RATE, channels=1, dtype='int16',
            blocksize=self.block_size, device=self.device_index,
            callback=audio_callback
        )
        with stream:
            try:
                loop = asyncio.get_running_loop()
                # 처리 스레드가 결과를 output_queue에 넣을 때까지 비동기적으로 대기합니다.
                # 'run_in_executor'는 동기 함수(output_queue.get)를 비동기 루프에서 안전하게 실행시켜줍니다.
                detected_audio = await loop.run_in_executor(None, self.output_queue.get)
                return detected_audio
            except asyncio.CancelledError:
                logger.info("리스닝 작업이 취소되었습니다.")
                return None

    def _clear_queues(self):
        """큐에 남아있는 이전 데이터를 모두 비웁니다."""
        while not self.input_queue.empty():
            self.input_queue.get_nowait()
        while not self.output_queue.empty():
            self.output_queue.get_nowait()

    def close(self) -> None:
        """애플리케이션 종료 시 처리 스레드와 Cobra 인스턴스를 안전하게 해제합니다."""
        self.stop_event.set()
        if self.processing_thread.is_alive():
            self.processing_thread.join()
        if hasattr(self, 'cobra'):
            self.cobra.delete()
        logger.info("Cobra VAD 모듈이 정리되었습니다.")

    def initialize(self) -> None: pass
    def is_initialized(self) -> bool: return True