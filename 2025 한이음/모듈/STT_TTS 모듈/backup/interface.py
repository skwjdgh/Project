# /Backend/Utility/STT_TTS/interface.py

# #################################################
#   추상 인터페이스 정의 (Abstract Interfaces Definition)
# #################################################

from abc import ABC, abstractmethod
from typing import Generator

# 이 파일은 각 모듈이 어떤 메서드를 가져야 하는지에 대한 '설계도' 또는 '계약'을 정의합니다.
# 이를 통해 코드의 일관성을 유지하고, 다른 라이브러리로 쉽게 교체할 수 있습니다.

# ####################################
#   IModel: 기본 모델 인터페이스
# ####################################
class IModel(ABC):
    """모든 AI 모델 클래스가 따라야 할 기본 계약 (모델 로딩, 상태 확인, 리소스 해제)"""

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

# ####################################
#   ISTT: STT 인터페이스
# ####################################
class ISTT(IModel):
    """모든 STT 클래스가 따라야 할 계약"""

    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> str:
        """오디오 바이트를 텍스트로 변환하는 메서드."""
        pass

# ####################################
#   ITTS: TTS 인터페이스
# ####################################
class ITTS(IModel):
    """모든 TTS 클래스가 따라야 할 계약"""

    @abstractmethod
    def speak(self, text: str) -> None:
        """텍스트를 음성으로 변환하고 재생하는 메서드."""
        pass

# ####################################
#   IVAD: VAD 인터페이스
# ####################################
class IVAD(ABC):
    """모든 VAD 클래스가 따라야 할 계약"""

    @abstractmethod
    def listen(self) -> Generator[bytes, None, None]:
        """음성을 감지하고 음성 프레임을 반환(yield)하는 메서드."""
        pass

    @abstractmethod
    def close(self) -> None:
        """사용한 오디오 리소스를 정리하는 메서드."""
        pass