# factory_fp.py

import serial
import time
from imp_fp_enroll import enroll
from imp_fp_verify import verify
from imp_fp_reset import reset

# 사용자의 환경에 맞게 시리얼 포트와 속도를 설정하세요.
# 윈도우: "COM3", "COM4", ...
# 맥/리눅스: "/dev/tty.usbserial-XXXX" 또는 "/dev/ttyUSB0"
SERIAL_PORT = 'COM4'  # 예시 포트
BAUD_RATE = 9600

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"{SERIAL_PORT}에 연결되었습니다. 잠시 후 아두이노가 준비됩니다...")
        time.sleep(2)  # 아두이노 재시작 대기
        
        # 아두이노로부터 초기 메시지 확인
        initial_message = ser.readline().decode().strip()
        if initial_message == "FOUND_SENSOR":
            print("지문 센서가 성공적으로 연결되었습니다. ✅")
        else:
            print("지문 센서를 찾을 수 없습니다. 프로그램을 종료합니다. ❌")
            ser.close()
            return
            
    except serial.SerialException as e:
        print(f"시리얼 포트 연결에 실패했습니다: {e}")
        print("포트 이름을 확인하고, 아두이노가 연결되었는지 확인해주세요.")
        return

    while True:
        print("\n===== 지문 인식 관리 시스템 =====")
        print("1. 지문 등록")
        print("2. 지문 확인")
        print("3. 모든 데이터 초기화")
        print("4. 종료")
        choice = input("원하는 작업의 번호를 입력하세요: ")

        if choice == '1':
            enroll(ser)
        elif choice == '2':
            verify(ser)
        elif choice == '3':
            reset(ser)
        elif choice == '4':
            break
        else:
            print("잘못된 입력입니다. 1-4 사이의 숫자를 입력해주세요.")
            
    ser.close()
    print("프로그램을 종료합니다.")

if __name__ == "__main__":
    main()