# -*- coding: utf-8 -*-
"""
Tokenizer
- normalize_str: 대소문/공백/특수문자 제거, 비교 안정화
- tokenize_text: (가능시)MeCab으로 형태소 기반 토큰화, 실패시 정규식 폴백
- token_recall_match: 토큰 기반 recall 평가(퍼지 매칭 포함)
"""
import re
from typing import List
from difflib import SequenceMatcher
try:
    import MeCab
    _MECAB_OK = True
    _mecab_tagger = MeCab.Tagger()
except Exception:
    _MECAB_OK = False
    _mecab_tagger = None

def normalize_str(s: str) -> str:
    """소문자화 + 영숫자/한글만 남김 → 부분문자열 비교용 정규화 문자열."""
    s = s.lower()
    s = re.sub(r'[^0-9a-z가-힣]', '', s)
    return s

def regex_fallback_tokens(text: str) -> List[str]:
    """형태소 분석 실패 시, 한글/영숫자 토큰을 정규식으로 추출."""
    if not text: return []
    return re.findall(r'[가-힣]+|[a-zA-Z0-9]+', text)

def tokenize_text(text: str) -> List[str]:
    """
    텍스트를 토큰 리스트로 변환.
    - MeCab 사용 시: 명사/용언/외래어 등 의미있는 품사만 선별
    - 폴백: 정규식 단어 단위
    """
    if not text: return []
    if not _MECAB_OK or _mecab_tagger is None:
        return regex_fallback_tokens(text)
    kept=[]
    try:
        parsed=_mecab_tagger.parse(text).splitlines()
        for line in parsed:
            if line=="EOS": break
            try:
                word, feats = line.split("\t")
                pos = feats.split(",")[0]
                # 명사류/용언/어근/영문/기호 일부만 유지
                if pos.startswith('N') or pos in ('VV','VA','XR','SL','SH'):
                    kept.append(word)
            except ValueError:
                continue
    except Exception:
        return regex_fallback_tokens(text)
    # 순서 보존 중복 제거
    seen=set(); out=[]
    for t in kept:
        if t not in seen:
            seen.add(t); out.append(t)
    return out

def _fuzzy_eq(a: str, b: str, min_ratio: float) -> bool:
    """퍼지(시퀀스 유사도) 비교: 임계 이상이면 동일로 간주."""
    if not a or not b: return False
    return SequenceMatcher(None, a, b).ratio() >= min_ratio

def token_recall_match(required_tokens, found_tokens, min_recall: float=0.6, fuzzy_ratio: float=0.86) -> int:
    """
    토큰 recall 평가:
    - required 토큰 집합 대비 발견 토큰 집합의 (퍼지 포함) recall이 임계 이상이면 1
    - 아니면 0
    """
    req_norm=[normalize_str(t) for t in required_tokens]; req_norm=[t for t in req_norm if t]
    found_norm={normalize_str(t) for t in found_tokens if t}
    if not req_norm: return 0
    hit=0
    for t in req_norm:
        if t in found_norm: hit+=1
        else:
            if any(_fuzzy_eq(t,f,fuzzy_ratio) for f in found_norm): hit+=1
    recall = hit/len(req_norm)
    return 1 if recall>=min_recall else 0
