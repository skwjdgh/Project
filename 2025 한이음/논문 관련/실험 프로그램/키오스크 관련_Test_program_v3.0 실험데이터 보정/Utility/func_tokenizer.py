# -*- coding: utf-8 -*-

import re
from typing import List
from difflib import SequenceMatcher

# MeCab 사용 가능하면 활용, 불가하면 정규식 폴백
try:
    import MeCab  # type: ignore
    _MECAB_OK = True
    _mecab_tagger = MeCab.Tagger()
except Exception:
    _MECAB_OK = False
    _mecab_tagger = None


def normalize_str(s: str) -> str:
    """
    비교 일관성을 높이는 강한 정규화:
      - 소문자화
      - 한글/영문/숫자만 남김
    """
    s = s.lower()
    s = re.sub(r'[^0-9a-z가-힣]', '', s)
    return s


def regex_fallback_tokens(text: str) -> List[str]:
    """공백 분할 대신 '한글/영문/숫자 블록'으로 안전한 폴백."""
    if not text:
        return []
    return re.findall(r'[가-힣]+|[a-zA-Z0-9]+', text)


def tokenize_text(text: str) -> List[str]:
    """
    품사 기반 토큰화(가능 시 MeCab 사용) + 안전 폴백.
      - 유지 품사: 명사(N*), 동/형용사(VV/VA), 어근(XR), 외국어/한자(SL/SH)
      - 중복 제거: 입력 순서 보존
    """
    if not text:
        return []
    if not _MECAB_OK or _mecab_tagger is None:
        return regex_fallback_tokens(text)

    kept = []
    try:
        parsed = _mecab_tagger.parse(text).splitlines()
        for line in parsed:
            if line == "EOS":
                break
            try:
                word, feats = line.split("\t")
                pos = feats.split(",")[0]
                if pos.startswith('N') or pos in ('VV', 'VA', 'XR', 'SL', 'SH'):
                    kept.append(word)
            except ValueError:
                continue
    except Exception:
        return regex_fallback_tokens(text)

    # 순서 유지하며 중복 제거
    seen = set()
    out = []
    for t in kept:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _fuzzy_eq(a: str, b: str, min_ratio: float) -> bool:
    if not a or not b:
        return False
    return SequenceMatcher(None, a, b).ratio() >= min_ratio


def token_recall_match(
    required_tokens,
    found_tokens,
    min_recall: float = 0.6,
    fuzzy_ratio: float = 0.86
) -> int:
    """
    "모든 토큰 일치" 대신 "부분 일치(리콜 임계치)".
    - 정규화된 required 토큰 중, found에 (정확/퍼지) 포함되는 비율이 min_recall 이상이면 1.
    - fuzzy_ratio는 철자/형태 변이 흡수를 위한 시퀀스 유사도 하한.
    """
    req_norm = [normalize_str(t) for t in required_tokens]
    req_norm = [t for t in req_norm if t]
    found_norm = {normalize_str(t) for t in found_tokens if t}

    if not req_norm:
        return 0

    hit = 0
    for t in req_norm:
        if t in found_norm:
            hit += 1
        else:
            # 퍼지 일치 허용
            if any(_fuzzy_eq(t, f, fuzzy_ratio) for f in found_norm):
                hit += 1

    recall = hit / len(req_norm)
    return 1 if recall >= min_recall else 0
