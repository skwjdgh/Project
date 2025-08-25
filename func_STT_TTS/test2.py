# --- 파일: Backend/Utility/STT_TTS/test2.py ---
"""
단독 STT/TTS 연동 테스트 스크립트.

- 패키지로 실행: python -m Backend.Utility.STT_TTS.test2
- ITTS.synthesize() 또는 speak() 어느 쪽도 지원
- 5초 녹음(16 kHz, mono) → STT → 결과를 다시 TTS로 피드백
"""

from __future__ import annotations

import os
import atexit
import asyncio
import tempfile
import platform
import subprocess
from typing import Optional

import numpy as np
import sounddevice as sd
from loguru import logger
from dotenv import load_dotenv

# 패키지 상대 import
from .factory import load_config, create_stt, create_tts, setup_logging  # type: ignore
from .def_interface import ISTT, ITTS  # type: ignore
from .def_exceptions import TranscriptionError, TTSError  # type: ignore

# 프로젝트 루트(.env, config.yaml) 경로
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yaml")

# 녹음 파라미터
RECORD_SECONDS = 5
SAMPLE_RATE = 16000  # 16 kHz mono 권장

# ------------------------------- 유틸 -------------------------------

def _say_with_tts(tts: ITTS, text: str, title: str = "tts_output") -> Optional[str]:
    """
    ITTS가 synthesize(text)->bytes 를 제공하면 임시 mp3로 저장 후 OS 기본 플레이어로 재생.
    speak(text)만 제공하면 그 메서드를 호출.
    """
    try:
        if hasattr(tts, "synthesize"):
            audio_bytes = tts.synthesize(text)  # type: ignore[attr-defined]
            if not audio_bytes:
                return None
            tmp = os.path.join(tempfile.gettempdir(), f"{title}.mp3")
            with open(tmp, "wb") as f:
                f.write(audio_bytes)

            # OS 기본 플레이어로 비차단 재생
            system = platform.system().lower()
            try:
                if "windows" in system:
                    os.startfile(tmp)  # type: ignore[attr-defined]
                elif "darwin" in system:
                    subprocess.Popen(["open", tmp])
                else:
                    subprocess.Popen(["xdg-open", tmp])
            except Exception as e:
                logger.warning(f"OS 플레이어 재생 실패(무시): {e}")
            return tmp

        if hasattr(tts, "speak"):
            getattr(tts, "speak")(text)  # type: ignore[misc]
            return None

        logger.warning("TTs 객체에 synthesize/speak가 없어 음성 안내를 생략합니다.")
        return None

    except TTSError as e:
        logger.warning(f"TTS 합성 실패(무시): {e}")
        return None


def _record_audio(duration: int, samplerate: int) -> np.ndarray:
    """duration초 동안 mono 녹음하여 int16 numpy 배열((N,1))을 반환."""
    logger.info(f"{duration}초 동안 녹음합니다... 말씀해 주세요!")
    sd.default.samplerate = samplerate
    sd.default.channels = 1
    rec = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    logger.info("녹음 완료.")
    return rec

# ------------------------------ 메인 루틴 ------------------------------

async def main(stt: ISTT, tts: ITTS) -> None:
    logger.info("🚀 STT/TTS 테스트 시작")

    # 1) 안내 TTS (실패해도 계속 진행)
    _say_with_tts(tts, f"T T S 기능을 테스트합니다. 잠시 후 {RECORD_SECONDS}초 동안 녹음합니다.", title="tts_intro")
    await asyncio.sleep(1.0)

    # 2) 녹음(동기 → 스레드)
    audio_np: np.ndarray = await asyncio.to_thread(_record_audio, RECORD_SECONDS, SAMPLE_RATE)
    audio_bytes: bytes = audio_np.tobytes()
    if not audio_bytes:
        logger.error("녹음된 오디오가 비었습니다.")
        return

    # 3) STT
    logger.info("음성 인식 시작…")
    try:
        recognized: str = await asyncio.to_thread(stt.transcribe, audio_bytes)
    except TranscriptionError as e:
        logger.error(f"STT 실패: {e}")
        recognized = ""

    if recognized:
        logger.info(f"[인식 결과] {recognized}")
        _say_with_tts(tts, f"인식된 문장은, {recognized} 입니다.", title="tts_result")
    else:
        logger.warning("음성을 인식하지 못했습니다.")
        _say_with_tts(tts, "음성을 인식하지 못했습니다.", title="tts_empty")

    logger.info("테스트 종료.")

# ------------------------------ 엔트리 ------------------------------

if __name__ == "__main__":
    setup_logging()
    load_dotenv(ENV_PATH)

    stt_module: Optional[ISTT] = None
    tts_module: Optional[ITTS] = None

    def _cleanup():
        try:
            if stt_module:
                stt_module.close()
        finally:
            if tts_module:
                tts_module.close()

    atexit.register(_cleanup)

    try:
        # 설정 로드 및 모듈 생성/초기화
        config = load_config(CONFIG_PATH)
        stt_module = create_stt(config)
        tts_module = create_tts(config)
        stt_module.initialize()
        tts_module.initialize()
        logger.info("✅ STT/TTS 모듈 초기화 완료")

        asyncio.run(main(stt_module, tts_module))
    except Exception as e:
        logger.critical(f"프로그램 초기화 중 오류: {e}", exc_info=True)
