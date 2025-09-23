import re
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class JuminRequest(BaseModel):
    jumin: str  # 사용자 입력 주민등록번호 (13자리)


class VerifyResponse(BaseModel):
    success: bool
    name: str | None = None
    error: str | None = None


@router.post("/recognition/", response_model=VerifyResponse)
async def verify_jumin(request: JuminRequest):
    """
    - request.jumin: 순수 13자리 숫자 문자열
    - fake_user_lookup에서 조회
    - 매칭되면 success=True + name, 아니면 success=False + error
    """
    jumin = request.jumin

    # 1) 형식 검증: 13자리 숫자
    if not re.fullmatch(r"\d{13}", jumin):
        return VerifyResponse(
            success=False,
            error="잘못된 형식입니다. 13자리 숫자(YYMMDDXXXXXXX)만 입력해주세요."
        )

    # 2) 사용자 조회 (더미 함수)
    user = fake_user_lookup(jumin)
    if not user:
        return VerifyResponse(
            success=False,
            error="등록된 사용자가 아닙니다."
        )

    # 3) 통과 시 이름 포함 반환
    return VerifyResponse(
        success=True,
        name=user["name"]
    )


def fake_user_lookup(jumin: str) -> dict | None:
    """
    데모용 더미 조회 함수. 실제 DB 로직으로 교체하세요.
    """
    fake_db = {
        "9011111111111": {"name": "홍길동"},
        "8505051222222": {"name": "김상철"},
        "9701012345678": {"name": "이영희"},
    }
    return fake_db.get(jumin)
