class KioskException(Exception):
    """이 애플리케이션의 모든 커스텀 예외가 상속받는 기본 예외 클래스"""
    pass

class TranscriptionError(KioskException):
    """STT(음성->텍스트) 변환 실패 시 발생하는 전용 예외"""
    pass

class TTSError(KioskException):
    """TTS(텍스트->음성) 생성 또는 재생 실패 시 발생하는 전용 예외"""
    pass

class VADStreamError(KioskException):
    """VAD 마이크 스트림(입력)에서 오류 발생 시 던져지는 전용 예외"""
    pass