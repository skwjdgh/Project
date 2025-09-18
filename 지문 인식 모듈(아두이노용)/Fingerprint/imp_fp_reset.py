# imp_fp_reset.py

import serial
import os
import shutil
from def_fp_err import handle_error

def reset(ser):
    """
    센서의 모든 지문 데이터와 로컬 데이터를 삭제합니다.
    """
    confirm = input("\n정말로 모든 지문 데이터를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다. (y/n): ")
    if confirm.lower() != 'y':
        print("초기화 작업을 취소했습니다.")
        return
        
    try:
        print("지문 센서의 데이터를 초기화합니다...")
        ser.write(b"RESET\n")
        
        while True:
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                print(f"아두이노 응답: {response}")

                if response == "RESET_SUCCESS":
                    print("센서 데이터 초기화 성공.")
                    # 로컬 data_fp 폴더 삭제
                    if os.path.exists('data_fp'):
                        shutil.rmtree('data_fp')
                        print("로컬 데이터 폴더(data_fp)를 삭제했습니다.")
                    print("\n✨ 모든 데이터가 성공적으로 초기화되었습니다.")
                    break
                elif "FAIL" in response:
                    print(f"\n🚨 오류: {handle_error(response)}")
                    break
    
    except Exception as e:
        print(f"초기화 중 예외 발생: {e}")