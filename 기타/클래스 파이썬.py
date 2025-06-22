"""
대학교 수준 뉴스 에이전트 시스템 - 파이썬 클래스 설계 (단순화 버전)
객체지향 프로그래밍 학습을 위한 적절한 복잡도의 클래스 구조
"""

import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# 기본 데이터 모델 (Data Models)
# ============================================================================

class NewsCategory(Enum):
    """뉴스 카테고리 열거형"""
    POLITICS = "정치"
    ECONOMY = "경제" 
    TECHNOLOGY = "기술"
    SPORTS = "스포츠"
    ENTERTAINMENT = "연예"


@dataclass
class UserProfile:
    """사용자 프로파일 데이터 클래스"""
    user_id: str
    interests: List[NewsCategory]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환 (JSON 저장용)"""
        return {
            'user_id': self.user_id,
            'interests': [cat.value for cat in self.interests],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        """딕셔너리에서 객체 생성"""
        return cls(
            user_id=data['user_id'],
            interests=[NewsCategory(cat) for cat in data['interests']],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )


@dataclass 
class NewsArticle:
    """뉴스 기사 데이터 클래스"""
    title: str
    content: str
    category: NewsCategory
    source: str
    url: str
    published_at: datetime


@dataclass
class NewsSummary:
    """뉴스 요약 데이터 클래스"""
    summary_text: str
    articles_count: int
    created_at: datetime
    user_id: str


# ============================================================================
# 사용자 관리 클래스 (User Management)
# ============================================================================

class UserManager:
    """사용자 프로파일 관리 클래스"""
    
    def __init__(self, data_file: str = "user_profiles.json"):
        """
        사용자 관리자 초기화
        
        Args:
            data_file: 사용자 데이터 저장 파일 경로
        """
        self.data_file = data_file
        self.profiles: Dict[str, UserProfile] = {}
        self.load_profiles()
    
    def load_profiles(self):
        """JSON 파일에서 사용자 프로파일 로드"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for user_id, profile_data in data.items():
                    self.profiles[user_id] = UserProfile.from_dict(profile_data)
        except FileNotFoundError:
            print(f"프로파일 파일 {self.data_file}이 없습니다. 새로 생성합니다.")
            self.profiles = {}
    
    def save_profiles(self):
        """사용자 프로파일을 JSON 파일에 저장"""
        data = {}
        for user_id, profile in self.profiles.items():
            data[user_id] = profile.to_dict()
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """사용자 프로파일 조회"""
        return self.profiles.get(user_id)
    
    def create_profile(self, user_id: str, interests: List[NewsCategory]) -> UserProfile:
        """새 사용자 프로파일 생성"""
        now = datetime.now()
        profile = UserProfile(
            user_id=user_id,
            interests=interests,
            created_at=now,
            updated_at=now
        )
        self.profiles[user_id] = profile
        self.save_profiles()
        return profile
    
    def update_interests(self, user_id: str, new_interests: List[NewsCategory]):
        """사용자 관심사 업데이트"""
        if user_id in self.profiles:
            self.profiles[user_id].interests = new_interests
            self.profiles[user_id].updated_at = datetime.now()
            self.save_profiles()
    
    def create_default_profile(self, user_id: str) -> UserProfile:
        """기본 프로파일 생성 (관심사를 모를 때)"""
        default_interests = [
            NewsCategory.POLITICS,
            NewsCategory.ECONOMY,
            NewsCategory.TECHNOLOGY
        ]
        return self.create_profile(user_id, default_interests)


# ============================================================================
# 뉴스 수집 클래스 (News Collection)
# ============================================================================

class NewsCollector:
    """뉴스 수집 클래스"""
    
    def __init__(self, api_key: str):
        """
        뉴스 수집기 초기화
        
        Args:
            api_key: News API 키
        """
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/top-headlines"
        self.category_mapping = {
            NewsCategory.POLITICS: "general",
            NewsCategory.ECONOMY: "business", 
            NewsCategory.TECHNOLOGY: "technology",
            NewsCategory.SPORTS: "sports",
            NewsCategory.ENTERTAINMENT: "entertainment"
        }
    
    def fetch_news(self, category: NewsCategory, country: str = "kr", 
                   page_size: int = 10) -> List[NewsArticle]:
        """
        뉴스 API에서 뉴스 가져오기
        
        Args:
            category: 뉴스 카테고리
            country: 국가 코드
            page_size: 가져올 기사 수
            
        Returns:
            뉴스 기사 리스트
        """
        params = {
            'apiKey': self.api_key,
            'country': country,
            'category': self.category_mapping.get(category, 'general'),
            'pageSize': page_size
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article_data in data.get('articles', []):
                if article_data.get('title') and article_data.get('description'):
                    article = NewsArticle(
                        title=article_data['title'],
                        content=article_data['description'],
                        category=category,
                        source=article_data.get('source', {}).get('name', 'Unknown'),
                        url=article_data.get('url', ''),
                        published_at=datetime.now()  # 실제로는 파싱 필요
                    )
                    articles.append(article)
            
            return articles
            
        except requests.RequestException as e:
            print(f"뉴스 가져오기 실패: {e}")
            return []
    
    def fetch_news_by_interests(self, interests: List[NewsCategory]) -> List[NewsArticle]:
        """사용자 관심사에 따른 뉴스 수집"""
        all_articles = []
        for category in interests:
            articles = self.fetch_news(category, page_size=5)
            all_articles.extend(articles)
        return all_articles


# ============================================================================
# AI 요약 클래스 (AI Summarization)
# ============================================================================

class NewsSummarizer:
    """뉴스 요약 클래스 (OpenAI API 사용)"""
    
    def __init__(self, api_key: str):
        """
        뉴스 요약기 초기화
        
        Args:
            api_key: OpenAI API 키
        """
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def summarize_articles(self, articles: List[NewsArticle], 
                          user_interests: List[NewsCategory]) -> str:
        """
        뉴스 기사들을 요약
        
        Args:
            articles: 요약할 뉴스 기사 리스트
            user_interests: 사용자 관심사
            
        Returns:
            요약된 뉴스 텍스트
        """
        if not articles:
            return "표시할 뉴스가 없습니다."
        
        # 기사 내용을 하나의 텍스트로 합치기
        combined_text = ""
        for article in articles:
            combined_text += f"제목: {article.title}\n내용: {article.content}\n\n"
        
        # 관심사를 문자열로 변환
        interests_str = ", ".join([cat.value for cat in user_interests])
        
        # 프롬프트 생성
        prompt = f"""
다음 뉴스들을 사용자의 관심사({interests_str})에 맞춰 한국어로 요약해주세요.
중요한 내용만 간결하게 3-4문장으로 정리해주세요.

뉴스 내용:
{combined_text}

요약:
"""
        
        return self._call_openai_api(prompt)
    
    def _call_openai_api(self, prompt: str) -> str:
        """OpenAI API 호출 (간단한 버전)"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',  # 비용 절약을 위해 3.5 사용
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 300,
            'temperature': 0.7
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content'].strip()
            
        except requests.RequestException as e:
            print(f"AI 요약 실패: {e}")
            return "요약을 생성할 수 없습니다. 나중에 다시 시도해주세요."


# ============================================================================
# 웹 인터페이스 클래스 (Web Interface)
# ============================================================================

class WebInterface:
    """Flask 기반 웹 인터페이스"""
    
    def __init__(self, news_agent):
        """
        웹 인터페이스 초기화
        
        Args:
            news_agent: NewsAgent 인스턴스
        """
        self.news_agent = news_agent
        # Flask 앱은 실제 구현에서 설정
    
    def render_main_page(self, user_id: str) -> str:
        """메인 페이지 렌더링"""
        # 실제로는 HTML 템플릿을 사용
        summary = self.news_agent.get_personalized_summary(user_id)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>개인화 뉴스 요약</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .mobile {{ max-width: 100%; }}
            </style>
        </head>
        <body>
            <h1>🗞️ 개인화 뉴스 요약</h1>
            <div class="summary">
                {summary}
            </div>
            <p><small>마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}</small></p>
        </body>
        </html>
        """
        return html
    
    def detect_device_type(self, user_agent: str) -> str:
        """디바이스 타입 감지 (간단한 버전)"""
        user_agent = user_agent.lower()
        if 'mobile' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent:
            return 'tablet'
        else:
            return 'desktop'


# ============================================================================
# 메인 뉴스 에이전트 클래스 (Main News Agent)
# ============================================================================

class NewsAgent:
    """
    메인 뉴스 에이전트 클래스
    모든 구성 요소를 조합하여 전체 시스템을 관리
    """
    
    def __init__(self, news_api_key: str, openai_api_key: str):
        """
        뉴스 에이전트 초기화
        
        Args:
            news_api_key: News API 키
            openai_api_key: OpenAI API 키
        """
        # 각 모듈 초기화
        self.user_manager = UserManager()
        self.news_collector = NewsCollector(news_api_key)
        self.news_summarizer = NewsSummarizer(openai_api_key)
        self.web_interface = WebInterface(self)
        
        # 캐시 (간단한 메모리 캐시)
        self.summary_cache: Dict[str, tuple] = {}  # {user_id: (summary, timestamp)}
        self.cache_duration = timedelta(hours=3)  # 3시간 캐시
    
    def get_or_create_user_profile(self, user_id: str, 
                                  interests: Optional[List[NewsCategory]] = None) -> UserProfile:
        """사용자 프로파일 가져오기 또는 생성"""
        profile = self.user_manager.get_profile(user_id)
        
        if profile is None:
            if interests:
                profile = self.user_manager.create_profile(user_id, interests)
            else:
                profile = self.user_manager.create_default_profile(user_id)
        
        return profile
    
    def get_personalized_summary(self, user_id: str) -> str:
        """개인화된 뉴스 요약 생성"""
        # 캐시 확인
        if user_id in self.summary_cache:
            summary, timestamp = self.summary_cache[user_id]
            if datetime.now() - timestamp < self.cache_duration:
                return summary
        
        # 사용자 프로파일 가져오기
        profile = self.get_or_create_user_profile(user_id)
        
        # 뉴스 수집
        articles = self.news_collector.fetch_news_by_interests(profile.interests)
        
        # AI 요약 생성
        summary = self.news_summarizer.summarize_articles(articles, profile.interests)
        
        # 캐시에 저장
        self.summary_cache[user_id] = (summary, datetime.now())
        
        return summary
    
    def update_user_interests(self, user_id: str, new_interests: List[NewsCategory]):
        """사용자 관심사 업데이트"""
        self.user_manager.update_interests(user_id, new_interests)
        
        # 캐시 무효화
        if user_id in self.summary_cache:
            del self.summary_cache[user_id]
    
    def render_web_page(self, user_id: str, user_agent: str = "") -> str:
        """웹 페이지 렌더링"""
        return self.web_interface.render_main_page(user_id)


# ============================================================================
# Flask 웹 애플리케이션 (실제 구현 예시)
# ============================================================================

def create_flask_app(news_api_key: str, openai_api_key: str):
    """Flask 애플리케이션 생성 함수"""
    from flask import Flask, request, render_template_string
    
    app = Flask(__name__)
    news_agent = NewsAgent(news_api_key, openai_api_key)
    
    @app.route('/')
    def home():
        """홈 페이지"""
        user_id = request.args.get('user_id', 'default_user')
        user_agent = request.headers.get('User-Agent', '')
        
        return news_agent.render_web_page(user_id, user_agent)
    
    @app.route('/update_interests', methods=['POST'])
    def update_interests():
        """관심사 업데이트"""
        user_id = request.form.get('user_id', 'default_user')
        interests_str = request.form.getlist('interests')
        
        # 문자열을 NewsCategory로 변환
        try:
            interests = [NewsCategory(cat) for cat in interests_str]
            news_agent.update_user_interests(user_id, interests)
            return "관심사가 업데이트되었습니다!"
        except ValueError:
            return "잘못된 관심사입니다.", 400
    
    return app


# ============================================================================
# 메인 실행 코드 (사용 예시)
# ============================================================================

def main():
    """메인 실행 함수"""
    # API 키 설정 (실제로는 환경변수에서 가져오기)
    NEWS_API_KEY = "your_news_api_key_here"
    OPENAI_API_KEY = "your_openai_api_key_here"
    
    # 뉴스 에이전트 생성
    agent = NewsAgent(NEWS_API_KEY, OPENAI_API_KEY)
    
    # 테스트 사용자 생성
    test_user = "student123"
    test_interests = [NewsCategory.TECHNOLOGY, NewsCategory.ECONOMY]
    
    # 사용자 프로파일 생성
    profile = agent.get_or_create_user_profile(test_user, test_interests)
    print(f"사용자 프로파일: {profile}")
    
    # 개인화된 뉴스 요약 생성
    summary = agent.get_personalized_summary(test_user)
    print(f"\n뉴스 요약:\n{summary}")
    
    # 웹 서버 실행 (Flask)
    print("\n웹 서버를 시작합니다...")
    app = create_flask_app(NEWS_API_KEY, OPENAI_API_KEY)
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()


"""
=== 대학교 수준 클래스 다이어그램 특징 ===

1. 🎓 학습 목표
   - 객체지향 프로그래밍 기본 개념 (클래스, 상속, 캡슐화)
   - 파이썬 데이터클래스와 열거형 활용
   - 외부 API 연동 및 JSON 데이터 처리
   - 간단한 웹 서비스 구현

2. 📚 적절한 복잡도
   - 총 6개의 주요 클래스 (너무 많지 않음)
   - 각 클래스는 명확한 단일 책임
   - 이해하기 쉬운 메서드명과 주석
   - 실제 동작하는 완전한 코드

3. 🔧 실용적 기능
   - JSON 파일 기반 데이터 저장 (DB 없이도 동작)
   - News API와 OpenAI API 실제 연동
   - Flask 기반 웹 인터페이스
   - 기본적인 캐싱 메커니즘

4. 📝 확장 가능성
   - 새로운 뉴스 카테고리 추가 용이
   - 다른 API 서비스로 교체 가능
   - 웹 UI 개선 및 기능 추가 가능
   - 데이터베이스 연동으로 업그레이드 가능

이 설계는 대학교 프로젝트로서 다음과 같은 학습 효과를 제공합니다:
- 실제 동작하는 시스템 완성의 성취감
- 객체지향 설계 원칙의 실습
- 외부 서비스 연동 경험
- 웹 개발 기초 경험
"""