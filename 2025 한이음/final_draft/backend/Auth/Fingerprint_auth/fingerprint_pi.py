import serial
import time
import re
import glob

BAUD_RATE = 9600

# ####################################
#    아두이노 포트 자동 검색
# ####################################
def find_arduino_port():
    """/dev/ttyACM* 패턴을 사용하여 아두이노 포트를 자동으로 찾습니다."""
    ports = glob.glob('/dev/ttyACM*')
    if not ports:
        return None
    if len(ports) > 1:
        print(f"여러 개의 포트를 찾았습니다: {ports}. 첫 번째 포트({ports[0]})를 사용합니다.")
    return ports[0]

class FingerprintAuth:
    # ####################################
    # 시리얼 통신 초기화 및 센서 확인
    # ####################################
    def __init__(self, port, baudrate):
        if port is None:
            print("❌ 아두이노를 찾을 수 없습니다. USB 연결을 확인하세요.")
            exit()
        
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)
            print(f"아두이노 포트({port})에 연결되었습니다.")
            
            sensor_status = self.read_serial()
            if "Found fingerprint sensor" in sensor_status:
                print("✅ 지문 센서가 성공적으로 연결되었습니다.")
            else:
                print("❌ 지문 센서를 찾을 수 없습니다. 아두이노-센서 연결을 확인하세요.")
                self.ser.close()
                exit()
        except serial.SerialException as e:
            print(f"오류: 시리얼 포트 '{port}'에 연결할 수 없습니다. 에러: {e}")
            exit()

    # ####################################
    # 아두이노로부터 시리얼 데이터 수신
    # ####################################
    def read_serial(self, timeout=5):
        """아두이노로부터 시리얼 데이터를 읽고 출력합니다."""
        lines = []
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    lines.append(line)
                    print(f"  [Arduino]: {line}")
            if lines and ("RESULT:" in lines[-1] or "CMD:" in lines[-1]):
                break
        return "\n".join(lines)

    # ####################################
    #      아두이노로 명령어 전송
    # ####################################
    def send_command(self, command, data=None):
        """아두이노에 명령과 데이터를 전송합니다."""
        print(f"\n[Pi -> Arduino]: '{command}' 명령 전송")
        self.ser.write(f"{command}\n".encode('utf-8'))
        if data:
            time.sleep(0.1)
            self.ser.write(f"{data}\n".encode('utf-8'))

    # ####################################
    #    지문 인증 요청 및 결과 처리
    # ####################################
    def fingerprint_authentication(self):
        """지문 인증을 요청하고 결과를 반환합니다."""
        self.send_command("match")
        response = self.read_serial()
        
        match = re.search(r'RESULT:SUCCESS:Found ID #(\d+)', response)
        if match:
            user_id = int(match.group(1))
            print(f"✅ 인증 성공! (ID: {user_id})")
            return True, user_id
        else:
            print("❌ 인증 실패: 일치하는 지문을 찾지 못했습니다.")
            return False, None

    # ####################################
    #       지문 등록 절차 시작
    # ####################################
    def enroll_fingerprint(self):
        """새로운 지문을 등록합니다."""
        self.send_command("enroll")
        response = self.read_serial()
        
        if "CMD:Please type in the ID" in response:
            try:
                user_id_str = input(">> 등록할 ID 번호(1-127)를 입력하세요: ")
                user_id = int(user_id_str)
                if not 1 <= user_id <= 127:
                    print("❌ ID는 1에서 127 사이여야 합니다.")
                    self.send_command("\n")
                    return
                
                self.ser.write(f"{user_id}\n".encode('utf-8'))
                response = self.read_serial(timeout=20)
                
                if "RESULT:SUCCESS" in response:
                    print("✅ 지문이 성공적으로 등록되었습니다.")
                else:
                    print("❌ 지문 등록에 실패했습니다.")
            except ValueError:
                print("❌ 잘못된 입력입니다. 숫자를 입력해야 합니다.")
                self.send_command("\n")

    # ####################################
    #       지문 삭제 절차 시작
    # ####################################
    def delete_fingerprint(self):
        """저장된 지문을 삭제합니다."""
        self.send_command("delete")
        response = self.read_serial()
        
        if "CMD:Please type in the ID" in response:
            try:
                user_id_str = input(">> 삭제할 ID 번호(1-127)를 입력하세요: ")
                int(user_id_str)
                
                self.ser.write(f"{user_id_str}\n".encode('utf-8'))
                response = self.read_serial(timeout=5)
                
                if "RESULT:SUCCESS" in response:
                    print("✅ 지문이 성공적으로 삭제되었습니다.")
                else:
                    print("❌ 지문 삭제에 실패했습니다.")
            except ValueError:
                print("❌ 잘못된 입력입니다. 숫자를 입력해야 합니다.")
                self.send_command("\n")

# ####################################
#        메인 프로그램 실행
# ####################################
def main():
    """메인 실행 함수"""
    arduino_port = find_arduino_port()
    auth_system = FingerprintAuth(arduino_port, BAUD_RATE)
    
    while True:
        print("\n" + "="*34)
        print("  지문 인증 시스템 (v2.2 - KR)")
        print("-"*34)
        print("  1. 지문 인증")
        print("  2. 지문 등록")
        print("  3. 지문 삭제")
        print("  4. 종료")
        print("="*34)
        choice = input(">> 원하는 작업의 번호를 선택하세요: ")

        if choice == '1':
            auth_system.fingerprint_authentication()
        elif choice == '2':
            auth_system.enroll_fingerprint()
        elif choice == '3':
            auth_system.delete_fingerprint()
        elif choice == '4':
            print("프로그램을 종료합니다.")
            auth_system.ser.close()
            break
        else:
            print("잘못된 선택입니다. 1, 2, 3, 4 중 하나를 입력하세요.")
        time.sleep(1)

if __name__ == "__main__":
    main()