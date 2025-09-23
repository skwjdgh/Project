# Backend/Utility/STT_TTS/imp_stt_openai.py
import os, io, re
from typing import Dict, Any, List
from openai import OpenAI
from loguru import logger

from .def_interface import ISTT
from .def_exceptions import TranscriptionError


class SpeechToText(ISTT):
    _LANG_MAP = {
        "korean": "ko", "ko-kr": "ko", "kr": "ko", "kor": "ko", "korea": "ko",
        "english": "en", "en-us": "en", "en-gb": "en",
    }

    @staticmethod
    def _normalize_lang(lang: str | None, default: str = "ko") -> str:
        if not lang: return default
        l = SpeechToText._LANG_MAP.get(lang.strip().lower(), lang.strip().lower())
        return l if re.fullmatch(r"[a-z]{2}", l) else default

    def __init__(self, config: Dict[str, Any]) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("환경 변수 OPENAI_API_KEY가 설정되지 않았습니다.")
        self.client = OpenAI(api_key=api_key)

        self.model = config.get("model", "whisper-1")
        self.language = self._normalize_lang(config.get("language_code", "ko"), "ko")

        # ✅ 도메인 키워드(가중치 대용) - 필요시 config로 외부 주입
        self.domain_terms: List[str] = config.get("domain_terms", [
            "주민등록등본", "주민등록초본", "가족관계증명서", "건강보험자격득실확인서",
            "주민등록번호", "서울시", "날씨", "예보", "인쇄", "키오스크"
        ])
        # ✅ 자주 틀리는 표현 후처리 사전
        self.corrections: Dict[str, str] = {
            # ===== 등본 관련 =====
            "등군": "등본",
            "등뽄": "등본",
            "등번": "등본",
            "등본서": "등본",
            "등본 좀": "등본",

            # ===== 초본 관련 =====
            "초뽄": "초본",
            "초번": "초본",
            "촌번": "초본",
            "초본서": "초본",
            "초본 좀": "초본",

            # ===== 가족관계증명서 =====
            "가족 관계 증명서": "가족관계증명서",
            "가족증명서": "가족관계증명서",
            "가족관계 증명": "가족관계증명서",
            "가족관계서": "가족관계증명서",
            "가족 증명": "가족관계증명서",

            # ===== 건강보험자격득실확인서 =====
            "건강 보험 자격 득실 확인서": "건강보험자격득실확인서",
            "건강보험 자격 확인서": "건강보험자격득실확인서",
            "건강보험 득실 확인서": "건강보험자격득실확인서",
            "건강보험 확인서": "건강보험자격득실확인서",
            "자격득실 확인서": "건강보험자격득실확인서",

            # ===== 인쇄 관련 =====
            "인쇄 해줘": "인쇄해줘",
            "출력 해줘": "인쇄해줘",
            "프린트 해줘": "인쇄해줘",

            # ===== 날씨 관련 (광범위) =====
            "날씨 알려 줘": "날씨",
            "날씨 좀": "날씨",
            "오늘 날씨": "날씨",
            "지금 날씨": "날씨",
            "주간 날씨": "날씨",
            "주말 날씨": "날씨",
            "내일 날씨": "날씨",
            "모레 날씨": "날씨",
            "일기 예보": "날씨",
            "주간 예보": "날씨",
            "날씨 예보": "날씨",

            # 자연어형 질문들
            "오늘 덥다": "날씨",
            "오늘 더워": "날씨",
            "더워?": "날씨",
            "추워?": "날씨",
            "오늘 추워": "날씨",
            "춥다": "날씨",
            "더운지": "날씨",
            "추운지": "날씨",

            "비 와": "날씨",
            "비와": "날씨",
            "비 올까": "날씨",
            "오늘 비": "날씨",
            "비 예보": "날씨",
            "눈 와": "날씨",
            "눈와": "날씨",
            "눈 올까": "날씨",

            # 기온 질문
            "기온": "날씨",
            "온도": "날씨",
            "몇 도야": "날씨",
            "몇도야": "날씨",
            "지금 몇도": "날씨",
            "오늘 몇도": "날씨",
        }

        self._is_initialized = False

    def initialize(self) -> None:
        self._is_initialized = True
        logger.info(f"OpenAI STT 초기화 (model={self.model}, language={self.language})")

    def is_initialized(self) -> bool:
        return self._is_initialized

    def _build_prompt(self) -> str:
        # Whisper의 prompt는 '이런 단어가 나온다' 힌트 정도로 작동
        terms = ", ".join(self.domain_terms)
        return f"다음 한국어 키오스크 도메인 용어가 자주 등장합니다: {terms}"

    def _post_correction(self, text: str) -> str:
        out = text
        # 단순 치환 (띄어쓰기/대소문자 관대하게)
        for wrong, right in self.corrections.items():
            out = re.sub(re.escape(wrong), right, out, flags=re.IGNORECASE)
        # 불필요한 공백 정리
        out = re.sub(r"\s+", " ", out).strip()
        return out

    def transcribe(self, audio_bytes: bytes) -> str:
        if not self.is_initialized():
            raise RuntimeError("STT 모듈이 초기화되지 않았습니다.")

        lang = self._normalize_lang(self.language, default="ko")

        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            logger.info(f"STT 시작... (model={self.model}, lang={lang})")

            # ✅ 1차 시도: 언어 고정 + 온도 0 + 도메인 프롬프트
            prompt = self._build_prompt()
            transcript = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=lang,
                temperature=0,  # 가변성 최소화
                prompt=prompt  # 도메인 힌트
            )
            recognized_text = getattr(transcript, "text", None) or ""
            recognized_text = recognized_text.strip()

            # ✅ 너무 짧거나 빈 값이면 보강 재시도 (프롬프트만 변경/삭제 등)
            if len(recognized_text) < 2:
                logger.warning("1차 인식 결과가 너무 짧습니다. 보강 재시도를 수행합니다.")
                audio_file.seek(0)
                transcript2 = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=lang,
                    temperature=0,
                    # prompt 제거하여 모델이 자유롭게 해석하게
                )
                recognized_text = getattr(transcript2, "text", None) or ""
                recognized_text = recognized_text.strip()

            if not recognized_text:
                logger.warning("STT 응답에 text가 없습니다. (무음/잡음 가능)")
                return ""

            # ✅ 사전 치환 후 반환
            corrected = self._post_correction(recognized_text)
            logger.info(f"STT 완료 → '{recognized_text}'  => 보정 → '{corrected}'")
            return corrected

        except Exception as e:
            msg = str(e)
            if ("invalid_language_format" in msg) or ("Invalid language" in msg) or ("ISO-639-1" in msg):
                logger.error("언어 파라미터는 ISO-639-1 2글자 코드여야 합니다. 예: 'ko', 'en'")
            else:
                logger.error(f"OpenAI STT 오류: {msg}")
            raise TranscriptionError("OpenAI 음성 변환에 실패했습니다.") from e

    def close(self) -> None:
        pass
