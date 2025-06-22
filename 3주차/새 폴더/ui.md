sequenceDiagram
    participant User as 사용자
    participant Browser as 브라우저
    participant React as React 컴포넌트
    participant API as FastAPI 서버
    participant CSS as Tailwind CSS

    Note over User,CSS: UI 출력 모듈 프로세스 (데이터흐름도 기준)

    User->>Browser: 뉴스 요약 페이지 접속
    Browser->>React: React 앱 로드
    
    React->>React: 컴포넌트 초기화
    Note over React: useState, useEffect 훅 설정

    React->>API: GET /news/summary 요청
    Note right of React: 사용자 프로파일 기반 요청

    API-->>React: 뉴스 요약본 전달 (JSON)
    Note left of API: {summary, title, timestamp}

    React->>React: 상태 업데이트
    Note over React: setSummary(data.summary)

    React->>CSS: Tailwind 클래스 적용
    Note over CSS: 반응형 레이아웃<br/>p-4, max-w-xl, mx-auto

    React->>Browser: 가상 DOM 렌더링
    Note over React: JSX → HTML 변환

    Browser->>Browser: 실제 DOM 업데이트
    Note over Browser: 뉴스 요약본 화면 출력

    Browser-->>User: 개인화된 뉴스 요약 표시

    Note over User,CSS: 멀티 디바이스 대응

    alt 모바일 디바이스
        CSS->>CSS: 모바일 스타일 적용
        Note over CSS: text-sm, p-2, 세로 레이아웃
        Browser-->>User: 모바일 최적화 화면
    else 태블릿/PC
        CSS->>CSS: 데스크톱 스타일 적용
        Note over CSS: text-xl, p-4, 카드 레이아웃
        Browser-->>User: 데스크톱 최적화 화면
    end

    Note over User,CSS: 실시간 업데이트

    React->>API: 주기적 데이터 확인 (선택사항)
    alt 새로운 요약본 있음
        API-->>React: 업데이트된 요약본
        React->>Browser: 부분 재렌더링
        Browser-->>User: 실시간 요약 업데이트
    else 변경사항 없음
        Note over React: 기존 화면 유지
    end