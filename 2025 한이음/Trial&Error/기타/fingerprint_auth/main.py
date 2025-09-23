# /main.py

# #################################################
#   AI 비서 메인 실행 스크립트 (최종 개선판)
# #################################################

import os
import sys
from dotenv import load_dotenv

# --- .env 파일 로드 (가장 먼저 실행) ---
load_dotenv()

# --- 이후 다른 모듈 임포트 ---
import asyncio
import atexit
import random
import gc
from loguru import logger
from openai import OpenAI, APIError, AuthenticationError, APITimeoutError
from typing import Dict, Any, List, Optional

# --- 절대 경로 설정 및 모듈 임포트 ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_PATH = os.path.join(PROJECT_ROOT, 'Backend')
sys.path.append(BACKEND_PATH)

from Utility.STT_TTS import create_stt, create_tts, create_vad, ISTT, ITTS, IVAD
from Utility.STT_TTS.factory import load_config
from Utility.STT_TTS.exceptions import TranscriptionError, TTSError, VADStreamError
from Utility.STT_TTS.test import setup_logging, select_mic
from Utility.STT_TTS.types import AppConfig

# --- 상수 정의 ---
MAX_CONSECUTIVE_FAILURES = 3
API_RETRY_ATTEMPTS = 3
VAD_LISTEN_TIMEOUT = 20.0
CONVERSATION_SUMMARY_THRESHOLD = 10 

# ####################################
#   유틸리티 함수: 종료 명령어 확인
# ####################################
def is_exit_command(text: str) -> bool:
    """사용자의 발화가 종료 명령어인지 유연하게 확인합니다."""
    normalized_text = text.strip().lower()
    exit_keywords = ["종료", "그만", "수고했어", "잘가"]
    return any(keyword in normalized_text for keyword in exit_keywords)

# ####################################
#   대화 요약 및 API 질의 함수
# ####################################
async def summarize_conversation(messages: List[Dict[str, str]], client: OpenAI) -> str:
    """긴 대화 내역을 요약하여 토큰 사용량을 관리합니다."""
    logger.info(f"대화 턴({len(messages)//2})이 길어져 요약을 시도합니다...")
    summary_prompt = "다음 대화 내용을 간결하게 요약해줘. 중요한 맥락은 유지해야 해:\n\n" + \
                     "\n".join([f"{m['role']}: {m['content']}" for m in messages if m['role'] != 'system'])
    
    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": summary_prompt}],
            timeout=45.0
        )
        summary = response.choices[0].message.content
        logger.info(f"대화 요약 완료: {summary}")
        return summary
    except Exception:
        logger.error("대화 요약에 실패했습니다.", exc_info=True)
        return "대화 요약에 실패했어요."

async def query_openai_api(messages: List[Dict[str, str]], client: OpenAI) -> str:
    """API 질의 (지수 백오프 재시도 포함)"""
    for attempt in range(API_RETRY_ATTEMPTS):
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-3.5-turbo", messages=messages, timeout=20.0
            )
            return response.choices[0].message.content.strip()
        except (APIError, APITimeoutError) as e:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"API 호출 실패 (시도 {attempt + 1}), {wait_time:.2f}초 후 재시도합니다. 오류: {e}")
            if attempt == API_RETRY_ATTEMPTS - 1:
                return "API 서버와 통신 중 문제가 발생했습니다."
            await asyncio.sleep(wait_time)
    return "API 호출에 실패했습니다."

# ####################################
#   대화형 루프
# ####################################
async def conversation_loop(stt: ISTT, tts: ITTS, config: AppConfig, client: OpenAI, mic_index: int) -> None:
    """사용자와의 연속적인 대화를 처리하는 메인 루프"""
    messages = [{"role": "system", "content": "당신은 사용자의 질문에 명확하고 친절하게 답변하는 AI 비서입니다."}]
    follow_up_prompts = ["더 궁금한 점 있으신가요?", "또 다른 질문이 있으세요?", "무엇을 더 도와드릴까요?"]
    consecutive_failures = 0

    await asyncio.to_thread(tts.speak, "안녕하세요. 무엇을 도와드릴까요?")

    while True:
        vad: Optional[IVAD] = None
        try:
            if len(messages) > CONVERSATION_SUMMARY_THRESHOLD:
                summary = await summarize_conversation(messages, client)
                messages = messages[:1] + [{"role": "assistant", "content": f"이전 대화 요약: {summary}"}]

            vad = create_vad(config, mic_index)
            logger.info("🎤 음성 명령 대기 중...")
            
            async with asyncio.timeout(VAD_LISTEN_TIMEOUT):
                audio_frames = await asyncio.to_thread(next, vad.listen(), None)
            
            if audio_frames is None: raise asyncio.TimeoutError
            
            user_query = await asyncio.to_thread(stt.transcribe, audio_frames)
            user_query = user_query.strip()
            
            if not user_query:
                consecutive_failures += 1
                logger.warning(f"음성 인식 실패 ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    await asyncio.to_thread(tts.speak, "계속해서 음성을 알아들을 수 없어 대화를 종료합니다.")
                    break
                await asyncio.to_thread(tts.speak, "주변이 조금 시끄러운 것 같아요. 다시 말씀해주세요.")
                continue

            consecutive_failures = 0
            logger.info(f"[사용자 질문]: '{user_query}'")
            
            if is_exit_command(user_query):
                await asyncio.to_thread(tts.speak, "대화를 종료하시겠어요? 네 라고 답해주세요.")
                confirm_audio = await asyncio.to_thread(next, vad.listen(), None)
                if confirm_audio:
                    confirmation = await asyncio.to_thread(stt.transcribe, confirm_audio)
                    if any(word in confirmation for word in ["네", "응", "그래"]):
                        await asyncio.to_thread(tts.speak, "알겠습니다. 대화를 종료합니다.")
                        break
                await asyncio.to_thread(tts.speak, "대화를 계속합니다.")
                continue

            messages.append({"role": "user", "content": user_query})
            api_answer = await query_openai_api(messages, client)
            messages.append({"role": "assistant", "content": api_answer})
            
            await asyncio.to_thread(tts.speak, api_answer)
            await asyncio.sleep(0.5)
            await asyncio.to_thread(tts.speak, random.choice(follow_up_prompts))

        except asyncio.TimeoutError:
            logger.warning(f"{VAD_LISTEN_TIMEOUT}초 동안 음성 입력이 없어 대기를 중단합니다.")
            await asyncio.to_thread(tts.speak, "혹시 질문 있으신가요? 다시 부르시면 대답할게요.")
        except (TranscriptionError, TTSError) as e:
            logger.error(f"STT/TTS 처리 중 오류: {e}", exc_info=True)
        except Exception as e:
            logger.critical(f"대화 루프 중 예상치 못한 오류: {e}", exc_info=True)
            await asyncio.to_thread(tts.speak, "시스템에 문제가 발생하여 대화를 종료합니다.")
            break
        finally:
            if vad: await asyncio.to_thread(vad.close)
            gc.collect()

# ####################################
#   메인 진입점
# ####################################
async def main():
    """애플리케이션 초기화 및 실행"""
    setup_logging()
    
    stt_module, tts_module = None, None
    
    def cleanup():
        logger.info("애플리케이션 종료. 모든 리소스를 정리합니다.")
        if stt_module and stt_module.is_initialized(): stt_module.close()
        if tts_module and tts_module.is_initialized(): tts_module.close()
    atexit.register(cleanup)

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key: raise ValueError("환경 변수 OPENAI_API_KEY가 없습니다.")
        
        openai_client = OpenAI(api_key=api_key)
        await asyncio.to_thread(openai_client.models.list)
        logger.info("✅ OpenAI API 키가 유효합니다.")
        
        config_path = os.path.join(PROJECT_ROOT, 'config.yaml')
        config: AppConfig = load_config(config_path)
        
        stt_module = create_stt(config)
        tts_module = create_tts(config)
        
        await asyncio.to_thread(stt_module.initialize)
        await asyncio.to_thread(tts_module.initialize)
        
        if not stt_module.is_initialized() or not tts_module.is_initialized():
             raise RuntimeError("STT 또는 TTS 모델 초기화에 실패했습니다.")
        
        mic_index = await asyncio.to_thread(select_mic)
        await conversation_loop(stt_module, tts_module, config, openai_client, mic_index)

    except Exception as e:
        logger.critical(f"프로그램 초기화 또는 실행 중 심각한 오류 발생: {e}", exc_info=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("사용자에 의해 프로그램이 강제 종료되었습니다.")