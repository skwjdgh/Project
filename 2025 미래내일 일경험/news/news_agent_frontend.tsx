import React, { useState, useEffect } from 'react';
import { AlertCircle, Clock, User, Newspaper, Settings, Check, X } from 'lucide-react';

// SOLID 원칙을 적용한 React 컴포넌트 구조

// =============================================================================
// 인터페이스 및 타입 정의 (인터페이스 분리 원칙 - ISP)
// =============================================================================

interface NewsItem {
  title: string;
  summary: string;
  category: string;
  source: string;
  published_at: string;
  relevance_score: number;
}

interface UserProfile {
  user_id: string;
  interests: string[];
  profile_type: 'personalized' | 'default';
  updated_at: string;
}

interface CookieData {
  visited_categories?: string[];
  search_history?: string[];
  last_visit?: string;
}

// =============================================================================
// 커스텀 훅 (단일 책임 원칙 - SRP)
// =============================================================================

const useUserManager = () => {
  const [userId, setUserId] = useState<string>('');
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    // 사용자 ID 생성 또는 로컬 스토리지에서 복원
    let currentUserId = sessionStorage.getItem('user_id');
    if (!currentUserId) {
      currentUserId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('user_id', currentUserId);
    }
    setUserId(currentUserId);
  }, []);

  const fetchProfile = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/profile/${id}`);
      if (response.ok) {
        const profileData = await response.json();
        setProfile(profileData);
      }
    } catch (error) {
      console.error('Profile fetch error:', error);
    }
  };

  return { userId, profile, setProfile, fetchProfile };
};

const useCookieManager = () => {
  const [cookieConsent, setCookieConsent] = useState<boolean | null>(null);

  const generateMockCookieData = (): CookieData => {
    // 실제 환경에서는 document.cookie에서 데이터 추출
    const mockData: CookieData = {
      visited_categories: ['기술', 'AI', '경제'],
      search_history: ['인공지능 뉴스', '주식 시장', '기술 트렌드'],
      last_visit: new Date().toISOString()
    };
    return mockData;
  };

  const handleCookieConsent = async (userId: string, consent: boolean) => {
    try {
      const cookieData = consent ? generateMockCookieData() : null;
      
      const response = await fetch('http://localhost:8000/api/cookie-consent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          consent_given: consent,
          cookie_data: cookieData
        })
      });

      if (response.ok) {
        setCookieConsent(consent);
        sessionStorage.setItem('cookie_consent', consent.toString());
        return await response.json();
      }
    } catch (error) {
      console.error('Cookie consent error:', error);
    }
  };

  useEffect(() => {
    const savedConsent = sessionStorage.getItem('cookie_consent');
    if (savedConsent !== null) {
      setCookieConsent(savedConsent === 'true');
    }
  }, []);

  return { cookieConsent, handleCookieConsent };
};

const useNewsManager = () => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNews = async (userId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/news-summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId })
      });

      if (response.ok) {
        const newsData = await response.json();
        setNews(newsData);
      } else {
        setError('뉴스를 불러오는데 실패했습니다.');
      }
    } catch (error) {
      setError('서버 연결에 실패했습니다.');
      console.error('News fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  return { news, loading, error, fetchNews };
};

// =============================================================================
// 재사용 가능한 컴포넌트들 (단일 책임 원칙 - SRP)
// =============================================================================

const CookieConsentModal: React.FC<{
  onConsent: (consent: boolean) => void;
  loading: boolean;
}> = ({ onConsent, loading }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex items-center mb-4">
          <AlertCircle className="text-blue-500 mr-3" size={24} />
          <h2 className="text-xl font-bold text-gray-800">쿠키 사용 동의</h2>
        </div>
        
        <div className="mb-6">
          <p className="text-gray-600 mb-4">
            개인화된 뉴스 서비스 제공을 위해 쿠키 데이터를 사용하고자 합니다.
          </p>
          <ul className="text-sm text-gray-500 space-y-1">
            <li>• 방문 기록 기반 관심사 분석</li>
            <li>• 개인정보는 저장되지 않습니다</li>
            <li>• GDPR 및 개인정보보호법 준수</li>
          </ul>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={() => onConsent(true)}
            disabled={loading}
            className="flex-1 bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 disabled:opacity-50 flex items-center justify-center"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            ) : (
              <>
                <Check size={16} className="mr-2" />
                동의
              </>
            )}
          </button>
          <button
            onClick={() => onConsent(false)}
            disabled={loading}
            className="flex-1 bg-gray-500 text-white py-2 px-4 rounded hover:bg-gray-600 disabled:opacity-50 flex items-center justify-center"
          >
            <X size={16} className="mr-2" />
            거부
          </button>
        </div>
      </div>
    </div>
  );
};

const NewsCard: React.FC<{ news: NewsItem }> = ({ news }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR');
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      '기술': 'bg-blue-100 text-blue-800',
      '경제': 'bg-green-100 text-green-800',
      '스포츠': 'bg-red-100 text-red-800',
      '사회': 'bg-purple-100 text-purple-800',
      '일반': 'bg-gray-100 text-gray-800'
    };
    return colors[category as keyof typeof colors] || colors['일반'];
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-start justify-between mb-3">
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(news.category)}`}>
          {news.category}
        </span>
        <span className="text-xs text-gray-500 flex items-center">
          <Clock size={12} className="mr-1" />
          {formatDate(news.published_at)}
        </span>
      </div>
      
      <h3 className="text-lg font-bold text-gray-800 mb-3 line-clamp-2">
        {news.title}
      </h3>
      
      <p className="text-gray-600 mb-4 leading-relaxed">
        {news.summary}
      </p>
      
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500">
          출처: {news.source}
        </span>
        <div className="flex items-center">
          <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
          <span className="text-xs text-gray-500">
            관련도: {(news.relevance_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
};

const UserProfileCard: React.FC<{ profile: UserProfile | null }> = ({ profile }) => {
  if (!profile) return null;

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6">
      <div className="flex items-center mb-3">
        <User className="text-blue-500 mr-2" size={20} />
        <h3 className="text-lg font-semibold">사용자 프로파일</h3>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">프로파일 유형:</span>
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            profile.profile_type === 'personalized' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-800'
          }`}>
            {profile.profile_type === 'personalized' ? '개인화' : '기본'}
          </span>
        </div>
        
        <div>
          <span className="text-sm text-gray-600 block mb-1">관심사:</span>
          <div className="flex flex-wrap gap-1">
            {profile.interests.map((interest, index) => (
              <span 
                key={index}
                className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
              >
                {interest}
              </span>
            ))}
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">마지막 업데이트:</span>
          <span className="text-xs text-gray-500">
            {new Date(profile.updated_at).toLocaleDateString('ko-KR')}
          </span>
        </div>
      </div>
    </div>
  );
};

const LoadingSpinner: React.FC = () => (
  <div className="flex items-center justify-center py-12">
    <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
    <span className="ml-3 text-gray-600">뉴스를 불러오는 중...</span>
  </div>
);

const ErrorMessage: React.FC<{ message: string; onRetry: () => void }> = ({ message, onRetry }) => (
  <div className="text-center py-12">
    <AlertCircle className="mx-auto text-red-500 mb-4" size={48} />
    <p className="text-gray-600 mb-4">{message}</p>
    <button 
      onClick={onRetry}
      className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
    >
      다시 시도
    </button>
  </div>
);

const Header: React.FC<{ profile: UserProfile | null; onRefresh: () => void }> = ({ profile, onRefresh }) => (
  <header className="bg-white shadow-sm border-b">
    <div className="max-w-6xl mx-auto px-4 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Newspaper className="text-blue-500 mr-3" size={32} />
          <div>
            <h1 className="text-2xl font-bold text-gray-800">AI 뉴스 에이전트</h1>
            <p className="text-sm text-gray-600">개인화된 뉴스 요약 서비스</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          {profile && (
            <div className="text-right">
              <p className="text-sm font-medium text-gray-800">
                {profile.profile_type === 'personalized' ? '개인화 모드' : '기본 모드'}
              </p>
              <p className="text-xs text-gray-500">
                {profile.interests.length}개 관심사
              </p>
            </div>
          )}
          
          <button
            onClick={onRefresh}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 flex items-center"
          >
            <Settings size={16} className="mr-2" />
            새로고침
          </button>
        </div>
      </div>
    </div>
  </header>
);

// =============================================================================
// 메인 애플리케이션 컴포넌트 (조합 - Composition)
// =============================================================================

const NewsAgentApp: React.FC = () => {
  const { userId, profile, setProfile, fetchProfile } = useUserManager();
  const { cookieConsent, handleCookieConsent } = useCookieManager();
  const { news, loading, error, fetchNews } = useNewsManager();
  
  const [consentLoading, setConsentLoading] = useState(false);

  // 초기화 효과
  useEffect(() => {
    if (userId && cookieConsent !== null) {
      fetchProfile(userId);
      fetchNews(userId);
    }
  }, [userId, cookieConsent]);

  // 쿠키 동의 처리
  const handleConsentSubmit = async (consent: boolean) => {
    setConsentLoading(true);
    try {
      const result = await handleCookieConsent(userId, consent);
      if (result?.success) {
        await fetchProfile(userId);
        await fetchNews(userId);
      }
    } catch (error) {
      console.error('Consent handling error:', error);
    } finally {
      setConsentLoading(false);
    }
  };

  // 새로고침 처리
  const handleRefresh = () => {
    if (userId) {
      fetchNews(userId);
    }
  };

  // 에러 재시도 처리
  const handleRetry = () => {
    if (userId) {
      fetchNews(userId);
    }
  };

  // 쿠키 동의가 아직 처리되지 않았으면 모달 표시
  if (cookieConsent === null) {
    return (
      <div className="min-h-screen bg-gray-50">
        <CookieConsentModal 
          onConsent={handleConsentSubmit} 
          loading={consentLoading}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header profile={profile} onRefresh={handleRefresh} />
      
      <main className="max-w-6xl mx-auto px-4 py-6">
        <UserProfileCard profile={profile} />
        
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <Newspaper className="mr-2" size={24} />
            오늘의 뉴스 요약
            {profile?.profile_type === 'personalized' && (
              <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                맞춤형
              </span>
            )}
          </h2>
          
          {loading && <LoadingSpinner />}
          
          {error && (
            <ErrorMessage message={error} onRetry={handleRetry} />
          )}
          
          {!loading && !error && news.length === 0 && (
            <div className="text-center py-12">
              <Newspaper className="mx-auto text-gray-400 mb-4" size={48} />
              <p className="text-gray-600">표시할 뉴스가 없습니다.</p>
            </div>
          )}
          
          {!loading && !error && news.length > 0 && (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {news.map((item, index) => (
                <NewsCard key={index} news={item} />
              ))}
            </div>
          )}
        </div>
        
        {/* 개발자 정보 */}
        <footer className="mt-12 pt-6 border-t border-gray-200">
          <div className="text-center text-sm text-gray-500">
            <p className="mb-2">개인화된 AI 뉴스 에이전트 시스템</p>
            <p>개발: 헌빈솔호 | 지도교수: 이정일 | 업체: 그리드원</p>
            <p className="mt-2">
              SOLID 원칙 적용 • React + FastAPI + LangChain
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default NewsAgentApp;