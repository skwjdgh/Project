# -*- coding: utf-8 -*-
"""
Condition 3 — Noise Cancellation
- 순수 NC 파이프라인(Utility.Noisecanceller)을 적용한 뒤, A와 동일한 방식으로 STT/평가.
- 디코딩 옵션을 바꾸지 않으므로 '노이즈캔슬링만 다름'을 보장.
"""
from def_exception import TranscribeError
from Utility.Noisecanceller.func_noisecanceller import enhance_speech_in_memory
from Utility.Tokenizer.func_tokenizer import normalize_str

def _transcribe(model, audio_input, use_fp16: bool):
    """Whisper로 음성→텍스트. 실패 시 TranscribeError로 래핑."""
    try:
        result = model.transcribe(audio_input, fp16=use_fp16)
        return result.get("text","") or ""
    except Exception as e:
        raise TranscribeError(str(e))

def run(model, audio_path: str, ground_truth: str, cfg, *, base_text: str|None=None):
    """C: NC 후 STT(동일 디코더) → 부분 문자열 비교."""
    enhanced = enhance_speech_in_memory(audio_path)
    text_c = base_text if enhanced is None or getattr(enhanced,"size",0)==0 else _transcribe(model, enhanced, getattr(cfg,"USE_FP16",False))
    ok = 1 if normalize_str(ground_truth) in normalize_str(text_c) else 0
    return text_c, ok
