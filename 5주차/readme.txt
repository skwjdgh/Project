# =============================================================================
# requirements.txt - Python 백엔드 의존성
# =============================================================================
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
langchain==0.0.350
openai==1.3.0
requests==2.31.0
python-dotenv==1.0.0

# =============================================================================
# package.json - React 프론트엔드 의존성
# =============================================================================
# {
#   "name": "ai-news-agent-frontend",
#   "version": "1.0.0",
#   "private": true,
#   "dependencies": {
#     "react": "^18.2.0",
#     "react-dom": "^18.2.0",
#     "react-scripts": "5.0.1",
#     "tailwindcss": "^3.3.0",
#     "lucide-react": "^0.294.0",
#     "@types/react": "^18.2.0",
#     "@types/react-dom": "^18.2.0",
#     "typescript": "^4.9.0"
#   },
#   "scripts": {
#     "start": "react-scripts start",
#     "build": "react-scripts build",
#     "test": "react-scripts test",
#     "eject": "react-scripts eject"
#   },
#   "eslintConfig": {
#     "extends": [
#       "react-app",
#       "react-app/jest"
#     ]
#   },
#   "browserslist": {
#     "production": [
#       ">0.2%",
#       "not dead",
#       "not op_mini all"
#     ],
#     "development": [
#       "last 1 chrome version",
#       "last 1 firefox version",
#       "last 1 safari version"
#     ]
#   },
#   "proxy": "http://localhost:8000"
# }

# =============================================================================
# .env - 환경 변수 설정 (백엔드용)
# =============================================================================
# OPENAI_API_KEY=your_openai_api_key_here
# NEWS_API_KEY=your_news_api_key_here
# ENVIRONMENT=development
# LOG_LEVEL=INFO

# =============================================================================
# tailwind.config.js - Tailwind CSS 설정
# =============================================================================
# /** @type {import('tailwindcss').Config} */
# module.exports = {
#   content: [
#     "./src/**/*.{js,jsx,ts,tsx}",
#   ],
#   theme: {
#     extend: {},
#   },
#   plugins: [],
# }

# =============================================================================
# 프로젝트 폴더 구조
# =============================================================================

# ai-news-agent/
# ├── backend/
# │   ├── main.py                    # FastAPI 메인 애플리케이션
# │   ├── requirements.txt           # Python 의존성
# │   ├── .env                       # 환경 변수
# │   ├── profiles/                  # 사용자 프로파일 저장 폴더
# │   └── logs/                      # 로그 파일 폴더
# ├── frontend/
# │   ├── public/
# │   │   └── index.html
# │   ├── src/
# │   │   ├── App.tsx                # 메인 React 컴포넌트
# │   │   ├── index.tsx              # React 진입점
# │   │   └── index.css              # Tailwind CSS 임포트
# │   ├── package.json               # Node.js 의존성
# │   └── tailwind.config.js         # Tailwind 설정
# ├── README.md                      # 프로젝트 설명서
# └── docker-compose.yml             # Docker 설정 (선택사항)

# =============================================================================
# 프로젝트 초기 설정 스크립트
# =============================================================================

#!/bin/bash

# 프로젝트 폴더 생성
mkdir -p ai-news-agent/{backend,frontend}
cd ai-news-agent

echo "🚀 AI 뉴스 에이전트 시스템 설정을 시작합니다..."

# =============================================================================
# 백엔드 설정
# =============================================================================

echo "📦 백엔드 설정 중..."
cd backend

# Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
langchain==0.0.350
openai==1.3.0
requests==2.31.0
python-dotenv==1.0.0
EOF

pip install -r requirements.txt

# 환경 변수 파일 생성
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
NEWS_API_KEY=your_news_api_key_here
ENVIRONMENT=development
LOG_LEVEL=INFO
EOF

# 필요한 폴더 생성
mkdir -p profiles logs

echo "✅ 백엔드 설정 완료!"

# =============================================================================
# 프론트엔드 설정
# =============================================================================

echo "🎨 프론트엔드 설정 중..."
cd ../frontend

# React 앱 생성 (Create React App 사용)
npx create-react-app . --template typescript

# Tailwind CSS 설치
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Lucide React 아이콘 설치
npm install lucide-react

# Tailwind 설정 파일 수정
cat > tailwind.config.js << EOF
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF

# CSS 파일 수정
cat > src/index.css << EOF
@tailwind base;
@tailwind components;
@tailwind utilities;

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
EOF

echo "✅ 프론트엔드 설정 완료!"

# =============================================================================
# README.md 생성
# =============================================================================

cd ..
cat > README.md << EOF
# 개인화된 AI 뉴스 에이전트 시스템

## 프로젝트 개요
- **개발자**: 헌빈솔호
- **지도교수**: 이정일
- **업체**: 그리드원
- **목적**: 쿠키 기반 개인화 뉴스 요약 서비스

## 기술 스택
### 백엔드
- **Python 3.10+**
- **FastAPI**: REST API 서버
- **LangChain**: AI 체인 구성
- **OpenAI API**: 뉴스 요약 및 재질의
- **Pydantic**: 데이터 검증

### 프론트엔드
- **React 18 + TypeScript**
- **Tailwind CSS**: 반응형 디자인
- **Lucide React**: 아이콘 시스템

## SOLID 원칙 적용
1. **SRP (단일 책임 원칙)**: 각 클래스와 컴포넌트가 하나의 책임만 가짐
2. **OCP (개방-폐쇄 원칙)**: 확장에는 열려있고 수정에는 닫힌 구조
3. **LSP (리스코프 치환 원칙)**: 인터페이스 기반 구현으로 치환 가능
4. **ISP (인터페이스 분리 원칙)**: 필요한 기능만 포함하는 인터페이스
5. **DIP (의존성 역전 원칙)**: 추상화에 의존하는 의존성 주입 구조

## 설치 및 실행

### 사전 요구사항
- Python 3.10+
- Node.js 16+
- npm 또는 yarn

### 백엔드 실행
\`\`\`bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### 프론트엔드 실행
\`\`\`bash
cd frontend
npm install
npm start
\`\`\`

### 접속
- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 주요 기능
1. **쿠키 기반 개인화**: 사용자 행동 패턴 분석
2. **AI 뉴스 요약**: LangChain + OpenAI를 통한 지능형 요약
3. **재질의 검증**: AI를 통한 요약 정확성 검증
4. **반응형 UI**: 모든 디바이스 지원
5. **실시간 업데이트**: 3시간 주기 자동 갱신

## 테스트
### 백엔드 테스트
\`\`\`bash
cd backend
pytest tests/
\`\`\`

### 프론트엔드 테스트
\`\`\`bash
cd frontend
npm test
\`\`\`

## API 엔드포인트
- \`POST /api/cookie-consent\`: 쿠키 사용 동의 처리
- \`POST /api/news-summary\`: 개인화된 뉴스 요약 조회
- \`GET /api/profile/{user_id}\`: 사용자 프로파일 조회
- \`GET /api/health\`: 헬스 체크

## 개발 가이드라인
1. **코드 품질**: 타입 힌트, 문서화 주석 필수
2. **보안**: 개인정보 비저장, GDPR 준수
3. **성능**: 응답 시간 5초 이내 목표
4. **테스트**: 코드 커버리지 80% 이상

## 라이선스
교육용 프로젝트 - 상업적 사용 금지

## 문의
- 이메일: [개발자 이메일]
- GitHub: [레포지토리 URL]
EOF

echo "📚 README.md 생성 완료!"

# =============================================================================
# 실행 스크립트들 생성
# =============================================================================

# 백엔드 실행 스크립트
cat > backend/run.sh << EOF
#!/bin/bash
echo "🚀 백엔드 서버를 시작합니다..."
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
EOF

chmod +x backend/run.sh

# 프론트엔드 실행 스크립트
cat > frontend/run.sh << EOF
#!/bin/bash
echo "🎨 프론트엔드 서버를 시작합니다..."
npm start
EOF

chmod +x frontend/run.sh

# 전체 실행 스크립트 (개발용)
cat > start-dev.sh << EOF
#!/bin/bash
echo "🔧 개발 서버들을 시작합니다..."

# 백엔드 서버 백그라운드 실행
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=\$!

# 잠시 대기 (백엔드 서버 시작 시간)
sleep 3

# 프론트엔드 서버 실행
cd ../frontend
npm start &
FRONTEND_PID=\$!

echo "✅ 서버 시작 완료!"
echo "📱 프론트엔드: http://localhost:3000"
echo "🔧 백엔드: http://localhost:8000"
echo "📖 API 문서: http://localhost:8000/docs"
echo ""
echo "종료하려면 Ctrl+C를 누르세요."

# Ctrl+C 처리
trap 'kill \$BACKEND_PID \$FRONTEND_PID; exit' INT

# 대기
wait
EOF

chmod +x start-dev.sh

echo "🎉 프로젝트 설정이 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. backend/.env 파일에서 API 키 설정"
echo "2. ./start-dev.sh 실행으로 개발 서버 시작"
echo "3. http://localhost:3000 에서 애플리케이션 확인"
echo ""
echo "📁 프로젝트 구조:"
echo "ai-news-agent/"
echo "├── backend/           # FastAPI 백엔드"
echo "├── frontend/          # React 프론트엔드"  
echo "├── README.md         # 프로젝트 문서"
echo "└── start-dev.sh      # 개발 서버 실행 스크립트"

# =============================================================================
# Docker 설정 (선택사항)
# =============================================================================

cat > docker-compose.yml << EOF
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    volumes:
      - ./backend/profiles:/app/profiles
      - ./backend/logs:/app/logs
    depends_on:
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
EOF

echo "🐳 Docker 설정 파일도 생성되었습니다!"

# =============================================================================
# 테스트 파일 템플릿 생성
# =============================================================================

mkdir -p backend/tests frontend/src/__tests__

# 백엔드 테스트 템플릿
cat > backend/tests/test_main.py << EOF
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_cookie_consent():
    response = client.post("/api/cookie-consent", json={
        "user_id": "test_user",
        "consent_given": True,
        "cookie_data": {"test": "data"}
    })
    assert response.status_code == 200

def test_news_summary():
    response = client.post("/api/news-summary", json={
        "user_id": "test_user"
    })
    assert response.status_code == 200
    assert isinstance(response.json(), list)
EOF

echo "✅ 모든 설정이 완료되었습니다!"
echo "이제 프로젝트를 시작할 수 있습니다. 행운을 빌어요! 🍀"