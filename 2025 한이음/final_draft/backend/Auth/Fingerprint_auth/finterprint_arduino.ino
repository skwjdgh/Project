#include <Adafruit_Fingerprint.h>
#include <SoftwareSerial.h>

SoftwareSerial mySerial(2, 3);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

const unsigned long INPUT_TIMEOUT = 10000;

enum Command {
  UNKNOWN,
  ENROLL,
  MATCH,
  DELETE
};

// ####################################
//   문자열 명령을 enum으로 변환
// ####################################
Command getCommand(String cmdStr) {
  if (cmdStr.equals("enroll")) return ENROLL;
  if (cmdStr.equals("match")) return MATCH;
  if (cmdStr.equals("delete")) return DELETE;
  return UNKNOWN;
}

// ####################################
//  초기 설정 및 센서 연결 확인
// ####################################
void setup() {
  Serial.begin(9600);
  finger.begin(57600);
  delay(50);

  if (finger.verifyPassword()) {
    Serial.println("STATUS:Found fingerprint sensor!");
  } else {
    Serial.println("STATUS:Did not find fingerprint sensor :(");
    while (1) { delay(1); }
  }
}

// ####################################
//  메인 루프: Pi로부터 명령 수신
// ####################################
void loop() {
  if (Serial.available() > 0) {
    String commandStr = Serial.readStringUntil('\n');
    commandStr.trim();
    
    switch (getCommand(commandStr)) {
      case ENROLL:
        enrollFingerprint();
        break;
      case MATCH:
        matchFingerprint();
        break;
      case DELETE:
        deleteFingerprint();
        break;
      default:
        Serial.println("ERROR:Unknown command");
        break;
    }
  }
}

// ####################################
// 사용자 ID 입력 수신 (타임아웃 적용)
// ####################################
int readUserID() {
  unsigned long startTime = millis();
  while (Serial.available() == 0) {
    if (millis() - startTime > INPUT_TIMEOUT) {
      Serial.println("ERROR:Input timeout!");
      return 0;
    }
  }
  int id = Serial.parseInt();
  while(Serial.available() > 0) { Serial.read(); }
  return id;
}

// ####################################
//      지문 등록 절차 수행
// ####################################
void enrollFingerprint() {
  Serial.println("CMD:Please type in the ID # (from 1 to 127)...");
  int id = readUserID();
  if (id == 0) return;

  Serial.println("STATUS:Waiting for a finger to enroll as #" + String(id));
  
  // 1단계
  Serial.println("STATUS:Place finger on sensor...");
  while (finger.getImage() != FINGERPRINT_OK);
  finger.image2Tz(1);
  Serial.println("STATUS:Image taken. Remove finger.");
  delay(2000);
  while (finger.getImage() != FINGERPRINT_NOFINGER);

  // 2단계
  Serial.println("STATUS:Place same finger again...");
  while (finger.getImage() != FINGERPRINT_OK);
  finger.image2Tz(2);
  Serial.println("STATUS:Image taken.");

  if (finger.createModel() == FINGERPRINT_OK && finger.storeModel(id) == FINGERPRINT_OK) {
    Serial.println("RESULT:SUCCESS:Stored successfully!");
  } else {
    Serial.println("RESULT:ERROR:Failed to create or store model.");
  }
}

// ####################################
//       지문 스캔 및 인증
// ####################################
void matchFingerprint() {
  Serial.println("STATUS:Waiting for a finger to identify...");
  while (finger.getImage() != FINGERPRINT_OK);
  
  finger.image2Tz();
  
  if (finger.fingerSearch() == FINGERPRINT_OK) {
    Serial.print("RESULT:SUCCESS:Found ID #");
    Serial.print(finger.fingerID);
    Serial.print(" with confidence of ");
    Serial.println(finger.confidence);
  } else {
    Serial.println("RESULT:ERROR:Did not find a match.");
  }
}

// ####################################
//       저장된 지문 삭제
// ####################################
void deleteFingerprint() {
  Serial.println("CMD:Please type in the ID # (from 1 to 127) to delete...");
  int id = readUserID();
  if (id == 0) return;

  if (finger.deleteModel(id) == FINGERPRINT_OK) {
    Serial.println("RESULT:SUCCESS:Deleted!");
  } else {
    Serial.println("RESULT:ERROR:Failed to delete.");
  }
}