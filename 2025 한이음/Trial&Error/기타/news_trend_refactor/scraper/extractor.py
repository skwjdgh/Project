import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

ARTICLE_SELECTORS = [
    ("div", {"id": "dic_area"}),
    ("article", {"id": "dic_area"}),
    ("div", {"class": "article_body"}),
    ("div", {"class": "article-text"}),
    ("div", {"class": "story-news"}),
]

async def extract_article_text(url: str) -> str:
    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
        res = await client.get(url)
        res.raise_for_status()
    soup = BeautifulSoup(res.content, "html.parser")

    for tag, attrs in ARTICLE_SELECTORS:
        node = soup.find(tag, attrs=attrs)
        if node:
            text = node.get_text(strip=True)
            if text:
                return text

    paragraphs = soup.find_all("p")
    if paragraphs:
        text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)
        if text:
            return text

    raise HTTPException(status_code=400, detail=f"본문 추출에 실패했습니다: {url}")
