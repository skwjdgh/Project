# -*- coding: utf-8 -*-
"""
프로그램 전반에서 공통적으로 사용하는 예외 클래스 정의.

- ExperimentError: 실험(파이프라인) 전반에서 발생하는 최상위 예외의 베이스 클래스.
- DataLoadError: GT CSV/오디오 파일 등 데이터 로드 단계에서의 오류.
- TranscribeError: STT(Whisper) 호출 및 디코딩 과정에서의 오류.
- TokenizerInitWarning: 형태소 분석기 등 토크나이저 초기화 문제가 있을 때 알림용 경고.
"""

class ExperimentError(Exception):
    """모든 실험 관련 예외의 베이스 클래스. 상속용."""
    pass

class DataLoadError(ExperimentError):
    """데이터 경로/인코딩/스키마 등 입력 데이터 계층에서 발생하는 오류."""
    pass

class TranscribeError(ExperimentError):
    """STT(Whisper) 호출 실패, 결과 포맷 이상 등 음성→텍스트 전환에서의 오류."""
    pass

class TokenizerInitWarning(Warning):
    """형태소 분석기(예: MeCab) 초기화 실패 시, 정규식 폴백 사용을 알리는 경고."""
    pass
