# -*- coding: utf-8 -*-
"""
Condition C: Improved Noise Cancellation only (no token/dict)
- ffmpeg 기반 (librosa/resampy 미사용)
- Adaptive bypass by duration & spectral flatness
- anlmdn 사용, 실패 시 afftdn 폴백
- 반환: (recognized_text, match_int)  # match: 정규화 후 '포함' 매칭
"""

from __future__ import annotations
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from typing import Tuple

import torch

try:
    from def_exception import TranscribeError, ProcessError
except Exception:
    class TranscribeError(Exception): ...
    class ProcessError(Exception): ...

# ---------------------------
# 텍스트 정규화 & 포함 매칭 (A와 동일한 평가형식)
# ---------------------------
_HANGUL_PAT = re.compile(r"[^가-힣0-9a-zA-Z]+", re.UNICODE)

def _norm(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip().lower()
    s = s.replace(" ", "")
    return _HANGUL_PAT.sub("", s)

def _contain_match(recognized_text: str, gt_label: str) -> int:
    return 1 if _norm(gt_label) in _norm(recognized_text) else 0

# ---------------------------
# ffmpeg 유틸
# ---------------------------
def _have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None

def _probe_duration(path: str) -> float:
    try:
        out = subprocess.check_output(
            ["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1", path],
            stderr=subprocess.STDOUT
        )
        return float(out.decode("utf-8","ignore").strip())
    except Exception:
        return 0.0

_ASTATS_FLAT_RE = re.compile(r"Overall\s+Flatness:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)
def _measure_flatness(path: str) -> float:
    """
    ffmpeg astats로 전체 스펙트럼 평탄도(0~1, 1에 가까울수록 잡음형) 추정.
    실패 시 -1 반환하여 '정보 없음'으로 처리.
    """
    try:
        # astats는 stderr로 출력됨
        cmd = [
            "ffmpeg", "-hide_banner", "-nostats",
            "-i", path, "-af", "astats=metadata=1:reset=1",
            "-f", "null", "-"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, err = proc.communicate()
        text = err.decode("utf-8","ignore")
        m = _ASTATS_FLAT_RE.search(text)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return -1.0

def _try_ffmpeg_chain(in_path: str, af_chain: str, sr: int) -> str:
    out_wav = os.path.join(tempfile.gettempdir(), f"nc_{uuid.uuid4().hex}.wav")
    cmd = [
        "ffmpeg","-y","-i", in_path,
        "-ac","1","-af", af_chain,"-ar", str(sr),
        out_wav
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(out_wav) or os.path.getsize(out_wav)==0:
        raise ProcessError("ffmpeg 출력이 비어있음")
    return out_wav

def _denoise_adaptive(in_path: str, target_sr: int, cfg=None) -> str:
    """
    적응형 NC:
      - 짧은 발화 우회
      - 평탄도 기반 필요 시에만 NC
      - anlmdn 시도 → 실패 시 afftdn 폴백
    """
    if not _have_ffmpeg():
        raise ProcessError("ffmpeg/ffprobe 미탑재")

    # 1) 우회 규칙
    dur = _probe_duration(in_path)
    bypass_sec = float(getattr(cfg, "C_BYPASS_SEC", 0.9))
    if dur>0 and dur<bypass_sec:
        # 우회: 리샘플만
        return _try_ffmpeg_chain(in_path, f"aresample={target_sr}", target_sr)

    # 2) 평탄도 측정
    flat = _measure_flatness(in_path)
    flat_th = float(getattr(cfg, "C_FLATNESS_TH", 0.58))  # 높을수록 잡음형
    need_nc = (flat < 0) or (flat >= flat_th)  # 측정 실패면 보수적으로 NC 수행

    if not need_nc:
        # 깨끗한 음성: 모노+리샘플만
        return _try_ffmpeg_chain(in_path, f"aresample={target_sr}", target_sr)

    # 3) 보수적 파라미터 구성
    hp = int(getattr(cfg, "C_BANDPASS_LOW", 80))
    lp = int(getattr(cfg, "C_BANDPASS_HIGH", 6000))
    # anlmdn은 보통 말소리 보존력이 좋음. 없으면 afftdn 폴백
    anlmdn_s = float(getattr(cfg, "C_ANLMDN_S", 0.002))  # step
    anlmdn_p = float(getattr(cfg, "C_ANLMDN_P", 0.02))   # nu
    anlmdn_o = int(getattr(cfg, "C_ANLMDN_O", 15))       # order
    # afftdn nf(dB) 값은 절대 너무 낮게 하지 않음(말 훼손 방지)
    afftdn_nf = int(getattr(cfg, "C_AFFTDN_NF_DB", -23))
    # 다이내믹 노멀라이즈(너무 작게 녹음된 파일 보정)
    dyn = f"dynaudnorm=f=150:g=5"

    # 4) anlmdn → afftdn 폴백
    chain_try = [
        f"highpass=f={hp},lowpass=f={lp},anlmdn=s={anlmdn_s}:p={anlmdn_p}:o={anlmdn_o},{dyn},aresample={target_sr}",
        f"highpass=f={hp},lowpass=f={lp},afftdn=nf={afftdn_nf},{dyn},aresample={target_sr}",
    ]
    last_err = None
    for af in chain_try:
        try:
            return _try_ffmpeg_chain(in_path, af, target_sr)
        except subprocess.CalledProcessError as e:
            last_err = e
            continue
    raise ProcessError(f"ffmpeg NC 실패: {last_err}")

# ---------------------------
# Whisper
# ---------------------------
def _whisper(model, audio, fp16: bool) -> str:
    try:
        result = model.transcribe(audio, fp16=fp16)
        return (result.get("text") or "").strip()
    except Exception as e:
        raise TranscribeError(str(e))

# ---------------------------
# 메인
# ---------------------------
def run(model, audio_path: str, gt_label: str, cfg=None) -> Tuple[str, int]:
    if not os.path.exists(audio_path):
        raise ProcessError(f"오디오 파일 없음: {audio_path}")

    # CUDA일 때만 fp16
    try:
        device = next(model.parameters()).device
    except Exception:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_fp16 = bool(getattr(cfg, "USE_FP16", False) and device.type == "cuda")

    tmp = None
    try:
        tmp = _denoise_adaptive(audio_path, 16000, cfg)
        text = _whisper(model, tmp, fp16=use_fp16)
        match = _contain_match(text, gt_label)   # A와 동일한 '포함' 매칭
        return text, int(match)
    finally:
        if tmp and os.path.exists(tmp):
            try: os.remove(tmp)
            except: pass
