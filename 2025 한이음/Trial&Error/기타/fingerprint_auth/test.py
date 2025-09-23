# /Backend/Utility/STT_TTS/test.py

# #################################################
#   STT/TTS/VAD 모듈 통합 테스트 스크립트
# #################################################

import os
from dotenv import load_dotenv

# --- .env 파일 경로 지정 및 로드 (가장 먼저 실행) ---
# test.py 파일의 위치를 기준으로 프로젝트 루트 폴더의 .env 파일을 찾음
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

import pyaudio
from loguru import logger
from typing import List

# --- 상대 경로를 사용한 모듈 임포트 ---
from .factory import load_config, create_stt, create_tts, create_vad, setup_logging, setup_timezone
from .interface import ISTT, ITTS, IVAD
from .exceptions import TranscriptionError, TTSError, VADStreamError

# ####################################
#   마이크 선택 함수
# ####################################
def select_mic() -> int:
    """
    사용 가능한 마이크 목록을 보여주고 사용자에게 선택을 요청합니다.
    """
    p = pyaudio.PyAudio()
    mic_indices: List[int] = []
    logger.info("사용 가능한 마이크 목록:")
    for i in range(p.get_device_count()):
        if p.get_device_info_by_index(i).get('maxInputChannels') > 0:
            logger.info(f" [{i}] {p.get_device_info_by_index(i).get('name')}")
            mic_indices.append(i)
    p.terminate()

    if not mic_indices:
        raise VADStreamError("사용 가능한 마이크가 없습니다.")

    while True:
        try:
            choice_str = input("테스트에 사용할 마이크의 번호를 입력하세요: ")
            choice = int(choice_str)
            if choice in mic_indices:
                logger.info(f"마이크 {choice}번을 선택했습니다.")
                return choice
            else:
                logger.warning("목록에 없는 번호입니다. 다시 입력해주세요.")
        except ValueError:
            logger.warning("숫자를 입력해주세요.")

# ####################################
#   테스트 메인 루프
# ####################################
def main(stt: ISTT, tts: ITTS, vad: IVAD) -> None:
    """
    VAD -> STT -> TTS 순서로 모듈의 통합 동작을 테스트하는 메인 루프를 실행합니다.
    """
    logger.info("=" * 40)
    logger.info("🚀 로컬 모듈 통합 테스트를 시작합니다. '종료'라고 말하면 테스트가 중단됩니다.")
    logger.info("=" * 40)

    try:
        # 초기 안내 음성
        tts.speak("안녕하세요. 테스트를 시작합니다. 말씀해주세요.")

        # VAD의 컨텍스트 매니저(`with`)를 사용하여 리소스를 안전하게 관리
        with vad:
            # VAD가 음성을 감지하면 audio_frames를 반환하며 루프가 실행됨
            for audio_frames in vad.listen():
                try:
                    # 1. 음성을 텍스트로 변환
                    recognized_text = stt.transcribe(audio_frames)
                    
                    if recognized_text:
                        logger.info(f"[인식된 내용]: {recognized_text}")

                        # 2. 종료 명령어 확인
                        if "종료" in recognized_text:
                            tts.speak("테스트를 종료합니다.")
                            break
                        
                        # 3. 인식된 내용을 다시 음성으로 출력 (Echo)
                        response = f"'{recognized_text}' 라고 인식되었습니다."
                        tts.speak(response)

                # 개별 작업 실패가 전체 테스트 중단으로 이어지지 않도록 예외 처리
                except TranscriptionError as e:
                    logger.error(f"음성 인식 실패: {e}")
                    tts.speak("음성 인식에 실패했습니다.")
                except TTSError as e:
                    logger.error(f"음성 출력 실패: {e}")

    except VADStreamError as e:
        logger.critical(f"마이크 오류로 인해 테스트를 중단합니다: {e}")
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        logger.critical(f"예상치 못한 오류가 발생했습니다: {e}", exc_info=True)
    finally:
        logger.info("테스트 프로그램을 종료합니다.")

# ####################################
#   프로그램 진입점
# ####################################
if __name__ == '__main__':
    # 이 스크립트가 직접 실행될 때만 아래 코드가 실행됨
    setup_logging()
    
    try:
        # 위에서 정의한 project_root 변수를 사용하여 config.yaml 경로를 지정
        config_path = os.path.join(project_root, 'config.yaml')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"'{config_path}'에서 설정 파일을 찾을 수 없습니다.")
        
        config = load_config(config_path)
        setup_timezone(config)
        mic_index = select_mic()

        stt = create_stt(config)
        tts = create_tts(config)
        vad = create_vad(config, mic_index)

        logger.info("=" * 40)
        logger.info("테스트를 위해 AI 모델을 미리 로드합니다...")
        stt.initialize()
        tts.initialize()
        logger.info("✅ 모든 모델이 성공적으로 로드되었습니다.")
        
        main(stt, tts, vad)

    except FileNotFoundError as e:
        logger.critical(e)
    except (VADStreamError, Exception) as e:
        logger.critical(f"프로그램 초기화 중 심각한 오류 발생: {e}", exc_info=True)