# Kiosk 음성인식 백엔드 유틸리티

이 프로젝트는 라즈베리 파이 5에서 STT, TTS, VAD 기능을 제공하는 파이썬 유틸리티 모음입니다. 단순 스크립트를 넘어, 유지보수성과 안정성을 고려한 고도화된 아키텍처를 적용했습니다.

## 1. 아키텍처 및 설계

- **싱글턴(Singleton) 모델 관리**: `factory.py`에서 STT, TTS 모델 객체를 한 번만 생성하여 메모리 사용을 최적화하고, 반복적인 로딩을 방지합니다.
- **인터페이스 기반 설계**: `interface.py`의 추상 클래스를 통해 각 모듈의 역할을 정의하고 의존성을 낮춰, 향후 다른 라이브러리로 쉽게 교체할 수 있습니다.
- **계층적 예외 처리**: `exceptions.py`에 정의된 커스텀 예외(`TranscriptionError` 등)를 통해, 오류 발생 시 더욱 명확하고 안정적으로 대처합니다.
- **고급 로깅 시스템**: `loguru`를 사용하여 파일명, 함수명, 라인 번호까지 기록되는 상세하고 가독성 높은 로그를 통해 신속한 디버깅을 지원합니다.
- **자원 관리**: `ThreadPoolExecutor`를 활용하여 TTS 스레드를 효율적으로 관리하고, `with` 구문을 통한 VAD 리소스 자동 해제로 안정성을 높였습니다.

## 2. 단위 테스트

프로젝트의 안정성을 보장하기 위해 `pytest`와 `unittest.mock`을 사용한 단위 테스트가 구현되어 있습니다.

### 테스트 실행 방법

1.  **pytest 설치**
    ```bash
    pip install pytest
    ```
2.  **테스트 실행**
    `Utility` 디렉토리에서 아래 명령어를 실행하면 `tests/` 폴더의 모든 테스트를 자동으로 찾아 실행합니다.
    ```bash
    pytest -v
    ```

## 3. 의존성 설치

### 3.1. 시스템 라이브러리

```bash
sudo apt update
sudo apt install -y portaudio19-dev ffmpeg
```

### 3.2. MeloTTS 소스 코드

안정적인 버전 관리를 위해 특정 커밋을 사용하는 것을 권장합니다.
```bash
git clone https://github.com/myshell-ai/MeloTTS.git
cd MeloTTS
# git checkout <commit_hash>  # 특정 안정 버전으로 체크아웃 (예: git checkout 8d523c9)
cd ..
```

### 3.3. 파이썬 라이브러리

`Utility` 폴더에 `requirements.txt` 파일을 생성하고 아래 내용을 붙여넣으세요.

**`requirements.txt`:**
```txt
# Core ML & Audio
# 라즈베리 파이(aarch64)에 맞는 버전을 별도 설치해야 합니다. (아래 1단계 참고)
# torch
# torchaudio

# Basic
numpy==1.26.4
sounddevice==0.4.6
pyaudio==0.2.14
pyyaml==6.0.1

# Logging
loguru==0.7.2

# VAD
webrtcvad-wheels==2.0.10.post1

# STT
openai-whisper==20231117

# MeloTTS Dependencies
scipy
einops
eng_to_ipa
inflect
numba
phonemizer
tokenizers
tqdm
transformers
unidecode

# Testing
pytest
```

**설치 과정:**
```bash
# 1단계: PyTorch 설치 (aarch64, Python 3.10)
pip install torch torchaudio --extra-index-url https://www.piwheels.org/simple

# 2단계: requirements.txt로 나머지 패키지 설치
pip install -r requirements.txt

# 3단계: MeloTTS 설치 (Editable mode)
pip install -e MeloTTS/
```

## 4. 실행

모든 설정이 완료되면, 가상환경이 활성화된 상태에서 `test.py`를 실행합니다.
```bash
python3 test.py
```
프로그램은 마이크를 선택받은 후, STT/TTS 모델을 초기화하고 음성 안내를 시작합니다.