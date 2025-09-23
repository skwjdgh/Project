# imp_fp_verify.py

import serial
import json
from def_fp_err import handle_error

def verify(ser):
    """
    지문 확인 프로세스를 진행하고, 결과를 dict 형태로 반환합니다.
    """
    try:
        print("\n지문 확인을 시작합니다.")
        ser.write(b"VERIFY\n")
        
        while True:
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                print(f"아두이노 응답: {response}")

                if response == "PLACE_FINGER":
                    print("확인할 지문을 센서에 올려주세요...")
                
                elif response.startswith("VERIFY_SUCCESS"):
                    _, verified_id, confidence = response.split(',')
                    try:
                        with open(f'data_fp/{verified_id}.json', 'r', encoding='utf-8') as f:
                            user_data = json.load(f)
                        print(f"\n인증 성공! 환영합니다, {user_data['name']}님.")
                        return {"success": True, "userName": user_data['name']}
                    except FileNotFoundError:
                        print(f"\n경고: 센서 ID {verified_id} 확인, 로컬 데이터 없음.")
                        return {"success": False, "error": "USER_DATA_NOT_FOUND"}
                
                elif "FAIL" in response or "NOT_FOUND" in response:
                    error_msg = handle_error(response)
                    print(f"\n인증 실패: {error_msg}")
                    return {"success": False, "error": response}

    except Exception as e:
        print(f"확인 중 예외 발생: {e}")
        return {"success": False, "error": str(e)}

    return {"success": False, "error": "TIMEOUT"}