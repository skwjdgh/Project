# -*- coding: utf-8 -*-
import re
import unicodedata

# 프로젝트 내 별칭 사전이 따로 있으면 여기로 합치거나, config에서 주입해도 됨.
ALIASES = {
    "가족관계증명서": ["가족관계", "가족 증명서", "가족증명서"],
    "건강보험자격득실확인서": ["자격득실확인서","건보 자격득실","건강보험 자격득실","자격득실"],
    "날씨": ["오늘날씨","일기예보","기상","날씨정보"],
    "등본": ["주민등록등본","주민 등본","주민등본","등본발급"],
    "초본": ["주민등록초본","주민 초본","주민초본","초본발급"],
    "축제": ["페스티벌"],
    "카테고리": ["분류","범주"],
    "행사": ["이벤트","행사정보"],
}

_ws_punct = re.compile(r"[\s\W_]+", re.UNICODE)

def _norm(s: str) -> str:
    if not s: return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    s = _ws_punct.sub("", s)
    return s

# GT의 모든 변형 형태(자기 자신 + 별칭들)를 정규화된 집합으로
def _forms(gt: str):
    canon = None
    gt_n = _norm(gt)
    for k, vs in ALIASES.items():
        if gt_n == _norm(k) or gt_n in {_norm(v) for v in vs}:
            canon = _norm(k)
            break
    if canon is None:
        canon = gt_n
    out = {canon}
    for v in ALIASES.get(gt, []):
        out.add(_norm(v))
    # 역인덱스(별칭으로 GT 들어온 케이스)
    for k, vs in ALIASES.items():
        if gt in vs:
            out.add(_norm(k))
    return out

def contains_with_alias(gt: str, text: str) -> bool:
    t = _norm(text)
    for f in _forms(gt):
        if f and f in t:
            return True
    return False

# ---- 토큰화(외부 모듈 있으면 사용, 없으면 폴백) ----
try:
    import MeCab  # type: ignore
    _mecab = MeCab.Tagger("")
except Exception:
    _mecab = None

_tok_split = re.compile(r"[^\w가-힣]+")

def _tokenize(s: str):
    s = (s or "").strip()
    if not s: return []
    if _mecab:
        try:
            node = _mecab.parseToNode(s)
            toks = []
            while node:
                w = node.surface
                if w:
                    toks.append(_norm(w))
                node = node.next
            return [t for t in toks if t]
        except Exception:
            pass
    # 폴백: 정규식 기반
    return [ _norm(t) for t in _tok_split.split(s) if _norm(t) ]

def tokens_match_with_alias(gt: str, text: str) -> bool:
    forms = _forms(gt)
    toks = set(_tokenize(text))
    if not toks: return False
    # 토큰 기반(정확/부분) 매칭만 — 완화 매칭 금지
    for f in forms:
        if f in toks:  # 정확 일치
            return True
        # 토큰 일부 포함(복합어 방지용 아주 얕게 허용)
        if any((f and f in t) for t in toks):
            return True
    return False
