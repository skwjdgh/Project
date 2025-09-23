# -*- coding: utf-8 -*-
"""
Condition 4 — Tokenization + NC
- C의 텍스트를 사용하되, A의 토큰과 유니온한 뒤 B와 동일 매칭 로직 적용.
- 실전에서 가장 강건(일반적으로 B보다 높은 정확도).
"""
from Utility.Tokenizer.func_tokenizer import tokenize_text
from Condition.def_condition2 import _advanced_match

def run(model, audio_path: str, ground_truth: str, cfg, *, text_a: str|None=None, text_c: str|None=None) -> int:
    """D: 토큰 유니온(A∪C) + 동의어 OR 매칭."""
    aliases = getattr(cfg,"KEYWORD_ALIASES",{}).get(ground_truth,[])
    all_kw = [ground_truth]+aliases
    tok_a = tokenize_text(text_a or "")
    tok_c = tokenize_text(text_c or "")
    tokens = (list(dict.fromkeys(tok_a+tok_c)) if getattr(cfg,"USE_D_UNION_TOKENS",True) else tok_c)
    for kw in all_kw:
        if _advanced_match(tokenize_text(kw), tokens, kw, text_c or "", cfg):
            return 1
    return 0
