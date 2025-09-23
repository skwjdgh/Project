# def_fp_err.py

def handle_error(error_code):
    """
    아두이노로부터 받은 에러 코드를 처리합니다.
    """
    error_messages = {
        "SENSOR_NOT_FOUND": "지문 센서를 찾을 수 없습니다. 연결을 확인하세요.",
        "ENROLL_FAIL": "지문 등록에 실패했습니다. 다시 시도해주세요.",
        "VERIFY_FAIL": "지문 이미지 변환에 실패했습니다.",
        "FINGER_NOT_FOUND": "등록된 지문이 아닙니다.",
        "RESET_FAIL": "지문 데이터 초기화에 실패했습니다.",
        "NOT_FOUND": "등록된 지문이 아닙니다.",
        "TIMEOUT": "센서 응답이 지연되었습니다. 다시 시도해주세요."
    }
    return error_messages.get(error_code, "알 수 없는 오류가 발생했습니다.")