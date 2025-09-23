# -*- coding: utf-8 -*-
"""
Condition 2 — Tokenization 매칭
- A의 STT 결과를 재사용(재STT 없음)
- 토큰화/동의어/퍼지 매칭/문자 n-그램 백스톱으로 강건한 매칭을 수행
"""
from typing import Iterable
from difflib import SequenceMatcher
from Utility.Tokenizer.func_tokenizer import tokenize_text, normalize_str

def _char_ngrams(s: str, n: int) -> set[str]:
    """문자 n-그램 집합 생성 (정규화 후). 문자열 유사도 백스톱용."""
    s = normalize_str(s)
    if len(s) < n: return {s} if s else set()
    return {s[i:i+n] for i in range(len(s)-n+1)}

def _jacc(a: Iterable[str], b: Iterable[str]) -> float:
    """자카드 유사도."""
    A,B=set(a),set(b)
    if not A and not B: return 1.0
    if not A or not B:  return 0.0
    return len(A&B)/len(A|B)

def _advanced_match(required_tokens, found_tokens, keyword_text, full_text, cfg) -> int:
    """
    앵커 토큰 가중치 + 퍼지 매칭 + 문자 n-그램 백스톱.
    - recall 임계 이상이면 1, 아니면 n-그램 유사도 백스톱으로 한 번 더 패스.
    """
    min_recall = getattr(cfg,"TOKEN_RECALL_MIN",0.50)
    fuzzy_ratio= getattr(cfg,"FUZZY_RATIO_MIN",0.84)
    topk       = getattr(cfg,"ANCHOR_TOPK",3)
    w_anchor   = getattr(cfg,"ANCHOR_WEIGHT",2.5)
    use_back   = getattr(cfg,"USE_CHARGRAM_BACKSTOP",True)
    ngram_n    = getattr(cfg,"CHARGRAM_N",3)
    ngram_min  = getattr(cfg,"CHARGRAM_MIN",0.16)

    req=[normalize_str(t) for t in required_tokens if normalize_str(t)]
    found={normalize_str(t) for t in found_tokens if normalize_str(t)}
    if not req: return 0
    anchors=set(sorted(req, key=len, reverse=True)[:max(1,topk)])

    def _hit(t:str)->bool:
        if t in found: return True
        return any(SequenceMatcher(None,t,f).ratio()>=fuzzy_ratio for f in found)

    w_hit=w_tot=0.0
    for t in req:
        w = w_anchor if t in anchors else 1.0
        w_tot+=w; w_hit+= w if _hit(t) else 0.0
    recall = (w_hit/w_tot) if w_tot else 0.0
    if recall>=min_recall: return 1

    if use_back:
        if _jacc(_char_ngrams(keyword_text,ngram_n), _char_ngrams(full_text,ngram_n))>=ngram_min:
            return 1
    return 0

def run(model, audio_path: str, ground_truth: str, cfg, *, base_text: str|None=None) -> int:
    """
    B: A의 텍스트를 입력으로 받음 → 동의어/변형어까지 포함한 OR 매칭.
    반환: 1/0 (정답 여부)
    """
    text = base_text if base_text is not None else ""
    aliases = getattr(cfg,"KEYWORD_ALIASES",{}).get(ground_truth,[])
    all_kw = [ground_truth]+aliases
    tokens = tokenize_text(text)
    for kw in all_kw:
        if _advanced_match(tokenize_text(kw), tokens, kw, text, cfg):
            return 1
    return 0
