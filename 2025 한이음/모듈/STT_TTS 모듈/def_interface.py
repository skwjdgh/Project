from abc import ABC, abstractmethod
from typing import Generator, Optional, Coroutine

# --- 기본 모델 인터페이스 ---
class IModel(ABC):
    """
    모든 모듈(STT, TTS, VAD)이 공통적으로 가져야 할 기본 기능을 정의하는 추상 클래스.
    모델 로딩, 초기화 상태 확인, 리소스 해제 등 생명주기 관리를 위한 메서드를 포함합니다.
    """
    @abstractmethod
    def initialize(self) -> None:
        """모델을 명시적으로 로드하는 메서드."""
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """모델이 성공적으로 로드되었는지 확인하는 메서드."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """모듈의 리소스를 명시적으로 해제하는 메서드."""
        pass

# --- STT 인터페이스 ---
class ISTT(IModel):
    """
    STT(Speech-to-Text) 모듈을 위한 인터페이스.
    """
    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> str:
        """오디오 바이트를 텍스트로 변환하는 메서드."""
        pass

# --- TTS 인터페이스 ---
# 웹 환경에 맞게, 음성을 직접 재생하는 'speak' 대신
# 음성 데이터(bytes)를 생성하여 반환하는 'synthesize'로 메서드를 변경합니다.
class ITTS(IModel):
    """
    TTS(Text-to-Speech) 모듈을 위한 인터페이스.
    """
    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """텍스트를 음성 데이터(bytes)로 변환하여 반환하는 메서드."""
        pass

# --- VAD 인터페이스 ---
class IVAD(IModel):
    """
    VAD(Voice Activity Detector) 모듈을 위한 인터페이스.
    """
    @abstractmethod
    async def listen(self) -> Optional[bytes]:
        """음성이 감지될 때까지 비동기 대기하고, 감지된 오디오 데이터를 반환합니다."""
        pass