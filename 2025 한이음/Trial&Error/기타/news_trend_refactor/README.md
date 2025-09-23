# 뉴스 트렌드 요약 서비스 (Refactored)

FastAPI + LangChain(OpenAI) + ROUGE/BERTScore 평가 + 광고 필터링(ML) 기반의 한국어 뉴스 트렌드 요약 서비스 예시 구조입니다.

## 주요 변경점
- 모듈화/레이어 분리 (scraper, summarizer, filters, evaluation, utils)
- 광고 필터: 키워드 + Fine-tuned 모델 래퍼 (`filters/ad_classifier.py`)
- 요약 정확도 평가: ROUGE + BERTScore (`evaluation/metrics.py`)
- 이모지 제거/텍스트 정제 유틸 (`utils/clean_text.py`, `utils/emoji.py`)
- 비동기 HTTP 클라이언트(`httpx`) 사용
- Prompt 템플릿 분리 (`prompts/*.txt`)
- 설정/상수 (`config.py`)
- 테스트 스텁 (`tests/`)

> ⚠️ **법적 주의**: 네이버 뉴스 크롤링은 이용약관/robots.txt를 반드시 준수하십시오. 상업적 사용 금지, 과도한 요청 제한, 본문 저장 금지 등의 정책을 코드/운영 레벨에서 반영하세요.

## 빠른 시작

```bash
# 1) 환경 준비
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) 환경변수 설정
cp .env.example .env
# .env 에 OPENAI_API_KEY=... 입력

# 3) 실행
uvicorn app.main:app --reload --port 8000

# 4) 호출 예시
curl -X POST "http://localhost:8000/news_trend/" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "AI", "enable_ad_filter": true}'
```

## 디렉터리 구조

```
news_trend_refactor/
  README.md
  .env.example
  requirements.txt
  Dockerfile
  config.py
  prompts/
    summary_prompt.txt
    trend_prompt.txt
  utils/
    emoji.py
    clean_text.py
  filters/
    ad_classifier.py
  evaluation/
    metrics.py
  scraper/
    naver.py
    extractor.py
  summarizer/
    chain.py
  app/
    __init__.py
    main.py
  tests/
    test_utils.py
```

## TODO
- 광고 분류용 fine-tuned 모델 교체 (현재 distilbert-base-multilingual-cased dummy)
- 크롤링 rate limit / 캐시 / 예외 핸들링 강화
- BERTScore/lang 선택 자동화
- 테스트 케이스 확장
```
