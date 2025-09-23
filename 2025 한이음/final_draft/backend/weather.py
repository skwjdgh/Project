# -*- coding: utf-8 -*-
import os
import json
import httpx
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

# ✅ .env 로드 (환경변수 import 시점 문제 방지)
from dotenv import load_dotenv
load_dotenv()

# ✅ OpenAI SDK (>=1.x)
from openai import OpenAI
from openai import APIConnectionError, APIStatusError, AuthenticationError, RateLimitError

router = APIRouter()

class WeatherRequest(BaseModel):
    city: str

# ---- Config ----
OWM_TIMEOUT = 10  # seconds
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# ---- Lazy OpenAI Client ----
_openai_client: Optional[OpenAI] = None
def get_openai_client() -> Optional[OpenAI]:
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    _openai_client = OpenAI(api_key=api_key)
    return _openai_client

def _extract_openai_text(resp) -> str:
    """
    OpenAI responses.create 응답에서 텍스트 안전 추출
    - 일부 버전은 resp.output_text가 속성, 일부는 메서드일 수 있음 → 모두 커버
    - 실패 시 output/content 구조로 폴백
    """
    if hasattr(resp, "output_text"):
        ot = getattr(resp, "output_text")
        try:
            return (ot() if callable(ot) else ot) or ""
        except Exception:
            pass
    try:
        parts = []
        for item in getattr(resp, "output", []) or []:
            for c in getattr(item, "content", []) or []:
                t = getattr(c, "text", None)
                if t:
                    parts.append(t)
        if parts:
            return "\n".join(parts)
    except Exception:
        pass
    try:
        return resp.choices[0].message.content or ""
    except Exception:
        return ""

def summarize_weather_2lines(city: str, weather_json: Dict[str, Any]) -> Optional[str]:
    """
    OpenAI로 한국어 '정확히 2줄' 요약 생성 (실패/키없음 시 None)
    """
    client = get_openai_client()
    if not client:
        return None

    prompt = f"""
다음 OpenWeather 날씨 JSON을 참고해 한국어로 '정확히 2줄' 요약을 작성해줘.
1줄: 현재/체감, 강수/바람 등 핵심 상황 (60자 내외)
2줄: 외출 준비물/주의사항 (60자 내외)
불필요한 서두/결론/이모지/문장번호/따옴표 없이, 두 줄만 출력.

사람에게 말해주듯이 존댓말 써줘야함

도시: {city}
JSON:
{json.dumps(weather_json, ensure_ascii=False)}
""".strip()

    try:
        resp = client.responses.create(model=OPENAI_MODEL, input=prompt)
        text = _extract_openai_text(resp).strip()

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if len(lines) >= 2:
            return "\n".join(lines[:2])
        if len(lines) == 1:
            return lines[0] + "\n우산/겉옷 등 기본 준비물 점검하세요."
        return None
    except (APIConnectionError, APIStatusError, AuthenticationError, RateLimitError) as e:
        print(f"⚠️ OpenAI 요약 실패: {type(e).__name__}: {e}")
        return None
    except Exception as e:
        print(f"⚠️ OpenAI 요약 처리 예외: {e}")
        return None

@router.post("/weather/")
async def get_weather(request: Request):
    """
    프론트엔드에서 도시 이름을 받아 OpenWeatherMap API로 날씨 정보를 조회하고,
    OpenAI로 '정확히 2줄' 요약을 생성해 weather_data['_meta']['ai_summary_ko']에 넣어 반환합니다.
    """
    try:
        data = await request.json()
        city = data.get("city", "Seoul")  # 기본값은 서울
        api_key = os.getenv("OPENWEATHER_API_KEY")

        if not api_key:
            return {"error": "Weather API key is not configured"}, 500

        # OpenWeatherMap API URL (units=metric: 섭씨, lang=kr: 한국어)
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=kr"

        async with httpx.AsyncClient(timeout=OWM_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()  # 200 OK가 아니면 에러 발생

        weather_data = response.json()
        print(f"✅ 날씨 정보 조회 성공: {city}")

        # ✅ OpenAI 2줄 요약 생성 후 weather_data에 합치기
        ai_summary = summarize_weather_2lines(city, weather_data)
        if ai_summary:
            meta = weather_data.get("_meta") or {}
            meta["ai_summary_ko"] = ai_summary
            weather_data["_meta"] = meta

        return weather_data


    except httpx.HTTPStatusError as e:
        print(f"❌ 날씨 API 오류: {e.response.status_code}")
        try:
            details = e.response.json()
        except Exception:
            details = {"text": e.response.text}
        return {"error": "Failed to fetch weather data", "details": details}, e.response.status_code
    except Exception as e:
        print(f"❌ 서버 내부 오류: {e}")
        return {"error": "An internal server error occurred", "details": str(e)}, 500
