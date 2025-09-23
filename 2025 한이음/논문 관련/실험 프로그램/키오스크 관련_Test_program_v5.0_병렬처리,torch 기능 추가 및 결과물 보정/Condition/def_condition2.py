# -*- coding: utf-8 -*-
import re
from def_exception import TranscribeError

# ---------- 공통 유틸 ----------
def _norm(s: str) -> str:
    if s is None: return ""
    s = str(s).lower().strip()
    s = re.sub(r"[^0-9a-z가-힣\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s

def _nospace(s: str) -> str:
    return re.sub(r"\s+", "", s or "")

def _aliases(cfg):
    return getattr(cfg, "KEYWORD_ALIASES", {}) or {}

def _baseline_include(hyp: str, gt: str) -> bool:
    # A와 동일: 공백 무시 포함 매칭(별칭 X)
    return _nospace(gt) in _nospace(hyp)

def _apply_alias(text: str, cfg) -> str:
    t = _norm(text)
    for canon, syns in _aliases(cfg).items():
        for w in ([canon] + list(syns)):
            wn = _norm(w)
            t = t.replace(wn, canon)
            t = _norm(_nospace(t).replace(_nospace(wn), canon))
    return t

def _alias_include(hyp: str, gt: str, cfg) -> bool:
    hyp2 = _apply_alias(hyp, cfg)
    gt2  = _apply_alias(gt,  cfg)
    return _nospace(gt2) in _nospace(hyp2)

def _tokenize_safe(text: str, cfg):
    try:
        import func_tokenizer as ft
    except Exception:
        try:
            from Utility import func_tokenizer as ft
        except Exception:
            ft = None
    if ft:
        try:
            return list(ft.tokenize(text, cfg))
        except TypeError:
            return list(ft.tokenize(text))
        except Exception:
            pass
    return [t for t in re.split(r"\s+", _norm(text)) if t]

def _token_match(hyp: str, gt: str, cfg) -> bool:
    hyp2 = _apply_alias(hyp, cfg)
    gt2  = _apply_alias(gt,  cfg)
    htok = set(_tokenize_safe(hyp2, cfg))
    gtok = set(_tokenize_safe(gt2,  cfg))
    return len(htok & gtok) > 0
# --------------------------------

def _transcribe(model, audio_input, fp16: bool):
    try:
        result = model.transcribe(audio_input, fp16=fp16)
        return (result.get("text") or "").strip()
    except Exception as e:
        raise TranscribeError(str(e))

def run(model, audio_path: str, gt: str, cfg):
    """
    B: 원본 오디오 -> STT -> (A기준 포함) or (별칭 포함) or (토큰 교집합)
    """
    fp16 = bool(getattr(cfg, "USE_FP16", False))
    text = _transcribe(model, audio_path, fp16)

    if _baseline_include(text, gt):               # A와 동일 기준 먼저
        return text, 1
    if _alias_include(text, gt, cfg):             # 별칭 포함
        return text, 1
    return text, int(_token_match(text, gt, cfg)) # 토큰 교집합
