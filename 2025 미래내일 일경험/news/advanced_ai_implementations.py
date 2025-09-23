# advanced_ai_service.py - 실제 AI API 연동 구현체
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

# LangChain 관련 임포트
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks import get_openai_callback

# 뉴스 API 관련 임포트
import requests
from bs4 import BeautifulSoup
import feedparser

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# =============================================================================
# 실제 뉴스 데이터 제공자 구현 (개방-폐쇄 원칙)
# =============================================================================

class NewsAPIProvider:
    """NewsAPI.org를 사용한 실제 뉴스 데이터 제공자"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2"
        
    def fetch_news(self, category: str = "general", language: str = "ko") -> List[Dict[str, Any]]:
        """NewsAPI에서 뉴스 데이터 가져오기"""
        if not self.api_key:
            raise ValueError("NEWS_API_KEY가 설정되지 않았습니다.")
        
        # 카테고리 매핑 (한국어 -> 영어)
        category_mapping = {
            "일반": "general",
            "기술": "technology", 
            "경제": "business",
            "스포츠": "sports",
            "과학": "science",
            "건강": "health",
            "엔터테인먼트": "entertainment"
        }
        
        english_category = category_mapping.get(category, category)
        
        params = {
            'apiKey': self.api_key,
            'category': english_category,
            'country': 'kr',
            'pageSize': 10,
            'sortBy': 'publishedAt'
        }
        
        try:
            response = requests.get(f"{self.base_url}/top-headlines", params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            formatted_news = []
            for article in articles:
                if article.get('title') and article.get('description'):
                    formatted_news.append({
                        'title': article['title'],
                        'content': article.get('description', '') + ' ' + (article.get('content', '') or ''),
                        'category': category,
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'published_at': article.get('publishedAt', datetime.now().isoformat()),
                        'url': article.get('url', '')
                    })
            
            return formatted_news
            
        except requests.RequestException as e:
            logging.error(f"뉴스 API 호출 실패: {e}")
            return []

class RSSNewsProvider:
    """RSS 피드를 사용한 뉴스 데이터 제공자"""
    
    def __init__(self):
        self.rss_feeds = {
            "일반": [
                "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
                "https://rss.cnn.com/rss/edition.rss"
            ],
            "기술": [
                "https://feeds.feedburner.com/TechCrunch",
                "https://www.wired.com/feed"
            ],
            "경제": [
                "https://feeds.bloomberg.com/markets/news.rss",
                "https://www.economist.com/rss"
            ]
        }
    
    def fetch_news(self, category: str = "일반") -> List[Dict[str, Any]]:
        """RSS 피드에서 뉴스 데이터 가져오기"""
        feeds = self.rss_feeds.get(category, self.rss_feeds["일반"])
        articles = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:  # 각 피드에서 최대 5개
                    articles.append({
                        'title': entry.get('title', ''),
                        'content': entry.get('summary', ''),
                        'category': category,
                        'source': feed.feed.get('title', 'RSS'),
                        'published_at': entry.get('published', datetime.now().isoformat()),
                        'url': entry.get('link', '')
                    })
            except Exception as e:
                logging.error(f"RSS 피드 파싱 실패 ({feed_url}): {e}")
                continue
        
        return articles

# =============================================================================
# LangChain 기반 AI 요약 서비스 구현 (단일 책임 원칙)
# =============================================================================

class LangChainAISummarizer:
    """LangChain과 OpenAI를 사용한 실제 AI 요약 서비스"""
    
    def __init__(self, openai_api_key: str = None, model_name: str = "gpt-3.5-turbo"):
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        # LangChain LLM 초기화
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=self.api_key,
            temperature=0.3,
            max_tokens=500
        )
        
        # 프롬프트 템플릿 설정
        self._setup_prompts()
        
        # 체인 설정
        self._setup_chains()
    
    def _setup_prompts(self):
        """프롬프트 템플릿 설정"""
        
        # 1차 요약 프롬프트
        self.summary_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""당신은 뉴스 요약 전문가입니다. 
주어진 뉴스 기사를 사용자의 관심사에 맞게 개인화하여 요약해주세요.

요약 규칙:
1. 300자 이내로 요약
2. 핵심 내용과 사용자 관심사 연결점 강조
3. 객관적이고 정확한 정보 제공
4. 한국어로 작성"""),
            HumanMessage(content="""
뉴스 제목: {title}
뉴스 내용: {content}
사용자 관심사: {interests}

위 정보를 바탕으로 사용자에게 맞춤형 뉴스 요약을 작성해주세요:
""")
        ])
        
        # 재질의 검증 프롬프트
        self.validation_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""당신은 뉴스 요약 검증 전문가입니다.
원본 기사와 요약본을 비교하여 정확성을 검증하고 개선점을 제시해주세요.

검증 기준:
1. 사실 정확성
2. 핵심 내용 누락 여부  
3. 편향성 확인
4. 요약 품질"""),
            HumanMessage(content="""
원본 기사: {original_content}
작성된 요약: {summary}

위 요약이 정확한지 검증하고, 필요시 개선된 요약을 제공해주세요:
""")
        ])
        
        # 관심사 분석 프롬프트
        self.interest_analysis_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""당신은 사용자 행동 분석 전문가입니다.
사용자의 웹 활동 데이터를 분석하여 뉴스 관심사를 추출해주세요."""),
            HumanMessage(content="""
사용자 쿠키 데이터: {cookie_data}

이 데이터에서 뉴스 관심사를 분석하고 3-5개의 카테고리로 정리해주세요:
""")
        ])
    
    def _setup_chains(self):
        """LangChain 체인 설정"""
        
        # 요약 체인
        self.summary_chain = LLMChain(
            llm=self.llm,
            prompt=self.summary_prompt,
            output_key="summary"
        )
        
        # 검증 체인
        self.validation_chain = LLMChain(
            llm=self.llm,
            prompt=self.validation_prompt,
            output_key="validated_summary"
        )
        
        # 순차 체인 (요약 -> 검증)
        self.sequential_chain = SequentialChain(
            chains=[self.summary_chain, self.validation_chain],
            input_variables=["title", "content", "interests", "original_content"],
            output_variables=["summary", "validated_summary"],
            verbose=True
        )
        
        # 관심사 분석 체인
        self.interest_chain = LLMChain(
            llm=self.llm,
            prompt=self.interest_analysis_prompt,
            output_key="interests"
        )
    
    async def summarize_news(self, news_content: str, user_interests: List[str], title: str = "") -> str:
        """비동기 뉴스 요약 생성"""
        try:
            with get_openai_callback() as cb:
                interests_str = ", ".join(user_interests)
                
                result = await asyncio.to_thread(
                    self.summary_chain.run,
                    title=title,
                    content=news_content,
                    interests=interests_str
                )
                
                # 토큰 사용량 로깅
                logging.info(f"요약 생성 - 토큰 사용량: {cb.total_tokens}, 비용: ${cb.total_cost:.4f}")
                
                return result
                
        except Exception as e:
            logging.error(f"AI 요약 생성 실패: {e}")
            return f"[요약 실패] {news_content[:200]}..."
    
    async def validate_summary(self, original_content: str, summary: str) -> str:
        """비동기 요약 검증 및 개선"""
        try:
            with get_openai_callback() as cb:
                result = await asyncio.to_thread(
                    self.validation_chain.run,
                    original_content=original_content,
                    summary=summary
                )
                
                logging.info(f"요약 검증 - 토큰 사용량: {cb.total_tokens}, 비용: ${cb.total_cost:.4f}")
                
                return result
                
        except Exception as e:
            logging.error(f"AI 요약 검증 실패: {e}")
            return summary + " [검증 실패]"
    
    async def analyze_interests_from_cookies(self, cookie_data: Dict[str, Any]) -> List[str]:
        """쿠키 데이터에서 관심사 AI 분석"""
        try:
            with get_openai_callback() as cb:
                cookie_str = str(cookie_data)
                
                result = await asyncio.to_thread(
                    self.interest_chain.run,
                    cookie_data=cookie_str
                )
                
                logging.info(f"관심사 분석 - 토큰 사용량: {cb.total_tokens}, 비용: ${cb.total_cost:.4f}")
                
                # AI 응답에서 관심사 추출 (간단한 파싱)
                interests = []
                for line in result.split('\n'):
                    if any(keyword in line for keyword in ['관심사', '카테고리', '주제']):
                        # 콜론 뒤의 내용 추출
                        if ':' in line:
                            interest_part = line.split(':', 1)[1].strip()
                            interests.extend([i.strip() for i in interest_part.split(',')])
                
                return interests[:5] if interests else ['일반', '사회', '경제']
                
        except Exception as e:
            logging.error(f"관심사 AI 분석 실패: {e}")
            return ['일반', '사회', '경제']

# =============================================================================
# 고급 사용자 프로파일 분석기 (리스코프 치환 원칙)
# =============================================================================

class AdvancedCookieAnalyzer:
    """AI 기반 고급 쿠키 분석기"""
    
    def __init__(self, ai_summarizer: LangChainAISummarizer):
        self.ai_summarizer = ai_summarizer
    
    async def analyze_cookies(self, cookie_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI를 활용한 고급 쿠키 분석"""
        
        # 기본 패턴 분석
        basic_interests = self._basic_pattern_analysis(cookie_data)
        
        # AI 기반 심화 분석
        ai_interests = await self.ai_summarizer.analyze_interests_from_cookies(cookie_data)
        
        # 결과 통합
        combined_interests = list(set(basic_interests + ai_interests))
        
        return {
            'interests': combined_interests,
            'confidence_score': self._calculate_confidence(cookie_data),
            'analysis_method': 'ai_enhanced',
            'analyzed_at': datetime.now().isoformat(),
            'raw_data_size': len(str(cookie_data))
        }
    
    def _basic_pattern_analysis(self, cookie_data: Dict[str, Any]) -> List[str]:
        """기본 패턴 분석"""
        interests = []
        
        # 방문 카테고리 분석
        if 'visited_categories' in cookie_data:
            interests.extend(cookie_data['visited_categories'])
        
        # 검색 히스토리 키워드 추출
        if 'search_history' in cookie_data:
            for search in cookie_data['search_history']:
                search_lower = search.lower()
                if any(tech_word in search_lower for tech_word in ['ai', '기술', 'tech', '인공지능']):
                    interests.append('기술')
                elif any(econ_word in search_lower for econ_word in ['경제', '주식', '투자', 'economy']):
                    interests.append('경제')
                elif any(sport_word in search_lower for sport_word in ['스포츠', '야구', '축구', 'sport']):
                    interests.append('스포츠')
        
        # 방문 시간 패턴 분석
        if 'visit_times' in cookie_data:
            visit_times = cookie_data['visit_times']
            if any(time.startswith('09:') or time.startswith('10:') for time in visit_times):
                interests.append('경제')  # 아침 시간대 방문자는 경제 관심 높음
        
        return list(set(interests))
    
    def _calculate_confidence(self, cookie_data: Dict[str, Any]) -> float:
        """분석 신뢰도 계산"""
        confidence = 0.0
        
        # 데이터 양에 따른 신뢰도
        data_points = len(cookie_data.get('visited_categories', [])) + \
                     len(cookie_data.get('search_history', [])) + \
                     len(cookie_data.get('visit_times', []))
        
        confidence += min(data_points * 0.1, 0.7)
        
        # 데이터 다양성에 따른 신뢰도
        if len(cookie_data.keys()) > 3:
            confidence += 0.2
        
        # 최근성에 따른 신뢰도
        if 'last_visit' in cookie_data:
            try:
                last_visit = datetime.fromisoformat(cookie_data['last_visit'])
                days_ago = (datetime.now() - last_visit).days
                if days_ago < 7:
                    confidence += 0.1
            except:
                pass
        
        return min(confidence, 1.0)

# =============================================================================
# 고성능 뉴스 서비스 (비동기 처리)
# =============================================================================

class AsyncNewsService:
    """비동기 처리를 지원하는 고성능 뉴스 서비스"""
    
    def __init__(self, news_provider, ai_summarizer: LangChainAISummarizer):
        self.news_provider = news_provider
        self.ai_summarizer = ai_summarizer
        self.cache = {}  # 실제 환경에서는 Redis 사용
    
    async def get_personalized_news_summary(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """비동기 개인화 뉴스 요약 생성"""
        
        cache_key = f"{user_profile['user_id']}_{datetime.now().strftime('%Y%m%d_%H')}"
        
        # 캐시 확인
        if cache_key in self.cache:
            logging.info(f"캐시에서 뉴스 요약 반환: {cache_key}")
            return self.cache[cache_key]
        
        # 뉴스 데이터 가져오기
        news_data = await asyncio.to_thread(self.news_provider.fetch_news)
        user_interests = user_profile.get('interests', ['일반'])
        
        # 병렬 요약 처리
        tasks = []
        for news_item in news_data[:5]:  # 최대 5개
            task = self._process_single_news(news_item, user_interests)
            tasks.append(task)
        
        summaries = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리 및 필터링
        valid_summaries = []
        for summary in summaries:
            if isinstance(summary, Exception):
                logging.error(f"뉴스 처리 실패: {summary}")
                continue
            if summary:
                valid_summaries.append(summary)
        
        # 관련성 점수로 정렬
        valid_summaries.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # 캐시 저장
        self.cache[cache_key] = valid_summaries
        
        return valid_summaries
    
    async def _process_single_news(self, news_item: Dict[str, Any], user_interests: List[str]) -> Optional[Dict[str, Any]]:
        """단일 뉴스 처리 (요약 + 검증)"""
        try:
            # 1차 AI 요약
            summary = await self.ai_summarizer.summarize_news(
                news_item['content'],
                user_interests,
                news_item['title']
            )
            
            # 2차 AI 검증 (재질의)
            validated_summary = await self.ai_summarizer.validate_summary(
                news_item['content'],
                summary
            )
            
            # 관련성 점수 계산
            relevance_score = self._calculate_relevance_score(news_item, user_interests)
            
            return {
                'title': news_item['title'],
                'summary': validated_summary,
                'category': news_item['category'],
                'source': news_item['source'],
                'published_at': news_item['published_at'],
                'relevance_score': relevance_score,
                'url': news_item.get('url', ''),
                'processing_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"뉴스 처리 실패 ({news_item.get('title', 'Unknown')}): {e}")
            return None
    
    def _calculate_relevance_score(self, news_item: Dict[str, Any], user_interests: List[str]) -> float:
        """AI 기반 관련성 점수 계산"""
        score = 0.0
        content_text = (news_item.get('title', '') + ' ' + news_item.get('content', '')).lower()
        
        # 키워드 매칭
        for interest in user_interests:
            if interest.lower() in content_text:
                score += 1.0
        
        # 카테고리 매칭
        if news_item.get('category', '').lower() in [i.lower() for i in user_interests]:
            score += 2.0
        
        # 최신성 보너스
        try:
            published_time = datetime.fromisoformat(news_item['published_at'].replace('Z', '+00:00'))
            hours_ago = (datetime.now() - published_time.replace(tzinfo=None)).total_seconds() / 3600
            if hours_ago < 6:  # 6시간 이내
                score += 0.5
        except:
            pass
        
        return min(score, 5.0)  # 최대 5점

# =============================================================================
# 통합 팩토리 클래스 (의존성 역전 원칙)
# =============================================================================

class ServiceFactory:
    """서비스 객체들을 생성하는 팩토리"""
    
    @staticmethod
    def create_production_services():
        """프로덕션 환경용 서비스 생성"""
        
        # AI 서비스 초기화
        ai_summarizer = LangChainAISummarizer()
        
        # 뉴스 제공자 (News API 우선, 실패시 RSS)
        try:
            news_provider = NewsAPIProvider()
            # API 키 테스트
            test_news = news_provider.fetch_news()
            if not test_news:
                raise Exception("News API 테스트 실패")
        except:
            logging.warning("News API 사용 불가, RSS 제공자로 대체")
            news_provider = RSSNewsProvider()
        
        # 고급 쿠키 분석기
        cookie_analyzer = AdvancedCookieAnalyzer(ai_summarizer)
        
        # 비동기 뉴스 서비스
        news_service = AsyncNewsService(news_provider, ai_summarizer)
        
        return {
            'ai_summarizer': ai_summarizer,
            'news_provider': news_provider,
            'cookie_analyzer': cookie_analyzer,
            'news_service': news_service
        }
    
    @staticmethod 
    def create_development_services():
        """개발 환경용 서비스 생성 (Mock 객체들)"""
        from main import MockNewsDataProvider, MockAISummarizer, CookieAnalyzer, NewsService
        
        return {
            'news_provider': MockNewsDataProvider(),
            'ai_summarizer': MockAISummarizer(),
            'cookie_analyzer': CookieAnalyzer(),
            'news_service': NewsService(MockNewsDataProvider(), MockAISummarizer())
        }

# =============================================================================
# 사용 예시
# =============================================================================

async def main():
    """사용 예시"""
    
    # 프로덕션 서비스 생성
    services = ServiceFactory.create_production_services()
    
    # 테스트 사용자 프로파일
    test_profile = {
        'user_id': 'test_user',
        'interests': ['기술', 'AI', '경제'],
        'profile_type': 'personalized'
    }
    
    # 개인화된 뉴스 요약 생성
    summaries = await services['news_service'].get_personalized_news_summary(test_profile)
    
    print(f"생성된 요약 개수: {len(summaries)}")
    for summary in summaries:
        print(f"제목: {summary['title']}")
        print(f"요약: {summary['summary'][:100]}...")
        print(f"관련성: {summary['relevance_score']:.2f}")
        print("-" * 50)

if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main())