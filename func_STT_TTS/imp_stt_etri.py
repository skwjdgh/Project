import os
import base64
import json
import requests
from loguru import logger
from typing import Dict, Any

from .def_interface import ISTT
from .def_exceptions import TranscriptionError

class SpeechToText(ISTT):
    """ETRI 음성 인식 API를 사용하여 오디오를 텍스트로 변환하는 클래스."""
    def __init__(self, config: Dict[str, Any]) -> None:
        # .env 파일에서 ETRI API 키를 불러옵니다.
        self.api_key = os.getenv("ETRI_API_KEY")
        if not self.api_key:
            raise ValueError("환경 변수 ETRI_API_KEY가 설정되지 않았습니다.")
        
        # config.yaml 파일에서 API URL과 언어 코드 설정을 가져옵니다.
        self.api_url = config['api_url']
        self.language_code = config['language_code']
        self._is_initialized = False

    def initialize(self) -> None:
        """특별히 로드할 모델이 없으므로, 초기화 상태 플래그만 설정합니다."""
        self._is_initialized = True

    def is_initialized(self) -> bool:
        """초기화 여부를 반환합니다."""
        return self._is_initialized

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        오디오 데이터를 ETRI API 서버로 전송하고, 인식된 텍스트를 받아옵니다.
        """
        if not self.is_initialized():
            raise RuntimeError("STT 모듈이 초기화되지 않았습니다.")
        try:
            # 오디오 데이터를 Base64로 인코딩하여 JSON에 포함시킬 수 있도록 합니다.
            audio_base64 = base64.b64encode(audio_bytes).decode("utf8")
            
            # API 요청을 위한 헤더와 본문을 구성합니다.
            request_headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "Authorization": self.api_key
            }
            request_data = {
                "argument": { "language_code": self.language_code, "audio": audio_base64 }
            }

            # 구성된 정보를 바탕으로 ETRI 서버에 POST 요청을 보냅니다.
            response = requests.post(
                self.api_url, headers=request_headers, data=json.dumps(request_data), timeout=20.0
            )
            # HTTP 상태 코드가 200(성공)이 아니면 예외를 발생시킵니다.
            response.raise_for_status()
            
            # 응답받은 JSON 데이터에서 인식된 텍스트를 추출합니다.
            response_data = response.json()
            recognized_text = response_data.get("return_object", {}).get("recognized", "")
            
            if not recognized_text:
                logger.warning(f"API가 음성을 인식하지 못했습니다. 응답: {response_data}")
                return ""
            
            logger.info(f"ETRI API 변환 완료 -> '{recognized_text}'")
            return recognized_text
        except requests.exceptions.RequestException as e:
            # 네트워크 관련 오류 발생 시
            raise TranscriptionError("API 서버와 통신하는 데 실패했습니다.") from e
        except Exception as e:
            # 기타 모든 오류 발생 시
            raise TranscriptionError("음성 변환에 실패했습니다.") from e

    def close(self) -> None:
        """API 방식이므로 특별히 해제할 리소스가 없습니다."""
        pass