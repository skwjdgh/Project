# 이 파일은 'STT_TTS' 폴더를 파이썬 패키지로 만들어줍니다.
# 다른 파일에서 'from Backend.Utility.STT_TTS import ...'와 같이 호출할 때,
# 이 파일에 정의된 것들을 간편하게 가져올 수 있도록 설정합니다.

# 팩토리 함수: 각 모듈(STT, TTS, VAD)의 인스턴스를 생성하고 설정을 로드합니다.
from .factory import create_stt, create_tts, create_vad, load_config, setup_logging
# 인터페이스 정의: 각 모듈이 따라야 할 설계도(추상 클래스)입니다.
from .def_interface import ISTT, ITTS, IVAD
# 사용자 정의 예외: 이 패키지에서 발생할 수 있는 특정 오류들을 정의합니다.
from .def_exceptions import KioskException, TranscriptionError, TTSError, VADStreamError
# 타입 정의: 설정 파일(config.yaml)의 구조를 미리 정의하여 코드 안정성을 높입니다.
from .def_types import AppConfig