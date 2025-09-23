# -*- coding: utf-8 -*-
"""
Condition 1 — Baseline
- 원음 그대로 STT 후, 정규화 문자열 부분일치로 평가.
- 평가 기준을 가장 단순화하여 다른 조건의 비교 기준선이 됨.
"""
from def_exception import TranscribeError
from Utility.Tokenizer.func_tokenizer import normalize_str

def _transcribe(model, audio_input, use_fp16: bool):
    """Whisper로 음성→텍스트. 실패 시 TranscribeError로 래핑."""
    try:
        result = model.transcribe(audio_input, fp16=use_fp16)
        return result.get("text","") or ""
    except Exception as e:
        raise TranscribeError(str(e))

def run(model, audio_path: str, ground_truth: str, cfg):
    """A: 원음 STT → GT(정답)과 부분문자열 비교."""
    text = _transcribe(model, audio_path, getattr(cfg,"USE_FP16",False))
    ok = 1 if normalize_str(ground_truth) in normalize_str(text) else 0
    return text, ok
