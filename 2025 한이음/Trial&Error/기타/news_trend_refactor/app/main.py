from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import asyncio

from config import KEYWORD_PURPOSE_MAP, AD_KEYWORDS
from utils.clean_text import clean_text
from filters.ad_classifier import AdClassifier
from scraper.naver import crawl_news_links_by_keyword
from scraper.extractor import extract_article_text
from summarizer.chain import summary_chain, trend_chain
from evaluation.metrics import evaluate_summary

# ---- FastAPI ----
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class NewsTrendRequest(BaseModel):
    keyword: str
    enable_ad_filter: bool = True
    period: str = '1d'  # '1h','1d','1w','1m'
    max_articles: int = 5

# 광고 분류기 전역 인스턴스
ad_classifier = AdClassifier()

def map_keyword_to_purpose(keyword: str) -> str:
    for k, p in KEYWORD_PURPOSE_MAP.items():
        if k in keyword:
            return p
    return f"{keyword} 관련 뉴스 요약"

@app.post("/news_trend/")
async def news_trend(req: NewsTrendRequest):
    keyword = req.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword는 필수입니다.")

    purpose = map_keyword_to_purpose(keyword)

    links = await crawl_news_links_by_keyword(keyword, max_articles=req.max_articles, period=req.period)

    summaries: List[str] = []
    details: List[dict] = []

    for news in links:
        try:
            article = await extract_article_text(news['url'])
            cleaned = clean_text(article, 'KR')

            # 광고 필터
            is_ad_kw = any(k.lower() in cleaned.lower() for k in AD_KEYWORDS)
            is_ad_ml = ad_classifier.is_ad(cleaned) if req.enable_ad_filter else False
            if req.enable_ad_filter and (is_ad_kw or is_ad_ml):
                print(f"[INFO] 광고성 기사 제외: {news['title']}")
                continue

            summary_resp = await asyncio.to_thread(summary_chain.invoke, {"purpose": purpose, "article": cleaned})
            summary = clean_text(summary_resp.content)

            acc_scores = evaluate_summary(cleaned, summary, is_ad=(is_ad_kw or is_ad_ml))

        except Exception as e:
            summary = f"요약 실패: {str(e)}"
            acc_scores = {"rouge1": 0.0, "rougeL": 0.0, "bertscore": 0.0, "is_ad": False}

        summaries.append(summary)
        details.append({
            "title": news["title"],
            "url": news["url"],
            "summary": summary,
            "accuracy_scores": acc_scores
        })

    if not summaries:
        raise HTTPException(status_code=404, detail="필터링 후 요약할 기사가 없습니다.")

    combined = "\n".join(summaries)
    trend_resp = await asyncio.to_thread(trend_chain.invoke, {"purpose": purpose, "summaries": combined})
    trend_summary = clean_text(trend_resp.content)
    trend_acc_scores = evaluate_summary(combined, trend_summary)

    return {
        "keyword": keyword,
        "purpose": purpose,
        "trend_digest": trend_summary,
        "trend_accuracy_scores": trend_acc_scores,
        "trend_articles": details
    }
