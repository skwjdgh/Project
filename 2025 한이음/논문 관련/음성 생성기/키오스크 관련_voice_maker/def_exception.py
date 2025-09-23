import logging

class AudioGenerationError(Exception):
    """오디오 생성 과정에서 오류가 발생했을 때 사용되는 예외입니다."""
    pass

class CSVReadError(Exception):
    """CSV 파일을 읽는 과정에서 오류가 발생했을 때 사용되는 예외입니다."""
    pass

def handle_error(e, detail=""):
    """발생한 예외를 로깅합니다."""
    logging.error(f"An error occurred: {e} | Details: {detail}", exc_info=True)
