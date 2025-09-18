# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, UploadFile, File, Form, Response, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
from dotenv import load_dotenv
from loguru import logger
from recognition import router as recognition_router
from weather import router as weather_router

import os
import json
import httpx
import tempfile
import subprocess

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, ".."))

# --- STT/TTS 통합: 모듈 import ---
# factory_backup -> factory로 경로를 수정하고, 필요한 예외 클래스를 import합니다.
from Utility.STT_TTS.factory import load_config, create_stt, create_tts, setup_logging
from Utility.STT_TTS.def_exceptions import TranscriptionError, TTSError

# ==================== 지문 인증 모듈 임포트 (주석 처리) ====================
import glob
import asyncio
import uuid
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect
# # 아래 함수들은 Utility/Fingerprint/fp_factory.py 와 같은 모듈에 구현되어야 합니다.
from Utility.Fingerprint import initialize_sensor, close_sensor_connection, get_sensor_connection, verify_fingerprint
# ======================================================================

# 환경변수 불러오기
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()
app.include_router(recognition_router)
app.include_router(weather_router)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STT/TTS 통합: 엔진 초기화 ---
# 프로젝트의 루트 디렉토리 경로를 계산하여 설정 파일을 올바르게 찾도록 합니다.
_stt = None
_tts = None

try:
    # .env와 config.yaml 파일 로드
    # load_dotenv(os.path.join(ROOT_DIR, ".env"))
    config = load_config(os.path.join(ROOT_DIR, "config.yaml"))
    setup_logging()

    # 설정 파일을 기반으로 STT, TTS 엔진 인스턴스 생성
    _stt = create_stt(config)
    _tts = create_tts(config)
    logger.info("STT/TTS 엔진 인스턴스 생성 완료.")

except Exception as e:
    logger.error(f"설정 파일 로드 또는 엔진 생성 실패: {e}")
    config = None

# ✅ 주요 키워드 사전
MINWON_KEYWORDS = {
    "등본": "주민등록등본 발급 요청",
    "주민등록등본": "주민등록등본 발급 요청",
    "주민등본": "주민등록등본 발급 요청",
    "초본": "주민등록초본 발급 요청",
    "주민등록초본": "주민등록초본 발급 요청",
    "주민초본": "주민등록초본 발급 요청",
    "가족관계증명서": "가족관계증명서 발급 요청",
    "가족관계증명": "가족관계증명서 발급 요청",
    "가족관계": "가족관계증명서 발급 요청",
    "가족증명": "가족관계증명서 발급 요청",
    "건강보험득실확인서": "건강보험득실확인서 발급 요청",
    "건강보험": "건강보험득실확인서 발급 요청",
    "건보": "건강보험득실확인서 발급 요청",
    "보험득실": "건강보험득실확인서 발급 요청",
    "보험득실확인": "건강보험득실확인서 발급 요청",
    "날씨": "날씨 정보 조회 요청",
    "오늘날씨": "날씨 정보 조회 요청",
    "내일날씨": "날씨 정보 조회 요청",
    "강수확률": "날씨 정보 조회 요청",
    "행사": "행사 정보 조회 요청",
    "축제": "행사 정보 조회 요청",
    "이벤트": "행사 정보 조회 요청",
    "페스티벌": "행사 정보 조회 요청",
}


# ✅ 키워드 기반 분석 함수
def get_purpose_by_keyword(user_input: str) -> str | None:
    for keyword, purpose in MINWON_KEYWORDS.items():
        if keyword in user_input:
            return purpose
    return None


# ✅ LLM 프롬프트
LLM_PROMPT = """
당신은 민원 키오스크 안내 도우미입니다.
아래는 사용자의 다양한 민원 요청 예시입니다.
반드시 **예시와 똑같은 한글 한 줄 요약**만 출력하세요.

[민원 목적 요약 예시]
- "등본 뽑아줘" → "주민등록등본 발급 요청"
- "등본 때고 싶어요" → "주민등록등본 발급 요청"
- "주민등록등본 필요합니다" → "주민등록등본 발급 요청"
- "초본 출력" → "주민등록초본 발급 요청"
- "가족관계증명서 뽑아줘" → "가족관계증명서 발급 요청"
- "가족관계증명 뽑을래" → "가족관계증명서 발급 요청"
- "토지대장 떼고싶어" → "토지(임야)대장 발급 요청"
- "여권 신청하고 싶어요" → "여권 발급 신청"
- "주민등록증 재발급 받아야 해" → "주민등록증 재발급 요청"
- "출입국 사실 증명 해주세요" → "출입국 사실증명 발급 요청"
- "오늘 날씨 알려줘" → "날씨 정보 조회 요청"
- "내일 비 오나?" → "날씨 정보 조회 요청"
- "근처 축제 뭐 있어?" → "행사 정보 조회 요청"
- "지역 행사 일정 알려줘" → "행사 정보 조회 요청"
- "공무원 시험 접수 안내해줘" → "민원 목적을 알 수 없음"
- "키오스크 고장났어요" → "민원 목적을 알 수 없음"
- "잡담" → "민원 목적을 알 수 없음"

[지침]
- 예시와 같이 반드시 한글 한 줄 요약으로만 답하세요.
- 예시에 없는 민원/잡담/질문 등은 반드시 '민원 목적을 알 수 없음'만 답하세요.
- 설명, 부가 텍스트, 인삿말 절대 금지.
"""


@app.on_event("startup")
async def startup_event():
    """FastAPI 앱 시작 시 STT/TTS 엔진을 초기화합니다."""
    if _stt:
        _stt.initialize()
        logger.info("STT 엔진 초기화 완료.")
    if _tts:
        _tts.initialize()
        logger.info("TTS 엔진 초기화 완료.")

    # --- 지문 센서 초기화 (주석 처리) ---
    initialize_sensor()


# 올바른 수정 예시
@app.on_event("shutdown")
def shutdown_event():
    """FastAPI 앱 종료 시 시리얼 포트를 닫습니다."""
    # --- 지문 센서 연결 해제 (주석 처리) ---
    close_sensor_connection()


def _ensure_wav(input_bytes: bytes, input_mime: str | None) -> bytes:
    """
    브라우저에서 전달받은 오디오 파일(webm, ogg 등)을 ETRI STT API가 요구하는
    WAV (16kHz, 1채널) 형식으로 변환합니다. 시스템에 ffmpeg가 설치되어 있어야 합니다.
    """
    mime = (input_mime or "").lower()

    # --- STT 문제 해결: 입력 데이터 유효성 검사 ---
    if not input_bytes or len(input_bytes) == 0:
        logger.error("입력 오디오 데이터가 비어있습니다.")
        raise ValueError("입력 오디오 데이터가 비어있습니다.")

    # 이미 wav 형식이면 변환 없이 바로 반환
    if "wav" in mime:
        return input_bytes

    # 임시 파일 생성하여 변환 작업 수행
    # delete=False: with 블록이 끝나도 파일이 지워지지 않도록 설정
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as src:
        src.write(input_bytes)
        src_path = src.name

    dst_path = src_path + ".wav"

    try:
        # --- STT 문제 해결: ffmpeg 명령어 실행 전 파일 존재 확인 ---
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"임시 파일 생성 실패: {src_path}")
        # --- 수정 완료 ---

        # ffmpeg 명령어 실행: -y(덮어쓰기), -i(입력), -ac 1(모노), -ar 16000(16kHz 샘플링)
        command = ["ffmpeg", "-y", "-i", src_path, "-ac", "1", "-ar", "16000", dst_path]
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,  # 성공 로그는 출력 안 함
            stderr=subprocess.PIPE,  # 에러 로그는 캡처
            check=True,  # 오류 발생 시 CalledProcessError 예외 발생
            timeout=30  # 30초 타임아웃 설정
        )

        # --- STT 문제 해결: 변환 결과 파일 존재 확인 ---
        if not os.path.exists(dst_path):
            raise FileNotFoundError(f"오디오 변환 결과 파일이 생성되지 않았습니다: {dst_path}")

        if os.path.getsize(dst_path) == 0:
            raise ValueError("변환된 오디오 파일이 비어있습니다.")
        # --- 수정 완료 ---

        with open(dst_path, "rb") as f:
            converted_bytes = f.read()

        # --- STT 문제 해결: 변환 결과 유효성 검사 ---
        if not converted_bytes or len(converted_bytes) == 0:
            raise ValueError("오디오 변환 결과가 비어있습니다.")
        # --- 수정 완료 ---

        return converted_bytes

    except FileNotFoundError:
        logger.error("ffmpeg를 찾을 수 없습니다. 시스템에 ffmpeg가 설치되어 있는지 확인해주세요.")
        raise
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else "알 수 없는 ffmpeg 오류"
        logger.error(f"ffmpeg 오디오 변환 실패: {error_msg}")
        raise
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg 변환 시간 초과")
        raise
    finally:
        # 임시 파일 삭제
        for file_path in [src_path, dst_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    logger.warning(f"임시 파일 삭제 실패: {file_path}, 오류: {e}")


# ✅ 텍스트 분석 API
@app.post("/receive-text/")
async def receive_text(request: Request):
    try:
        raw_body = await request.body()
        data = json.loads(raw_body.decode("utf-8"))
        user_input = data.get("text", "")
        print("📨 받은 텍스트:", user_input)

        # 1차 키워드 의포 파악
        keyword_purpose = get_purpose_by_keyword(user_input)
        print("🔍 키워드 매칭:", keyword_purpose)

        # 2차 LLM 의도 파악 요청
        system_prompt = ("너는 공공기관 키오스크 AI야. 사용자 목적만 예시처럼 "
                         "한 줄로 써줘. 예시 없는 건 '민원 목적을 알 수 없음'만 쓰면 된다.")
        if keyword_purpose:
            user_prompt = f"{LLM_PROMPT}\n[예상 목적: {keyword_purpose}]\n\"{user_input}\""
        else:
            user_prompt = f"{LLM_PROMPT}\n\"{user_input}\""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        summary = response.choices[0].message.content.strip()
        print("🧐 LLM 결과:", summary)

        return {
            "source": "llm",
            "summary": keyword_purpose,
            "purpose": keyword_purpose,
            "matched_keyword": keyword_purpose
        }

    except Exception as e:
        print("❌ OpenAI 오류:", e)
        return {
            "source": "error",
            "summary": "",
            "purpose": "분석 실패",
            "matched_keyword": None
        }


@app.post("/api/stt")
async def stt_once(file: UploadFile = File(...)):
    """
    프론트엔드에서 녹음된 오디오 파일(Blob)을 받아 텍스트로 변환하여 반환합니다.
    """
    try:
        # --- STT 문제 해결: 엔진 상태 체크 추가 ---
        if not _stt:
            logger.error("STT 엔진이 초기화되지 않았습니다.")
            return JSONResponse({"error": "STT 엔진이 준비되지 않았습니다."}, status_code=503)

        if not _stt.is_initialized():
            logger.error("STT 엔진이 초기화되지 않았습니다.")
            return JSONResponse({"error": "STT 엔진이 준비되지 않았습니다."}, status_code=503)
        # --- 수정 완료 ---

        # 업로드된 파일의 내용을 바이트로 읽음
        raw_bytes = await file.read()

        # --- STT 문제 해결: 파일 크기 체크 추가 ---
        if len(raw_bytes) == 0:
            logger.error("업로드된 오디오 파일이 비어있습니다.")
            return JSONResponse({"error": "오디오 파일이 비어있습니다."}, status_code=400)
        # --- 수정 완료 ---

        # 오디오를 STT API가 요구하는 16kHz/Mono WAV 형식으로 변환
        wav_bytes = _ensure_wav(raw_bytes, file.content_type)
        # STT 엔진으로 텍스트 변환 수행
        text = _stt.transcribe(wav_bytes)
        logger.info(f"STT 변환 결과: '{text}'")
        return JSONResponse({"text": text})

    except TranscriptionError as e:
        logger.error(f"STT 변환 오류: {e}")
        return JSONResponse({"error": str(e)}, status_code=502)
    except Exception as e:
        logger.error(f"STT 처리 중 알 수 없는 오류: {e}")
        return JSONResponse({"error": "알 수 없는 STT 오류가 발생했습니다."}, status_code=500)


# --- STT/TTS 통합: TTS API 엔드포인트 (수정) ---
@app.post("/api/tts")
async def tts_once(text: str = Form(...)):
    """
    프론트엔드에서 텍스트를 받아 음성 데이터(MP3)로 변환하여 반환합니다.
    """
    try:
        # 텍스트 유효성 검사
        if not text or not text.strip():
            return JSONResponse({"error": "TTS 변환을 위한 텍스트가 필요합니다."}, status_code=400)

        # --- TTS 문제 해결: 엔진 상태 체크 강화 ---
        if not _tts:
            logger.error("TTS 엔진이 초기화되지 않았습니다.")
            return JSONResponse({"error": "TTS 엔진이 준비되지 않았습니다."}, status_code=503)

        if not _tts.is_initialized():
            logger.error("TTS 엔진이 초기화되지 않았습니다.")
            return JSONResponse({"error": "TTS 엔진이 준비되지 않았습니다."}, status_code=503)
        # --- 수정 완료 ---

        # synthesize 메서드를 호출하여 음성 데이터를 바이트로 직접 받음
        audio_bytes = _tts.synthesize(text)

        # --- TTS 문제 해결: 오디오 바이트 유효성 검사 ---
        if not audio_bytes or len(audio_bytes) == 0:
            logger.error("TTS 변환 결과가 비어있습니다.")
            return JSONResponse({"error": "TTS 변환에 실패했습니다."}, status_code=502)
        # --- 수정 완료 ---

        # gTTS는 mp3를 생성하므로 media_type을 'audio/mpeg'로 설정
        # FastAPI의 Response 객체를 사용하여 바이트 데이터를 직접 전송
        logger.info(f"TTS 변환 완료: '{text}' ({len(audio_bytes)} bytes)")
        return Response(content=audio_bytes, media_type="audio/mpeg")

    except TTSError as e:
        logger.error(f"TTS 변환 오류: {e}")
        return JSONResponse({"error": str(e)}, status_code=502)
    except Exception as e:
        logger.error(f"TTS 처리 중 알 수 없는 오류: {e}")
        return JSONResponse({"error": "알 수 없는 TTS 오류가 발생했습니다."}, status_code=500)


# ======================================================================
# ================= 1. 웹소켓 (실시간 화면 구현) =================
# ======================================================================
@app.websocket("/ws/fingerprint")
async def websocket_fingerprint_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # 1. 프론트엔드로부터 첫 메시지(사용자 정보) 수신
        data = await websocket.receive_json()
        name = data.get("name")
        rrn = data.get("rrn")

        # 2. 사용자 정보 조회
        user_data = None
        data_fp_path = os.path.join(BACKEND_DIR, "Utility", "Fingerprint", "data_fp")
        plain_rrn_from_frontend = rrn.replace('-', '')

        for file_path in glob.glob(os.path.join(data_fp_path, "*.json")):
            with open(file_path, 'r', encoding='utf-8') as f:
                current_user = json.load(f)
                plain_rrn_from_db = current_user.get("rrn", "").replace('-', '')
                if current_user.get("name") == name and current_user.get("rrn", "").replace('-', '') ==  plain_rrn_from_frontend:
                    user_data = current_user
                    break
        
        if not user_data:
            await websocket.send_json({"status": "error", "message": "등록되지 않은 사용자입니다."})
            await websocket.close()
            return

        # 3. 지문 인증 5회 시도
        max_attempts = 5
        for attempt in range(max_attempts):
            # 프론트엔드에 지문 스캔 요청 메시지 전송
            attempts_left = max_attempts - attempt
            await websocket.send_json({
                "status": "AWAITING_FINGER",
                "message": f"센서에 손가락을 올려주세요. (남은 횟수: {attempts_left}회)",
                "attempts_left": attempts_left
            })

            # 1. 현재 활성화된 시리얼(ser) 객체를 가져옵니다.
            ser = get_sensor_connection()
            if not ser:
                logger.error("지문 센서 연결을 찾을 수 없습니다.")
                # 센서 연결 실패 처리 로직 추가 (예: 에러 메시지 전송 후 종료)
                await websocket.send_json({"status": "error", "message": "센서가 준비되지 않았습니다."})
                break

            # 2. 블로킹 함수인 verify_fingerprint를 비동기적으로 실행하여 서버 멈춤 방지
            #    위에서 수정한 verify_fingerprint 함수는 이제 {"success": True/False, ...} 형태의 딕셔너리를 반환합니다.
            result = await asyncio.to_thread(verify_fingerprint, ser)
            

            logger.info(f"지문 인증 시도 {attempt + 1}: 결과: {result}")

            if result.get("success"):
                await websocket.send_json({
                    "status": "pos_auth",
                    "message": "인증에 성공했습니다!",
                    "userName": user_data.get("name")
                })
                return # 성공 시 함수 종료

            # 실패 시 재시도 메시지 전송
            if attempt < max_attempts - 1:
                await websocket.send_json({
                    "status": "RETRY",
                    "message": "인증에 실패했습니다. 다시 시도해주세요.",
                    "attempts_left": attempts_left - 1
                })
            await asyncio.sleep(1) # 다음 시도 전 1초 대기

        # 4. 최종 실패
        await websocket.send_json({
            "status": "neg_auth",
            "message": "인증에 최종 실패했습니다. 초기 화면으로 돌아갑니다.",
            "attempts_left": 0
        })

    except WebSocketDisconnect:
        logger.info("클라이언트가 연결을 종료했습니다.")
    except Exception as e:
        logger.error(f"웹소켓 처리 중 오류 발생: {e}")
    finally:
        logger.info("웹소켓 연결이 닫혔습니다.")

