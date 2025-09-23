# main.py - FastAPI 메인 애플리케이션
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime, timedelta
import logging

# 의존성 주입을 위한 인터페이스와 구현체들
from abc import ABC, abstractmethod

# =============================================================================
# SOLID 원칙을 적용한 인터페이스 정의 (의존성 역전 원칙 - DIP)
# =============================================================================

class IUserProfileRepository(ABC):
    """사용자 프로파일 저장소 인터페이스"""
    @abstractmethod
    def save_profile(self, profile_data: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def load_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def profile_exists(self, user_id: str) -> bool:
        pass

class INewsDataProvider(ABC):
    """뉴스 데이터 제공자 인터페이스"""
    @abstractmethod
    def fetch_news(self, category: str = "general") -> List[Dict[str, Any]]:
        pass

class IAISummarizer(ABC):
    """AI 요약 서비스 인터페이스"""
    @abstractmethod
    def summarize_news(self, news_content: str, user_interests: List[str]) -> str:
        pass
    
    @abstractmethod
    def validate_summary(self, original_content: str, summary: str) -> str:
        pass

class ICookieAnalyzer(ABC):
    """쿠키 분석 서비스 인터페이스"""
    @abstractmethod
    def analyze_cookies(self, cookie_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

# =============================================================================
# 구체적인 구현체들 (단일 책임 원칙 - SRP)
# =============================================================================

class FileUserProfileRepository(IUserProfileRepository):
    """파일 기반 사용자 프로파일 저장소"""
    
    def __init__(self, storage_path: str = "./profiles"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def save_profile(self, profile_data: Dict[str, Any]) -> bool:
        try:
            user_id = profile_data.get('user_id', 'default')
            file_path = os.path.join(self.storage_path, f"{user_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.error(f"Profile save error: {e}")
            return False
    
    def load_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            file_path = os.path.join(self.storage_path, f"{user_id}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logging.error(f"Profile load error: {e}")
            return None
    
    def profile_exists(self, user_id: str) -> bool:
        file_path = os.path.join(self.storage_path, f"{user_id}.json")
        return os.path.exists(file_path)

class MockNewsDataProvider(INewsDataProvider):
    """모의 뉴스 데이터 제공자 (실제 환경에서는 NewsAPI 등을 사용)"""
    
    def fetch_news(self, category: str = "general") -> List[Dict[str, Any]]:
        # 실제 환경에서는 NewsAPI.org 또는 RSS 크롤링을 사용
        mock_news = [
            {
                "title": "AI 기술의 최신 동향",
                "content": "인공지능 기술이 빠르게 발전하면서 다양한 분야에서 활용되고 있습니다. 특히 자연어 처리와 컴퓨터 비전 분야에서 놀라운 성과를 보이고 있으며...",
                "category": "기술",
                "published_at": datetime.now().isoformat(),
                "source": "테크뉴스"
            },
            {
                "title": "경제 시장 전망",
                "content": "올해 경제 전망에 대한 전문가들의 의견이 분분합니다. 인플레이션 압력과 금리 정책이 주요 변수로 작용할 것으로 보입니다...",
                "category": "경제",
                "published_at": datetime.now().isoformat(),
                "source": "경제신문"
            },
            {
                "title": "스포츠 하이라이트",
                "content": "어제 열린 중요한 경기에서 놀라운 결과가 나왔습니다. 선수들의 뛰어난 플레이와 팀워크가 돋보였으며...",
                "category": "스포츠",
                "published_at": datetime.now().isoformat(),
                "source": "스포츠뉴스"
            }
        ]
        return mock_news

class MockAISummarizer(IAISummarizer):
    """모의 AI 요약 서비스 (실제 환경에서는 OpenAI API 사용)"""
    
    def summarize_news(self, news_content: str, user_interests: List[str]) -> str:
        # 실제 환경에서는 LangChain + OpenAI API 사용
        interests_str = ", ".join(user_interests)
        
        # 간단한 키워드 기반 요약 시뮬레이션
        if any(interest in news_content.lower() for interest in user_interests):
            return f"[개인화 요약] 당신의 관심사({interests_str})와 관련된 중요한 뉴스입니다. " + news_content[:200] + "..."
        else:
            return f"[일반 요약] " + news_content[:150] + "..."
    
    def validate_summary(self, original_content: str, summary: str) -> str:
        # 실제 환경에서는 AI 재질의 로직 구현
        if len(summary) > len(original_content) * 0.8:
            return summary[:int(len(original_content) * 0.5)] + "... [검증 후 축약됨]"
        return summary + " [AI 검증 완료]"

class CookieAnalyzer(ICookieAnalyzer):
    """쿠키 분석 서비스"""
    
    def analyze_cookies(self, cookie_data: Dict[str, Any]) -> Dict[str, Any]:
        interests = []
        
        # 쿠키 데이터에서 관심사 추출 로직
        if 'visited_categories' in cookie_data:
            interests.extend(cookie_data['visited_categories'])
        
        if 'search_history' in cookie_data:
            # 검색 기록에서 키워드 추출
            for search in cookie_data['search_history']:
                if '기술' in search or 'AI' in search:
                    interests.append('기술')
                elif '경제' in search or '주식' in search:
                    interests.append('경제')
                elif '스포츠' in search:
                    interests.append('스포츠')
        
        # 중복 제거
        interests = list(set(interests))
        
        return {
            'interests': interests if interests else ['일반'],
            'preference_score': len(interests) * 0.1,
            'analyzed_at': datetime.now().isoformat()
        }

# =============================================================================
# 서비스 계층 (단일 책임 원칙 + 개방-폐쇄 원칙)
# =============================================================================

class UserProfileService:
    """사용자 프로파일 관리 서비스"""
    
    def __init__(self, 
                 repository: IUserProfileRepository,
                 cookie_analyzer: ICookieAnalyzer):
        self.repository = repository
        self.cookie_analyzer = cookie_analyzer
    
    def create_profile_from_cookies(self, user_id: str, cookie_data: Dict[str, Any]) -> Dict[str, Any]:
        """쿠키 데이터로부터 사용자 프로파일 생성"""
        analyzed_data = self.cookie_analyzer.analyze_cookies(cookie_data)
        
        profile = {
            'user_id': user_id,
            'interests': analyzed_data['interests'],
            'preference_score': analyzed_data['preference_score'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'profile_type': 'personalized'
        }
        
        self.repository.save_profile(profile)
        return profile
    
    def create_default_profile(self, user_id: str) -> Dict[str, Any]:
        """기본 프로파일 생성"""
        profile = {
            'user_id': user_id,
            'interests': ['일반', '사회', '경제'],
            'preference_score': 0.0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'profile_type': 'default'
        }
        
        self.repository.save_profile(profile)
        return profile
    
    def get_or_create_profile(self, user_id: str, cookie_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """프로파일 조회 또는 생성"""
        existing_profile = self.repository.load_profile(user_id)
        
        if existing_profile:
            # 1주일이 지났는지 확인 (업데이트 로직)
            updated_at = datetime.fromisoformat(existing_profile['updated_at'])
            if datetime.now() - updated_at > timedelta(days=7):
                if cookie_data:
                    return self.create_profile_from_cookies(user_id, cookie_data)
            return existing_profile
        
        # 새 프로파일 생성
        if cookie_data:
            return self.create_profile_from_cookies(user_id, cookie_data)
        else:
            return self.create_default_profile(user_id)

class NewsService:
    """뉴스 관리 서비스"""
    
    def __init__(self, 
                 news_provider: INewsDataProvider,
                 ai_summarizer: IAISummarizer):
        self.news_provider = news_provider
        self.ai_summarizer = ai_summarizer
        self.summary_cache = {}  # 간단한 캐시 (실제 환경에서는 Redis 등 사용)
    
    def get_personalized_news_summary(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """개인화된 뉴스 요약 생성"""
        cache_key = f"{user_profile['user_id']}_{datetime.now().strftime('%Y%m%d_%H')}"
        
        # 3시간 캐시 확인
        if cache_key in self.summary_cache:
            cached_time = self.summary_cache[cache_key]['created_at']
            if datetime.now() - datetime.fromisoformat(cached_time) < timedelta(hours=3):
                return self.summary_cache[cache_key]['summaries']
        
        # 새로운 요약 생성
        news_data = self.news_provider.fetch_news()
        user_interests = user_profile.get('interests', ['일반'])
        
        summaries = []
        for news_item in news_data:
            # AI 요약 생성
            summary = self.ai_summarizer.summarize_news(
                news_item['content'], 
                user_interests
            )
            
            # AI 재질의 및 검증
            validated_summary = self.ai_summarizer.validate_summary(
                news_item['content'],
                summary
            )
            
            summaries.append({
                'title': news_item['title'],
                'summary': validated_summary,
                'category': news_item['category'],
                'source': news_item['source'],
                'published_at': news_item['published_at'],
                'relevance_score': self._calculate_relevance(news_item, user_interests)
            })
        
        # 관련성 점수로 정렬
        summaries.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # 캐시 저장
        self.summary_cache[cache_key] = {
            'summaries': summaries[:5],  # 상위 5개만
            'created_at': datetime.now().isoformat()
        }
        
        return summaries[:5]
    
    def _calculate_relevance(self, news_item: Dict[str, Any], user_interests: List[str]) -> float:
        """뉴스와 사용자 관심사의 관련성 점수 계산"""
        score = 0.0
        content = (news_item.get('title', '') + ' ' + news_item.get('content', '')).lower()
        
        for interest in user_interests:
            if interest.lower() in content:
                score += 1.0
        
        # 카테고리 매칭 보너스
        if news_item.get('category', '').lower() in [i.lower() for i in user_interests]:
            score += 2.0
        
        return score

# =============================================================================
# Pydantic 모델들 (데이터 검증)
# =============================================================================

class CookieConsentRequest(BaseModel):
    user_id: str
    consent_given: bool
    cookie_data: Optional[Dict[str, Any]] = None

class NewsRequest(BaseModel):
    user_id: str

class NewsSummaryResponse(BaseModel):
    title: str
    summary: str
    category: str
    source: str
    published_at: str
    relevance_score: float

# =============================================================================
# 의존성 주입 설정 (의존성 역전 원칙)
# =============================================================================

def get_user_profile_repository() -> IUserProfileRepository:
    return FileUserProfileRepository()

def get_news_provider() -> INewsDataProvider:
    return MockNewsDataProvider()

def get_ai_summarizer() -> IAISummarizer:
    return MockAISummarizer()

def get_cookie_analyzer() -> ICookieAnalyzer:
    return CookieAnalyzer()

def get_user_profile_service(
    repository: IUserProfileRepository = Depends(get_user_profile_repository),
    cookie_analyzer: ICookieAnalyzer = Depends(get_cookie_analyzer)
) -> UserProfileService:
    return UserProfileService(repository, cookie_analyzer)

def get_news_service(
    news_provider: INewsDataProvider = Depends(get_news_provider),
    ai_summarizer: IAISummarizer = Depends(get_ai_summarizer)
) -> NewsService:
    return NewsService(news_provider, ai_summarizer)

# =============================================================================
# FastAPI 애플리케이션 및 엔드포인트
# =============================================================================

app = FastAPI(
    title="개인화된 AI 뉴스 에이전트 시스템",
    description="쿠키 기반 개인화 뉴스 요약 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/api/cookie-consent")
async def handle_cookie_consent(
    request: CookieConsentRequest,
    profile_service: UserProfileService = Depends(get_user_profile_service)
):
    """쿠키 사용 동의 처리"""
    try:
        if request.consent_given and request.cookie_data:
            profile = profile_service.create_profile_from_cookies(
                request.user_id, 
                request.cookie_data
            )
        else:
            profile = profile_service.create_default_profile(request.user_id)
        
        return {"success": True, "profile_type": profile["profile_type"]}
    
    except Exception as e:
        logger.error(f"Cookie consent error: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")

@app.post("/api/news-summary", response_model=List[NewsSummaryResponse])
async def get_news_summary(
    request: NewsRequest,
    profile_service: UserProfileService = Depends(get_user_profile_service),
    news_service: NewsService = Depends(get_news_service)
):
    """개인화된 뉴스 요약 조회"""
    try:
        # 사용자 프로파일 조회
        profile = profile_service.get_or_create_profile(request.user_id)
        
        # 개인화된 뉴스 요약 생성
        summaries = news_service.get_personalized_news_summary(profile)
        
        return summaries
    
    except Exception as e:
        logger.error(f"News summary error: {e}")
        raise HTTPException(status_code=500, detail="뉴스 요약 생성 중 오류가 발생했습니다.")

@app.get("/api/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/profile/{user_id}")
async def get_user_profile(
    user_id: str,
    profile_service: UserProfileService = Depends(get_user_profile_service)
):
    """사용자 프로파일 조회"""
    try:
        profile = profile_service.get_or_create_profile(user_id)
        # 민감한 정보 제외하고 반환
        return {
            "user_id": profile["user_id"],
            "interests": profile["interests"],
            "profile_type": profile["profile_type"],
            "updated_at": profile["updated_at"]
        }
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        raise HTTPException(status_code=500, detail="프로파일 조회 중 오류가 발생했습니다.")

# =============================================================================
# 메인 실행부
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )