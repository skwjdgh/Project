import sounddevice as sd

print("사용 가능한 오디오 장치 목록:")
print(sd.query_devices())

device_index = int(input("\n상세 정보를 확인할 마이크의 번호(INDEX)를 입력하세요: "))
device_info = sd.query_devices(device_index, 'input')
print(f"\n--- [장치 이름: {device_info['name']}] ---")
print(f"최대 입력 채널: {device_info['max_input_channels']}")
print(f"기본 샘플링 레이트: {device_info['default_samplerate']}")
