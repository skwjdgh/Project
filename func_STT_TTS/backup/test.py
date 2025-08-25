import os
from dotenv import load_dotenv
import atexit
import asyncio
import pyaudio
from loguru import logger
from typing import List

from .factory import load_config, create_stt, create_tts, create_vad, setup_logging
from .def_interface import ISTT, ITTS, IVAD
from .def_exceptions import TranscriptionError, TTSError, VADStreamError

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

def select_mic() -> int:
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
                return choice
            else:
                logger.warning("목록에 없는 번호입니다.")
        except ValueError:
            logger.warning("숫자를 입력해주세요.")

async def main(stt: ISTT, tts: ITTS, vad: IVAD) -> None:
    logger.info("🚀 로컬 모듈 통합 테스트를 시작합니다. '종료'라고 말하면 테스트가 중단됩니다.")
    try:
        await tts.speak("안녕하세요. 테스트를 시작합니다. 말씀해주세요.")

        # ❗❗ 오디오 장치 전환을 위한 딜레이 추가 ❗❗
        await asyncio.sleep(0.5) 

        while True: 
            audio_frames = await vad.listen()
            if not audio_frames:
                logger.warning("감지된 오디오 데이터가 없습니다.")
                continue
            try:
                recognized_text = await asyncio.to_thread(stt.transcribe, audio_frames)
                if recognized_text:
                    logger.info(f"[인식된 내용]: {recognized_text}")
                    if "종료" in recognized_text:
                        await tts.speak("테스트를 종료합니다.")
                        break
                    response = f"'{recognized_text}' 라고 인식되었습니다."
                    await tts.speak(response)
            except (TranscriptionError, TTSError) as e:
                logger.error(f"처리 중 오류: {e}")
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 테스트가 중단되었습니다.")
    finally:
        logger.info("테스트 프로그램을 종료합니다.")

if __name__ == '__main__':
    setup_logging()
    stt_module, tts_module, vad_module = None, None, None
    def cleanup():
        if vad_module: vad_module.close()
        if stt_module: stt_module.close()
        if tts_module: tts_module.close()
    atexit.register(cleanup)
    try:
        config_path = os.path.join(project_root, 'config.yaml')
        config = load_config(config_path)
        mic_index = select_mic()
        stt_module = create_stt(config)
        tts_module = create_tts(config)
        vad_module = create_vad(config, mic_index)
        stt_module.initialize()
        tts_module.initialize()
        logger.info("✅ 모든 모델이 성공적으로 로드되었습니다.")
        asyncio.run(main(stt_module, tts_module, vad_module))
    except Exception as e:
        # ❗❗ 이 부분을 아래 내용으로 완전히 교체합니다 ❗❗
        import traceback
        print("===================== 실제 오류 상세 정보 =====================")
        print(f"오류 타입: {type(e)}")
        print(f"오류 값: {e}")
        traceback.print_exc()
        print("==========================================================")
        logger.critical(f"프로그램 초기화 중 오류: {e}")