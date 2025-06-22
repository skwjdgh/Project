"""
뉴스 에이전트 시스템 - 파이썬 클래스 다이어그램
요구사항 명세서를 바탕으로 한 객체지향 설계
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
import asyncio


# ============================================================================
# 데이터 모델 (Data Models)
# ============================================================================

class DeviceType(Enum):
    """디바이스 타입 열거형"""
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    PC = "pc"


class NewsCategory(Enum):
    """뉴스 카테고리 열거형"""
    POLITICS = "정치"
    ECONOMY = "경제"
    SOCIETY = "사회"
    CULTURE = "문화"
    SPORTS = "스포츠"
    TECHNOLOGY = "과학기술"
    INTERNATIONAL = "국제"


@dataclass
class UserProfile:
    """사용자 프로파일 데이터 클래스"""
    profile_id: str
    interests: List[NewsCategory]
    preferences: Dict[str, float]  # 카테고리별 선호도 (0.0-1.0)
    created_at: datetime
    updated_at: datetime
    is_default: bool = False
    
    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        data = {
            'profile_id': self.profile_id,
            'interests': [cat.value for cat in self.interests],
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_default': self.is_default
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'UserProfile':
        """JSON 문자열에서 객체 생성"""
        data = json.loads(json_str)
        return cls(
            profile_id=data['profile_id'],
            interests=[NewsCategory(cat) for cat in data['interests']],
            preferences=data['preferences'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            is_default=data.get('is_default', False)
        )


@dataclass
class NewsData:
    """뉴스 데이터 클래스"""
    article_id: str
    title: str
    content: str
    category: NewsCategory
    source: str
    published_at: datetime
    url: str
    
    def __hash__(self):
        return hash(self.article_id)


@dataclass
class NewsSummary:
    """뉴스 요약 데이터 클래스"""
    summary_id: str
    original_news: List[NewsData]
    summary_text: str
    user_profile_id: str
    created_at: datetime
    expires_at: datetime
    verified: bool = False
    
    def is_valid(self) -> bool:
        """요약본 유효성 검사"""
        return datetime.now() < self.expires_at


# ============================================================================
# 외부 인터페이스 (External Interfaces)
# ============================================================================

class APIInterface(ABC):
    """외부 API 인터페이스 추상 클래스"""
    
    @abstractmethod
    async def call_api(self, params: Dict) -> Dict:
        """API 호출 메서드"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """API 가용성 검사"""
        pass


class NewsAPIInterface(APIInterface):
    """뉴스 API 인터페이스 (SRS_FUN_013)"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limit = 100  # 시간당 호출 제한
        
    async def call_api(self, params: Dict) -> Dict:
        """뉴스 API 호출"""
        # 실제 API 호출 로직
        pass
    
    def is_available(self) -> bool:
        """API 가용성 검사"""
        # 연결 상태 및 rate limit 검사
        return True
    
    async def fetch_latest_news(self, categories: List[NewsCategory]) -> List[NewsData]:
        """최신 뉴스 가져오기"""
        pass


class OpenAIInterface(APIInterface):
    """OpenAI API 인터페이스 (SRS_FUN_014)"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.token_limit = 4000
        
    async def call_api(self, params: Dict) -> Dict:
        """OpenAI API 호출"""
        pass
    
    def is_available(self) -> bool:
        """API 가용성 검사"""
        return True
    
    async def summarize_news(self, news_list: List[NewsData], 
                           user_profile: UserProfile) -> str:
        """뉴스 요약 생성"""
        pass
    
    async def verify_summary(self, summary: str, original_news: List[NewsData]) -> bool:
        """요약 검증 (재질의)"""
        pass


class CloudStorageInterface(APIInterface):
    """클라우드 스토리지 인터페이스 (SRS_INF_008)"""
    
    def __init__(self, storage_config: Dict):
        self.storage_config = storage_config
        
    async def call_api(self, params: Dict) -> Dict:
        """스토리지 API 호출"""
        pass
    
    def is_available(self) -> bool:
        """스토리지 가용성 검사"""
        return True
    
    async def save_profile(self, profile: UserProfile) -> bool:
        """사용자 프로파일 저장"""
        pass
    
    async def load_profile(self, profile_id: str) -> Optional[UserProfile]:
        """사용자 프로파일 로드"""
        pass


# ============================================================================
# 시스템 모듈 (System Module)
# ============================================================================

class CookieDataAnalyzer:
    """쿠키 데이터 분석기 (SRS_FUN_004)"""
    
    def __init__(self):
        self.min_categories = 3
        
    def analyze_cookie_data(self, cookie_data: Dict) -> Dict[NewsCategory, float]:
        """쿠키 데이터 분석하여 관심사 추출"""
        preferences = {}
        # 쿠키 데이터 분석 로직
        return preferences
    
    def extract_interests(self, preferences: Dict[NewsCategory, float]) -> List[NewsCategory]:
        """선호도에서 관심사 목록 추출"""
        return [cat for cat, score in preferences.items() if score > 0.5]


class ProfileManager:
    """사용자 프로파일 관리자"""
    
    def __init__(self, storage: CloudStorageInterface):
        self.storage = storage
        self.analyzer = CookieDataAnalyzer()
        
    async def check_profile_exists(self, user_id: str) -> bool:
        """프로파일 존재 여부 확인 (SRS_FUN_002)"""
        profile = await self.storage.load_profile(user_id)
        return profile is not None
    
    async def create_personalized_profile(self, user_id: str, 
                                        cookie_data: Dict) -> UserProfile:
        """개인화 프로파일 생성 (SRS_FUN_005)"""
        preferences = self.analyzer.analyze_cookie_data(cookie_data)
        interests = self.analyzer.extract_interests(preferences)
        
        profile = UserProfile(
            profile_id=user_id,
            interests=interests,
            preferences=preferences,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_default=False
        )
        
        await self.storage.save_profile(profile)
        return profile
    
    async def create_default_profile(self, user_id: str) -> UserProfile:
        """기본 프로파일 생성 (SRS_FUN_006)"""
        default_interests = [NewsCategory.POLITICS, NewsCategory.ECONOMY, NewsCategory.SOCIETY]
        default_preferences = {cat: 0.5 for cat in default_interests}
        
        profile = UserProfile(
            profile_id=user_id,
            interests=default_interests,
            preferences=default_preferences,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_default=True
        )
        
        await self.storage.save_profile(profile)
        return profile
    
    async def update_profile_if_needed(self, profile: UserProfile, 
                                     cookie_data: Dict) -> UserProfile:
        """프로파일 주기적 업데이트 (SRS_FUN_007)"""
        week_ago = datetime.now() - timedelta(weeks=1)
        
        if profile.updated_at < week_ago:
            # 새로운 쿠키 데이터로 업데이트
            new_preferences = self.analyzer.analyze_cookie_data(cookie_data)
            profile.preferences = new_preferences
            profile.interests = self.analyzer.extract_interests(new_preferences)
            profile.updated_at = datetime.now()
            
            await self.storage.save_profile(profile)
        
        return profile


class SystemModule:
    """시스템 모듈 메인 클래스"""
    
    def __init__(self, storage: CloudStorageInterface):
        self.profile_manager = ProfileManager(storage)
        self.storage = storage
        
    async def access_cookie_data(self, user_consent: bool) -> Optional[Dict]:
        """쿠키 데이터 접근 (SRS_FUN_004)"""
        if not user_consent:
            return None
        
        # 실제 쿠키 데이터 접근 로직
        cookie_data = {}  # 브라우저에서 쿠키 데이터 수집
        return cookie_data
    
    async def get_or_create_profile(self, user_id: str, 
                                  cookie_data: Optional[Dict]) -> UserProfile:
        """사용자 프로파일 가져오기 또는 생성"""
        profile = await self.storage.load_profile(user_id)
        
        if profile:
            if cookie_data:
                profile = await self.profile_manager.update_profile_if_needed(
                    profile, cookie_data)
        else:
            if cookie_data:
                profile = await self.profile_manager.create_personalized_profile(
                    user_id, cookie_data)
            else:
                profile = await self.profile_manager.create_default_profile(user_id)
        
        return profile


# ============================================================================
# 뉴스 데이터 분석 모듈 (News Analysis Module)
# ============================================================================

class NewsCrawler:
    """뉴스 크롤러 (SRS_FUN_009)"""
    
    def __init__(self, news_api: NewsAPIInterface):
        self.news_api = news_api
        self.min_sources = 3
        
    async def crawl_news_data(self, categories: List[NewsCategory]) -> List[NewsData]:
        """뉴스 데이터 크롤링"""
        if not self.news_api.is_available():
            raise Exception("News API is not available")
        
        return await self.news_api.fetch_latest_news(categories)


class NewsAnalyzer:
    """뉴스 분석기"""
    
    def __init__(self, openai_api: OpenAIInterface):
        self.openai_api = openai_api
        
    async def summarize_with_profile(self, news_list: List[NewsData], 
                                   user_profile: UserProfile) -> str:
        """사용자 프로파일 기반 뉴스 요약 (SRS_FUN_010)"""
        if not self.openai_api.is_available():
            raise Exception("OpenAI API is not available")
        
        return await self.openai_api.summarize_news(news_list, user_profile)
    
    async def verify_and_requery(self, summary: str, 
                               original_news: List[NewsData]) -> str:
        """AI 재질의 및 검증 (SRS_FUN_011)"""
        is_verified = await self.openai_api.verify_summary(summary, original_news)
        
        if not is_verified:
            # 재요약 수행
            return await self.openai_api.summarize_news(original_news, None)
        
        return summary


class SummaryCache:
    """요약 캐시 관리"""
    
    def __init__(self):
        self.cache: Dict[str, NewsSummary] = {}
        self.validity_hours = 3
        
    def get_valid_summary(self, user_profile_id: str) -> Optional[NewsSummary]:
        """유효한 요약 가져오기"""
        summary = self.cache.get(user_profile_id)
        if summary and summary.is_valid():
            return summary
        return None
    
    def save_summary(self, summary: NewsSummary):
        """요약 저장"""
        self.cache[summary.user_profile_id] = summary
    
    def invalidate_expired(self):
        """만료된 요약 제거"""
        expired_keys = [
            key for key, summary in self.cache.items() 
            if not summary.is_valid()
        ]
        for key in expired_keys:
            del self.cache[key]


class NewsAnalysisModule:
    """뉴스 데이터 분석 모듈 메인 클래스"""
    
    def __init__(self, news_api: NewsAPIInterface, openai_api: OpenAIInterface):
        self.crawler = NewsCrawler(news_api)
        self.analyzer = NewsAnalyzer(openai_api)
        self.cache = SummaryCache()
        
    async def call_external_api(self) -> bool:
        """외부 API 호출 (SRS_FUN_008)"""
        # API 가용성 검사
        return True
    
    async def generate_news_summary(self, user_profile: UserProfile) -> NewsSummary:
        """뉴스 요약 생성 (SRS_FUN_012 포함)"""
        # 캐시에서 유효한 요약 확인
        cached_summary = self.cache.get_valid_summary(user_profile.profile_id)
        if cached_summary:
            return cached_summary
        
        # 새로운 요약 생성
        news_data = await self.crawler.crawl_news_data(user_profile.interests)
        summary_text = await self.analyzer.summarize_with_profile(news_data, user_profile)
        verified_summary = await self.analyzer.verify_and_requery(summary_text, news_data)
        
        # 요약 객체 생성
        summary = NewsSummary(
            summary_id=f"{user_profile.profile_id}_{datetime.now().timestamp()}",
            original_news=news_data,
            summary_text=verified_summary,
            user_profile_id=user_profile.profile_id,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=3),
            verified=True
        )
        
        # 캐시에 저장
        self.cache.save_summary(summary)
        return summary


# ============================================================================
# 인터페이스 모듈 (Interface Module)
# ============================================================================

class DeviceRenderer(ABC):
    """디바이스별 렌더러 추상 클래스"""
    
    @abstractmethod
    def render(self, summary: NewsSummary) -> str:
        """요약 렌더링"""
        pass
    
    @abstractmethod
    def check_compatibility(self) -> bool:
        """호환성 검사"""
        pass


class SmartphoneRenderer(DeviceRenderer):
    """스마트폰 렌더러"""
    
    def render(self, summary: NewsSummary) -> str:
        """모바일 최적화 렌더링"""
        # 스마트폰용 UI 렌더링
        return f"<div class='mobile-news'>{summary.summary_text}</div>"
    
    def check_compatibility(self) -> bool:
        return True
    
    def show_widget(self, summary: NewsSummary) -> str:
        """위젯 표시"""
        return f"<widget>{summary.summary_text[:100]}...</widget>"


class TabletRenderer(DeviceRenderer):
    """태블릿 렌더러"""
    
    def render(self, summary: NewsSummary) -> str:
        """태블릿 최적화 렌더링"""
        return f"<div class='tablet-news'>{summary.summary_text}</div>"
    
    def check_compatibility(self) -> bool:
        return True
    
    def show_widget(self, summary: NewsSummary) -> str:
        """위젯 표시"""
        return f"<widget class='tablet'>{summary.summary_text[:200]}...</widget>"


class PCRenderer(DeviceRenderer):
    """PC 렌더러"""
    
    def render(self, summary: NewsSummary) -> str:
        """PC 최적화 렌더링"""
        return f"<div class='desktop-news'>{summary.summary_text}</div>"
    
    def check_compatibility(self) -> bool:
        return True


class InterfaceModule:
    """인터페이스 모듈 메인 클래스 (SRS_FUN_015)"""
    
    def __init__(self):
        self.renderers = {
            DeviceType.SMARTPHONE: SmartphoneRenderer(),
            DeviceType.TABLET: TabletRenderer(),
            DeviceType.PC: PCRenderer()
        }
    
    def detect_device_type(self, user_agent: str) -> DeviceType:
        """디바이스 타입 감지"""
        # User-Agent 분석하여 디바이스 타입 결정
        if "Mobile" in user_agent:
            return DeviceType.SMARTPHONE
        elif "Tablet" in user_agent:
            return DeviceType.TABLET
        else:
            return DeviceType.PC
    
    def render_for_device(self, summary: NewsSummary, device_type: DeviceType) -> str:
        """디바이스별 렌더링"""
        renderer = self.renderers[device_type]
        return renderer.render(summary)


# ============================================================================
# 메인 모듈 (Main Module)
# ============================================================================

class NewsAgentMain:
    """뉴스 에이전트 메인 모듈"""
    
    def __init__(self, 
                 news_api: NewsAPIInterface, 
                 openai_api: OpenAIInterface,
                 storage: CloudStorageInterface):
        self.system_module = SystemModule(storage)
        self.analysis_module = NewsAnalysisModule(news_api, openai_api)
        self.interface_module = InterfaceModule()
        
    async def start_application(self) -> bool:
        """애플리케이션 시작 (SRS_FUN_001)"""
        try:
            # 시스템 초기화
            await self._initialize_system()
            return True
        except Exception as e:
            print(f"Application start failed: {e}")
            return False
    
    async def _initialize_system(self):
        """시스템 초기화"""
        # 3초 이내 초기화 완료 (SRS_NFN_001)
        pass
    
    async def check_user_profile(self, user_id: str) -> bool:
        """사용자 프로파일 확인 (SRS_FUN_002)"""
        return await self.system_module.profile_manager.check_profile_exists(user_id)
    
    async def request_cookie_permission(self, user_id: str) -> bool:
        """쿠키 사용 권한 요청 (SRS_FUN_003)"""
        # 실제 구현에서는 웹 브라우저 API 사용
        # GDPR 및 개인정보보호법 준수
        consent = input(f"사용자 {user_id}님, 개인화 서비스를 위해 쿠키 사용에 동의하시겠습니까? (y/n): ")
        return consent.lower() == 'y'
    
    async def coordinate_system_module(self, user_id: str, 
                                     user_consent: bool) -> UserProfile:
        """시스템 모듈과 연동"""
        cookie_data = await self.system_module.access_cookie_data(user_consent)
        return await self.system_module.get_or_create_profile(user_id, cookie_data)
    
    async def coordinate_analysis_module(self, user_profile: UserProfile) -> NewsSummary:
        """뉴스 분석 모듈과 연동"""
        return await self.analysis_module.generate_news_summary(user_profile)
    
    async def generate_news_output(self, user_profile: UserProfile) -> NewsSummary:
        """요약된 뉴스 데이터 수신"""
        return await self.coordinate_analysis_module(user_profile)
    
    async def send_to_interface(self, summary: NewsSummary, 
                              user_agent: str) -> str:
        """인터페이스로 최종 출력 전달"""
        device_type = self.interface_module.detect_device_type(user_agent)
        return self.interface_module.render_for_device(summary, device_type)
    
    async def access_external_api(self) -> bool:
        """외부 API 접근 관리"""
        return await self.analysis_module.call_external_api()
    
    async def process_user_request(self, user_id: str, user_agent: str) -> str:
        """사용자 요청 전체 처리 플로우"""
        try:
            # 1. 애플리케이션 시작
            if not await self.start_application():
                return "시스템 초기화 실패"
            
            # 2. 사용자 프로파일 확인
            profile_exists = await self.check_user_profile(user_id)
            
            # 3. 쿠키 권한 요청 (프로파일이 없거나 업데이트가 필요한 경우)
            user_consent = False
            if not profile_exists:
                user_consent = await self.request_cookie_permission(user_id)
            
            # 4. 시스템 모듈 연동 (프로파일 생성/로드)
            user_profile = await self.coordinate_system_module(user_id, user_consent)
            
            # 5. 뉴스 분석 모듈 연동 (요약 생성)
            news_summary = await self.generate_news_output(user_profile)
            
            # 6. 인터페이스 모듈로 출력
            final_output = await self.send_to_interface(news_summary, user_agent)
            
            return final_output
            
        except Exception as e:
            return f"처리 중 오류 발생: {e}"


# ============================================================================
# 유틸리티 및 설정 클래스
# ============================================================================

class SystemConfig:
    """시스템 설정 클래스"""
    
    def __init__(self):
        self.performance_config = {
            'init_timeout': 3,  # 초기화 시간 제한 (초)
            'summary_timeout': 5,  # 요약 생성 시간 제한 (초)
            'api_timeout': 2,  # API 응답 시간 제한 (초)
        }
        
        self.quality_config = {
            'accuracy_threshold': 0.9,  # 90% 정확성 보장
            'availability_target': 0.99,  # 99% 가용성 목표
        }
        
        self.cache_config = {
            'summary_validity_hours': 3,  # 요약 유효 시간
            'max_cache_size': 1000,  # 최대 캐시 크기
        }
        
        self.browser_compatibility = [
            'Chrome 90+',
            'Firefox 88+',
            'Safari 14+'
        ]


class ErrorHandler:
    """에러 처리 클래스"""
    
    @staticmethod
    def handle_api_error(api_name: str, error: Exception) -> str:
        """API 오류 처리"""
        return f"{api_name} API 호출 실패: {str(error)}"
    
    @staticmethod
    def handle_network_error(error: Exception) -> str:
        """네트워크 오류 처리"""
        return f"네트워크 연결 오류: {str(error)}"
    
    @staticmethod
    def handle_data_error(error: Exception) -> str:
        """데이터 처리 오류"""
        return f"데이터 처리 오류: {str(error)}"


class Logger:
    """로깅 클래스 (SRS_NFN_007)"""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = log_level
        self.retention_days = 7
    
    def log_info(self, message: str):
        """정보 로그"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] INFO: {message}")
    
    def log_warning(self, message: str):
        """경고 로그"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] WARNING: {message}")
    
    def log_error(self, message: str):
        """오류 로그"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] ERROR: {message}")
    
    def log_user_action(self, user_id: str, action: str):
        """사용자 액션 로그"""
        timestamp = datetime.now().isoformat()
        # 개인정보 마스킹 처리
        masked_user_id = f"{user_id[:3]}***{user_id[-3:]}" if len(user_id) > 6 else "***"
        print(f"[{timestamp}] USER_ACTION: {masked_user_id} - {action}")


class PerformanceMonitor:
    """성능 모니터링 클래스 (SRS_NFN_008)"""
    
    def __init__(self):
        self.response_times = []
        self.error_counts = {}
        
    def record_response_time(self, operation: str, time_ms: int):
        """응답 시간 기록"""
        self.response_times.append({
            'operation': operation,
            'time_ms': time_ms,
            'timestamp': datetime.now()
        })
    
    def record_error(self, error_type: str):
        """오류 발생 기록"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def get_average_response_time(self, operation: str) -> float:
        """평균 응답 시간 조회"""
        operation_times = [
            record['time_ms'] for record in self.response_times 
            if record['operation'] == operation
        ]
        return sum(operation_times) / len(operation_times) if operation_times else 0.0
    
    def check_performance_targets(self) -> Dict[str, bool]:
        """성능 목표 달성 여부 확인"""
        return {
            'init_time_ok': self.get_average_response_time('init') <= 3000,
            'summary_time_ok': self.get_average_response_time('summary') <= 5000,
            'api_time_ok': self.get_average_response_time('api_call') <= 2000,
        }


# ============================================================================
# 팩토리 및 의존성 주입 클래스
# ============================================================================

class APIFactory:
    """API 인스턴스 팩토리"""
    
    @staticmethod
    def create_news_api(config: Dict) -> NewsAPIInterface:
        """뉴스 API 인스턴스 생성"""
        return NewsAPIInterface(
            api_key=config['news_api_key'],
            base_url=config['news_api_url']
        )
    
    @staticmethod
    def create_openai_api(config: Dict) -> OpenAIInterface:
        """OpenAI API 인스턴스 생성"""
        return OpenAIInterface(
            api_key=config['openai_api_key'],
            model=config.get('openai_model', 'gpt-4')
        )
    
    @staticmethod
    def create_storage_api(config: Dict) -> CloudStorageInterface:
        """클라우드 스토리지 API 인스턴스 생성"""
        return CloudStorageInterface(config['storage_config'])


class NewsAgentFactory:
    """뉴스 에이전트 팩토리"""
    
    @staticmethod
    def create_news_agent(config: Dict) -> NewsAgentMain:
        """뉴스 에이전트 메인 인스턴스 생성"""
        # API 인스턴스들 생성
        news_api = APIFactory.create_news_api(config)
        openai_api = APIFactory.create_openai_api(config)
        storage_api = APIFactory.create_storage_api(config)
        
        # 메인 모듈 생성 및 반환
        return NewsAgentMain(news_api, openai_api, storage_api)


# ============================================================================
# 사용 예시 및 테스트 코드
# ============================================================================

async def main():
    """메인 실행 함수 예시"""
    
    # 설정 정보
    config = {
        'news_api_key': 'your_news_api_key',
        'news_api_url': 'https://newsapi.org/v2',
        'openai_api_key': 'your_openai_api_key',
        'openai_model': 'gpt-4',
        'storage_config': {
            'type': 'aws_s3',
            'bucket': 'news-agent-profiles'
        }
    }
    
    # 뉴스 에이전트 생성
    news_agent = NewsAgentFactory.create_news_agent(config)
    
    # 사용자 요청 처리
    user_id = "user123"
    user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) Mobile"
    
    try:
        result = await news_agent.process_user_request(user_id, user_agent)
        print("뉴스 요약 결과:")
        print(result)
        
    except Exception as e:
        print(f"처리 중 오류: {e}")


if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main())


"""
=== 클래스 다이어그램 요약 ===

1. 데이터 모델 (Data Models)
   - UserProfile: 사용자 프로파일 정보
   - NewsData: 뉴스 데이터
   - NewsSummary: 뉴스 요약 정보

2. 외부 인터페이스 (External Interfaces)
   - APIInterface: 추상 API 인터페이스
   - NewsAPIInterface: 뉴스 API 연동
   - OpenAIInterface: OpenAI API 연동
   - CloudStorageInterface: 클라우드 스토리지 연동

3. 시스템 모듈 (System Module)
   - CookieDataAnalyzer: 쿠키 데이터 분석
   - ProfileManager: 사용자 프로파일 관리
   - SystemModule: 시스템 모듈 메인

4. 뉴스 분석 모듈 (News Analysis Module)
   - NewsCrawler: 뉴스 크롤링
   - NewsAnalyzer: 뉴스 분석 및 요약
   - SummaryCache: 요약 캐시 관리
   - NewsAnalysisModule: 분석 모듈 메인

5. 인터페이스 모듈 (Interface Module)
   - DeviceRenderer: 디바이스별 렌더러 추상 클래스
   - SmartphoneRenderer, TabletRenderer, PCRenderer: 디바이스별 구현
   - InterfaceModule: 인터페이스 모듈 메인

6. 메인 모듈 (Main Module)
   - NewsAgentMain: 전체 시스템 조정 및 제어

7. 유틸리티 클래스
   - SystemConfig: 시스템 설정
   - ErrorHandler: 오류 처리
   - Logger: 로깅
   - PerformanceMonitor: 성능 모니터링
   - APIFactory, NewsAgentFactory: 팩토리 패턴

이 설계는 SOLID 원칙을 따르며, 각 모듈의 책임이 명확히 분리되어 있고,
확장성과 유지보수성을 고려한 구조입니다.
"""