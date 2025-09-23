# fp_factory.py

import os
import yaml
import serial
import time

# Fingerprint 폴더 내의 다른 모듈들을 상대 경로로 가져옵니다.
from .imp_fp_enroll import enroll
from .imp_fp_verify import verify
from .imp_fp_reset import reset

# 전역 변수로 시리얼 연결 객체를 관리합니다.
ser = None

def _load_config():
    """
    프로젝트 루트의 config.yaml 파일을 찾아 설정을 불러옵니다.
    """
    # 현재 파일의 위치에서 시작하여 상위 폴더로 이동하며 config.yaml을 찾습니다.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # .../backend/Utility/Fingerprint -> .../backend/Utility -> .../backend -> .../
    config_path = os.path.abspath(os.path.join(current_dir, "../../../", "config.yaml"))
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"설정 파일(config.yaml)을 찾을 수 없습니다: {config_path}")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    if 'fingerprint' not in config:
        raise ValueError("config.yaml 파일에 'fingerprint' 설정이 없습니다.")
        
    return config['fingerprint']


def initialize_sensor():
    """
    config.yaml에서 설정을 읽어 지문 센서를 초기화하고 연결합니다.
    성공하면 시리얼 객체를, 실패하면 None을 반환합니다.
    """
    global ser
    
    # 이미 연결되어 있다면 기존 연결을 반환합니다.
    if ser and ser.is_open:
        print("이미 센서에 연결되어 있습니다.")
        return ser
        
    try:
        config = _load_config()
        port = config.get('serial_port', 'COM4')
        baud = config.get('baud_rate', 9600)
        
        ser = serial.Serial(port, baud, timeout=1)
        print(f"{port}에 연결되었습니다. 잠시 후 아두이노가 준비됩니다...")
        time.sleep(2)  # 아두이노 재시작 대기
        
        initial_message = ser.readline().decode().strip()
        if initial_message == "FOUND_SENSOR":
            print("지문 센서가 성공적으로 연결되었습니다. ✅")
            return ser
        else:
            print(f"지문 센서를 찾을 수 없습니다. (응답: {initial_message}) ❌")
            ser.close()
            ser = None
            return None
            
    except serial.SerialException as e:
        print(f"시리얼 포트 연결에 실패했습니다: {e}")
        print("포트 이름을 확인하고, 아두이노가 연결되었는지, config.yaml 설정이 올바른지 확인해주세요.")
        ser = None
        return None
    except Exception as e:
        print(f"센서 초기화 중 오류 발생: {e}")
        if ser and ser.is_open:
            ser.close()
        ser = None
        return None

def close_sensor_connection():
    """
    활성화된 시리얼 포트 연결을 닫습니다.
    """
    global ser
    if ser and ser.is_open:
        ser.close()
        ser = None
        print("시리얼 포트 연결을 해제했습니다.")

def get_sensor_connection():
    """
    현재 관리 중인 시리얼 연결 객체를 반환합니다.
    """
    global ser
    return ser

# --- 각 기능을 수행하는 래퍼(wrapper) 함수 ---

def enroll_fingerprint(ser_instance):
    """지문 등록 프로세스를 실행합니다."""
    if not ser_instance or not ser_instance.is_open:
        print("오류: 센서가 연결되지 않았습니다.")
        return
    enroll(ser_instance)

def verify_fingerprint(ser_instance):
    """지문 확인 프로세스를 실행합니다."""
    if not ser_instance or not ser_instance.is_open:
        print("오류: 센서가 연결되지 않았습니다.")
        return {"success": False, "error": "SENSOR_NOT_CONNECTED"}
    
    return verify(ser_instance)

def reset_database(ser_instance):
    """지문 데이터베이스 초기화 프로세스를 실행합니다."""
    if not ser_instance or not ser_instance.is_open:
        print("오류: 센서가 연결되지 않았습니다.")
        return
    reset(ser_instance)

def get_sensor_connection():
    """
    현재 관리 중인 시리얼 연결 객체를 반환합니다.
    연결이 끊겼다면 재연결을 시도합니다.
    """
    global ser
    # ser 객체가 없거나, 있더라도 연결이 닫혀있으면 재초기화 시도
    if not ser or not ser.is_open:
        print("센서 연결이 끊어져 있어 재연결을 시도합니다...")
        initialize_sensor() # 재연결 시도
    return ser