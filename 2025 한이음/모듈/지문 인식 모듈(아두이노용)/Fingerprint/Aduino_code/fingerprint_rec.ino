#include <Adafruit_Fingerprint.h>
#include <SoftwareSerial.h>

// 아두이노의 2번, 3번 핀을 지문 센서의 TX, RX에 연결합니다.
SoftwareSerial mySerial(2, 3);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

void setup() {
  Serial.begin(9600); // PC와의 시리얼 통신 시작
  while (!Serial) {
    ; // 시리얼 포트가 연결될 때까지 대기
  }
  
  // 지문 센서와의 통신 속도 설정
  finger.begin(57600);
  delay(5);
  if (finger.verifyPassword()) {
    Serial.println("FOUND_SENSOR");
  } else {
    Serial.println("SENSOR_NOT_FOUND");
    while (1) { delay(1); }
  }
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.startsWith("ENROLL")) {
      int id = command.substring(7).toInt();
      enrollFingerprint(id);
    } else if (command == "VERIFY") {
      verifyFingerprint();
    } else if (command == "RESET") {
      resetFingerprints();
    }
  }
}

// 지문 등록 함수
void enrollFingerprint(int id) {
  Serial.println("ENROLL_START");
  Serial.flush();
  
  // 1단계: 첫 번째 이미지 캡처
  Serial.println("PLACE_FINGER");
  while (finger.getImage() != FINGERPRINT_OK);
  Serial.println("IMAGE_TAKEN");
  if (finger.image2Tz(1) != FINGERPRINT_OK) {
    Serial.println("ENROLL_FAIL");
    return;
  }
  
  Serial.println("REMOVE_FINGER");
  delay(2000);
  while (finger.getImage() != FINGERPRINT_NOFINGER);

  // 2단계: 두 번째 이미지 캡처
  Serial.println("PLACE_AGAIN");
  while (finger.getImage() != FINGERPRINT_OK);
  Serial.println("IMAGE_TAKEN");
  if (finger.image2Tz(2) != FINGERPRINT_OK) {
    Serial.println("ENROLL_FAIL");
    return;
  }
  
  // 모델 생성 및 저장
  if (finger.createModel() != FINGERPRINT_OK) {
    Serial.println("ENROLL_FAIL");
    return;
  }

  if (finger.storeModel(id) != FINGERPRINT_OK) {
    Serial.println("ENROLL_FAIL");
    return;
  }
  
  Serial.println("ENROLL_SUCCESS," + String(id));
}

// 지문 확인 함수
void verifyFingerprint() {
  Serial.println("VERIFY_START");
  Serial.println("PLACE_FINGER");
  
  while (finger.getImage() != FINGERPRINT_OK);

  if (finger.image2Tz() != FINGERPRINT_OK) {
    Serial.println("VERIFY_FAIL");
    return;
  }

  if (finger.fingerSearch() != FINGERPRINT_OK) {
    Serial.println("FINGER_NOT_FOUND");
    return;
  }
  
  Serial.println("VERIFY_SUCCESS," + String(finger.fingerID) + "," + String(finger.confidence));
}

// 지문 데이터 초기화 함수
void resetFingerprints() {
  if (finger.emptyDatabase() == FINGERPRINT_OK) {
    Serial.println("RESET_SUCCESS");
  } else {
    Serial.println("RESET_FAIL");
  }
}