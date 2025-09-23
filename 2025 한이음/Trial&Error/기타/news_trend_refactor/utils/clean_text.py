import re
from .emoji import strip_emoji

def clean_text(text: str, lang: str = 'KR') -> str:
    """기본적인 공백/이모지/특수문자 제거. 필요시 언어별 전처리 분기."""
    if not text:
        return ''
    text = strip_emoji(text)
    text = text.replace('\xa0', ' ')
    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
