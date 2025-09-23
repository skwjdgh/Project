# -*- coding: utf-8 -*-
import re
from def_exception import TranscribeError
from Utility.func_keyword_alias import contains_with_alias  # 별칭 포함 매칭

def _transcribe(model, audio_input, fp16: bool):
    try:
        result = model.transcribe(audio_input, fp16=fp16)
        return (result.get("text") or "").strip()
    except Exception as e:
        raise TranscribeError(str(e))

def run(model, audio_path: str, gt_keyword: str, cfg):
    fp16 = bool(getattr(cfg, "USE_FP16", False))
    text = _transcribe(model, audio_path, fp16)
    match = contains_with_alias(gt_keyword, text)
    return text, bool(match)
