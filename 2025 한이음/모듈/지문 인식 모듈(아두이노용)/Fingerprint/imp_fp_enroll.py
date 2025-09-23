# imp_fp_enroll.py

import serial
import json
import os
import time
import re  # 주민등록번호 형식 검사를 위해 re 모듈 추가
from def_fp_err import handle_error

def get_user_info():
    """
    사용자로부터 이름과 주민등록번호를 입력받고 유효성을 검사합니다.
    이름은 비워둘 수 없으며, 주민등록번호는 'xxxxxx-xxxxxxx' 형식이어야 합니다.
    """
    # 사용자 이름 입력
    while True:
        user_name = input("사용자 이름을 입력하세요: ")
        if user_name.strip():  # 공백만 입력하는 경우 방지
            break
        else:
            print("이름은 비워둘 수 없습니다. 다시 입력해주세요.")

    # 주민등록번호 입력 및 형식 검사
    while True:
        rrn = input("주민등록번호 13자리를 입력하세요 (예: 991231-1234567): ")
        # 정규표현식을 사용하여 '숫자6자리-숫자7자리' 형식인지 확인
        if re.match(r'^\d{6}-\d{7}$', rrn):
            return user_name, rrn
        else:
            print("잘못된 형식입니다. 'xxxxxx-xxxxxxx' 형식으로 다시 입력해주세요.")

def enroll(ser):
    """
    지문 등록 프로세스를 진행합니다.
    """
    try:
        # data_fp 폴더 확인 및 생성
        if not os.path.exists('data_fp'):
            os.makedirs('data_fp')

        # 다음 등록할 ID 결정
        files = os.listdir('data_fp')
        next_id = 1
        if files:
            ids = sorted([int(f.split('.')[0]) for f in files if f.endswith('.json')])
            if ids:
                next_id = ids[-1] + 1
        
        print(f"\n새로운 지문을 ID {next_id}로 등록합니다.")
        ser.write(f"ENROLL,{next_id}\n".encode())
        
        while True:
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                print(f"아두이노 응답: {response}")

                if response == "PLACE_FINGER":
                    print("지문 센서에 손가락을 올려주세요...")
                elif response == "IMAGE_TAKEN":
                    print("이미지를 캡처했습니다.")
                elif response == "REMOVE_FINGER":
                    print("손가락을 떼어주세요.")
                elif response == "PLACE_AGAIN":
                    print("같은 손가락을 다시 올려주세요...")
                elif response.startswith("ENROLL_SUCCESS"):
                    _, enrolled_id = response.split(',')
                    
                    # 수정된 사용자 정보 입력 함수 호출
                    user_name, rrn = get_user_info()
                    
                    # 저장할 데이터에 주민등록번호(rrn) 추가
                    fingerprint_data = {
                        "id": int(enrolled_id),
                        "name": user_name,
                        "rrn": rrn,  # 주민등록번호 필드 추가
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 한글 깨짐 방지를 위해 encoding='utf-8' 및 ensure_ascii=False 추가
                    with open(f'data_fp/{enrolled_id}.json', 'w', encoding='utf-8') as f:
                        json.dump(fingerprint_data, f, indent=4, ensure_ascii=False)
                        
                    print(f"\n🎉 지문 등록 성공! (ID: {enrolled_id}, 이름: {user_name})")
                    break
                elif "FAIL" in response or "NOT_FOUND" in response:
                    print(f"\n🚨 오류: {handle_error(response)}")
                    break

    except Exception as e:
        print(f"등록 중 예외 발생: {e}")