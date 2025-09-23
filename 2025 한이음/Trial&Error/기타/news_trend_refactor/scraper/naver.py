import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException


def is_valid_news_url(url: str) -> bool:
    return (
        url.startswith("http")
        and "news.naver.com" in url
        and "channelPromotion" not in url
        and "/static/" not in url
        and "/main/" not in url
        and "/special/" not in url
    )

async def crawl_news_links_by_keyword(keyword: str, max_articles: int = 5, period: str = '1d'):
    """네이버 뉴스에서 키워드로 검색하여 최신 기사 링크를 추출."""
    params = {
        'where': 'news',
        'query': keyword,
        'nso': f'so:r,p:{period},a:all'
    }
    search_url = "https://search.naver.com/search.naver"

    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
        res = await client.get(search_url, params=params)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

    links = []
    selectors = ['a.news_tit', 'a.tit']
    for selector in selectors:
        for a_tag in soup.select(selector):
            title = (a_tag.get("title", "").strip()) or a_tag.get_text(strip=True)
            href = a_tag.get("href", "").strip()
            if is_valid_news_url(href) and href not in [l['url'] for l in links]:
                links.append({"title": title, "url": href})
            if len(links) >= max_articles:
                break
        if len(links) >= max_articles:
            break

    if len(links) < max_articles:
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].strip()
            title = a_tag.get("title", "").strip() or a_tag.get_text(strip=True)
            if "news.naver.com" in href and href not in [l['url'] for l in links]:
                links.append({"title": title, "url": href})
            if len(links) >= max_articles:
                break

    if not links:
        raise HTTPException(status_code=404, detail=f"최근 기간 내 관련 뉴스 기사를 찾을 수 없습니다. (키워드: {keyword})")
    return links[:max_articles]
