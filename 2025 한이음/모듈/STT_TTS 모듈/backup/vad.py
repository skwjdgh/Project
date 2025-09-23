# #################################################
#   음성 구간 탐지 모듈 (VAD w/ Resampling)
# #################################################

import webrtcvad
import pyaudio
import collections
import time
import numpy as np
from scipy.signal import resample_poly
from loguru import logger
from typing import Optional, Generator, Type, Dict, Any

from .interface import IVAD
from .exceptions import VADStreamError

class VoiceActivityDetector(IVAD):
    """
    음성 활동을 감지하여 음성 프레임만 반환하는 클래스.
    실시간 리샘플링 기능을 포함하여 하드웨어 호환성을 높임.
    """

    # ####################################
    #   VAD 객체 초기화
    # ####################################
    def __init__(self, config: Dict[str, Any], device_index: Optional[int] = None) -> None:
        """VAD, PyAudio 및 리샘플링 관련 파라미터를 초기화하고 마이크 스트림을 엽니다."""
        self.vad = webrtcvad.Vad(config['aggressiveness'])
        self.audio = pyaudio.PyAudio()

        # VAD가 요구하는 샘플링 속도와 하드웨어의 실제 샘플링 속도를 분리
        self.VAD_RATE = config['rate']
        self.HARDWARE_RATE = config.get('hardware_rate', self.VAD_RATE)
        
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.FRAME_DURATION_MS = config['frame_duration_ms']
        # 청크 크기는 하드웨어의 실제 샘플링 속도를 기준으로 계산
        self.CHUNK = int(self.HARDWARE_RATE * self.FRAME_DURATION_MS / 1000)
        
        self.device_index = device_index
        self.timeout_seconds = config['timeout_seconds']
        self.min_speech_frames = config['min_speech_frames']

        logger.info(f"마이크 스트림 시작 (하드웨어: {self.HARDWARE_RATE}Hz -> VAD: {self.VAD_RATE}Hz)")
        # 마이크 스트림은 하드웨어의 실제 샘플링 속도로 엽니다.
        self.stream = self.audio.open(format=self.FORMAT,
                                      channels=self.CHANNELS,
                                      rate=self.HARDWARE_RATE,
                                      input=True,
                                      frames_per_buffer=self.CHUNK,
                                      input_device_index=self.device_index)

    # ####################################
    #   음성 입력 리스닝 및 리샘플링
    # ####################################
    def listen(self) -> Generator[bytes, None, None]:
        """마이크 입력을 들으면서 음성 구간을 감지하고, 원본 오디오 데이터를 반환합니다."""
        ring_buffer_size = int(self.timeout_seconds / (self.FRAME_DURATION_MS / 1000))
        ring_buffer = collections.deque(maxlen=ring_buffer_size)
        triggered = False
        voiced_frames = []

        logger.info("🎤 음성 입력을 기다립니다...")

        try:
            while True:
                # 1. 하드웨어 속도로 원본 오디오 데이터 읽기
                frame_hw = self.stream.read(self.CHUNK, exception_on_overflow=False)
                
                # 2. VAD 처리를 위한 실시간 리샘플링
                audio_np_hw = np.frombuffer(frame_hw, dtype=np.int16)
                audio_np_vad = resample_poly(audio_np_hw, self.VAD_RATE, self.HARDWARE_RATE).astype(np.int16)
                frame_vad = audio_np_vad.tobytes()

                # VAD 프레임 길이에 맞게 조정 (webrtcvad는 10, 20, 30ms 프레임만 처리)
                vad_frame_len = int(self.VAD_RATE * self.FRAME_DURATION_MS / 1000 * 2) # 샘플당 2바이트
                if len(frame_vad) > vad_frame_len:
                    frame_vad = frame_vad[:vad_frame_len]

                # 3. 리샘플링된 데이터로 음성 여부 판단
                is_speech = self.vad.is_speech(frame_vad, self.VAD_RATE)

                # 4. 음성 감지 로직 (STT에는 고품질 원본 오디오를 저장)
                if not triggered:
                    ring_buffer.append((frame_hw, is_speech))
                    num_voiced = len([s for f, s in ring_buffer if s])
                    if num_voiced > 0.8 * ring_buffer.maxlen:
                        triggered = True
                        logger.info("🔴 음성 감지 시작됨")
                        voiced_frames.extend([f for f, s in ring_buffer])
                        ring_buffer.clear()
                else:
                    voiced_frames.append(frame_hw) # 원본 오디오 프레임 저장
                    ring_buffer.append((frame_hw, is_speech))
                    num_unvoiced = len([s for f, s in ring_buffer if not s])
                    if num_unvoiced > 0.9 * ring_buffer.maxlen:
                        logger.info("...음성 감지 종료됨")
                        # 최소 0.5초 이상 녹음된 경우에만 데이터 반환
                        if len(voiced_frames) * self.CHUNK / self.HARDWARE_RATE > 0.5:
                            yield b''.join(voiced_frames)
                        # 상태 초기화
                        triggered = False
                        voiced_frames = []
                        ring_buffer.clear()
                        logger.info("\n🎤 다음 음성 입력을 기다립니다...")
        except IOError as e:
            logger.error(f"마이크 스트림 읽기 오류: {e}", exc_info=True)
            raise VADStreamError("마이크 입력에 문제가 발생했습니다.") from e
        except KeyboardInterrupt:
            logger.info("VAD 리스닝이 중단되었습니다.")
        finally:
            if self.stream.is_active():
                self.stream.stop_stream()
            logger.info("VAD 스트림이 정리되었습니다.")

    # ####################################
    #   리소스 정리 (Context Manager)
    # ####################################
    def close(self) -> None:
        """오디오 스트림과 PyAudio 인스턴스를 모두 종료합니다."""
        if self.stream.is_active(): self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        logger.info("오디오 리소스가 정리되었습니다.")

    def __enter__(self) -> 'VoiceActivityDetector':
        return self

    def __exit__(self, exc_type: Type[BaseException], exc_val: BaseException, exc_tb: Any) -> None:
        self.close()