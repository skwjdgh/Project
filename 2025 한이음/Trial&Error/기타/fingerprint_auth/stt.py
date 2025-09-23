# #################################################
#   음성-텍스트 변환 모듈 (ETRI API)
# #################################################

import os
import base64
import json
import requests
from loguru import logger
from typing import Dict, Any

from .interface import ISTT
from .exceptions import TranscriptionError

class SpeechToText(ISTT):
    """ETRI 음성 인식 API를 사용하여 음성을 텍스트로 변환하는 클래스"""

    # ####################################
    #   STT 객체 초기화
    # ####################################
    def __init__(self, config: Dict[str, Any]) -> None:
        """API 키와 설정을 초기화합니다."""
        # .env 파일에서 ETRI API 키를 불러옵니다.
        self.api_key = os.getenv("ETRI_API_KEY")
        if not self.api_key:
            raise ValueError("환경 변수 ETRI_API_KEY가 설정되지 않았습니다.")
        
        # config.yaml 파일에서 API URL과 언어 코드를 불러옵니다.
        self.api_url = config['api_url']
        self.language_code = config['language_code']
        self._is_initialized = False
        logger.info("ETRI STT 모듈이 생성되었습니다.")

    # ####################################
    #   모듈 초기화
    # ####################################
    def initialize(self) -> None:
        """API 방식이므로 별도 모델 로딩은 필요 없으며, 상태만 변경합니다."""
        logger.info("ETRI STT는 별도 모델 로딩이 필요 없습니다. 초기화 완료로 간주합니다.")
        self._is_initialized = True

    # ####################################
    #   초기화 상태 확인
    # ####################################
    def is_initialized(self) -> bool:
        """모듈이 초기화되었는지 여부를 반환합니다."""
        return self._is_initialized

    # ####################################
    #   음성 -> 텍스트 변환
    # ####################################
    def transcribe(self, audio_bytes: bytes) -> str:
        """오디오 바이트를 받아 ETRI API로 전송하고, 변환된 텍스트를 반환합니다."""
        if not self.is_initialized():
            raise RuntimeError("STT 모듈이 초기화되지 않았습니다.")

        try:
            # 1. 오디오 데이터를 Base64로 인코딩합니다.
            audio_base64 = base64.b64encode(audio_bytes).decode("utf8")
            
            # 2. API 문서에 맞게 헤더 및 Body 구성
            request_headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "Authorization": self.api_key
            }
            request_data = {
                "argument": {
                    "language_code": self.language_code,
                    "audio": audio_base64
                }
            }

            logger.info("ETRI 음성 인식 API에 요청을 전송합니다...")
            
            # 3. API를 호출합니다.
            response = requests.post(
                self.api_url,
                headers=request_headers,
                data=json.dumps(request_data),
                timeout=20.0
            )
            response.raise_for_status()  # 200 OK 응답이 아닐 경우 예외를 발생시킵니다.

            # 4. 응답 본문을 JSON으로 파싱하고 텍스트를 추출합니다.
            response_data = response.json()
            recognized_text = response_data.get("return_object", {}).get("recognized", "")
            
            if not recognized_text:
                logger.warning(f"API가 음성을 인식하지 못했거나, 응답이 비어있습니다. 응답: {response_data}")
                return ""
                
            logger.info(f"ETRI API 변환 완료 -> '{recognized_text}'")
            return recognized_text

        except requests.exceptions.RequestException as e:
            logger.error(f"ETRI API 요청 실패: {e}", exc_info=True)
            raise TranscriptionError("음성 인식 API 서버와 통신하는 데 실패했습니다.") from e
        except Exception as e:
            logger.error(f"STT 변환 중 예상치 못한 오류 발생: {e}", exc_info=True)
            raise TranscriptionError("음성 변환에 실패했습니다.") from e

    # ####################################
    #   리소스 정리
    # ####################################
    def close(self) -> None:
        """API 방식이므로 별도의 리소스 정리 작업은 필요 없습니다."""
        logger.info("ETRI STT 모듈 리소스 정리가 완료되었습니다.")
        pass