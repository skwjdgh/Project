# -*- coding: utf-8 -*-

import math
import numpy as np
from pydub import AudioSegment, effects
import noisereduce as nr

import def_config as cfg

# ===== Config (safe defaults) =====
TARGET_SR               = int(getattr(cfg, "TARGET_SR", 16000))
TARGET_CHANNELS         = int(getattr(cfg, "TARGET_CHANNELS", 1))

HPF_CUTOFF_HZ           = int(getattr(cfg, "HPF_CUTOFF_HZ", 100))
LPF_CUTOFF_HZ           = int(getattr(cfg, "LPF_CUTOFF_HZ", 7000))
PREEMPHASIS             = float(getattr(cfg, "PREEMPHASIS", 0.97))

USE_WEBRTCVAD           = bool(getattr(cfg, "USE_WEBRTCVAD", True))
VAD_AGGR                = int(getattr(cfg, "VAD_AGGR", 2))
MIN_NOISE_SEC           = float(getattr(cfg, "MIN_NOISE_SEC", 0.5))
SNR_BYPASS_DB           = float(getattr(cfg, "SNR_BYPASS_DB", 12.0))

NR_PROP_DECREASE        = float(getattr(cfg, "NR_PROP_DECREASE", 0.65))
NR_STATIONARY           = bool(getattr(cfg, "NR_STATIONARY", False))
NR_WIN_SIZE             = int(getattr(cfg, "NR_WIN_SIZE", 2048))   # legacy name
NR_N_FFT                = int(getattr(cfg, "NR_N_FFT", NR_WIN_SIZE))
NR_HOP_LENGTH           = int(getattr(cfg, "NR_HOP_LENGTH", 512))
NR_FREQ_MASK_SMOOTH_HZ  = int(getattr(cfg, "NR_FREQ_MASK_SMOOTH_HZ", 600))
NR_TIME_MASK_SMOOTH_MS  = int(getattr(cfg, "NR_TIME_MASK_SMOOTH_MS", 64))

# Gating fine-tune (optional in def_config)
GATE_ATTN               = float(getattr(cfg, "GATE_ATTN", 0.40))   # attenuation for non-speech
SPEECH_GAIN             = float(getattr(cfg, "SPEECH_GAIN", 1.05)) # slight boost for speech

# optional VAD
try:
    import webrtcvad
    _VAD_OK = USE_WEBRTCVAD
except Exception:
    webrtcvad = None
    _VAD_OK = False


def _load_audio_segment(file_path: str) -> AudioSegment:
    return AudioSegment.from_file(file_path)


def _segment_to_float32(seg: AudioSegment) -> np.ndarray:
    seg = seg.set_sample_width(2)  # 16-bit
    samples = np.array(seg.get_array_of_samples()).astype(np.float32)
    samples /= np.iinfo(np.int16).max
    return samples


def _pre_emphasis(y: np.ndarray, coef: float = 0.97) -> np.ndarray:
    if y.size == 0:
        return y
    out = np.empty_like(y)
    out[0] = y[0]
    out[1:] = y[1:] - coef * y[:-1]  # bugfix: use y[1:] not y[1]
    return out


def _apply_band_filters(seg: AudioSegment) -> AudioSegment:
    if HPF_CUTOFF_HZ and HPF_CUTOFF_HZ > 0:
        seg = seg.high_pass_filter(HPF_CUTOFF_HZ)
    if LPF_CUTOFF_HZ and LPF_CUTOFF_HZ > 0:
        seg = seg.low_pass_filter(LPF_CUTOFF_HZ)
    return seg


def _frame_generator(y16k_bytes: bytes, frame_ms: int = 30):
    frame_bytes = int(TARGET_SR * (frame_ms / 1000.0)) * 2  # 16-bit mono
    for i in range(0, len(y16k_bytes), frame_bytes):
        chunk = y16k_bytes[i:i + frame_bytes]
        if len(chunk) == frame_bytes:
            yield chunk


def _vad_mask_float32(y: np.ndarray, frame_ms: int = 30) -> np.ndarray:
    """
    Returns boolean mask per-sample: True=speech, False=non-speech.
    Uses webrtcvad if available, else energy-based fallback.
    """
    if y.size == 0:
        return np.zeros(0, dtype=bool)

    if _VAD_OK and webrtcvad is not None:
        vad = webrtcvad.Vad(int(VAD_AGGR))
        y_clipped = np.clip(y, -1.0, 1.0)
        y_int16 = (y_clipped * 32767.0).astype(np.int16).tobytes()
        mask_frames = []
        for frame in _frame_generator(y_int16, frame_ms=frame_ms):
            mask_frames.append(vad.is_speech(frame, TARGET_SR))
        samples_per_frame = int(TARGET_SR * frame_ms / 1000)
        mask = np.repeat(mask_frames, samples_per_frame)
        if mask.size < y.size:
            pad_val = mask_frames[-1] if mask_frames else False
            mask = np.concatenate([mask, np.full(y.size - mask.size, pad_val, dtype=bool)])
        return mask[:y.size]

    # energy fallback
    win = max(1, int(TARGET_SR * 0.03))  # 30ms
    rms = np.sqrt(np.convolve(y ** 2, np.ones(win) / win, mode="same") + 1e-12)
    thr = np.quantile(rms, 0.2)
    return rms > max(thr, 1e-4)


def _smooth_and_dilate_mask(mask: np.ndarray, smooth_ms: int = 60, dilate_ms: int = 30) -> np.ndarray:
    """
    Smooth (debounce) and dilate around boundaries to preserve speech edges.
    """
    if mask.size == 0:
        return mask
    k1 = max(1, int(TARGET_SR * smooth_ms / 1000))  # smoothing window
    k2 = max(1, int(TARGET_SR * dilate_ms / 1000))  # dilation window
    smoothed = (np.convolve(mask.astype(float), np.ones(k1), mode="same") >= 0.5 * k1)
    dilated  = (np.convolve(smoothed.astype(float), np.ones(k2), mode="same") > 0)
    return dilated.astype(bool)


def _collect_noise_clip(y: np.ndarray, speech_mask: np.ndarray) -> np.ndarray:
    non_speech = ~speech_mask
    noise = y[non_speech]
    need = int(MIN_NOISE_SEC * TARGET_SR)
    if noise.size < need:
        win = max(1, int(TARGET_SR * 0.03))
        rms = np.sqrt(np.convolve(y ** 2, np.ones(win) / win, mode="same") + 1e-12)
        idx = np.argsort(rms)[: int(0.1 * y.size)]  # bottom 10%
        noise = np.concatenate([noise, y[np.sort(idx)]])
    return noise.astype(np.float32)


def _snr_estimate(y: np.ndarray, noise: np.ndarray) -> float:
    if y.size == 0 or noise.size == 0:
        return 0.0
    nvar = float(np.var(noise) + 1e-9)
    svar = float(np.var(y) + 1e-9)
    sig = max(svar - nvar, 1e-9)
    return 10.0 * math.log10(sig / nvar)


def enhance_speech_in_memory(file_path: str) -> np.ndarray:
    """
    Pure NC (self-tuning):
      1) VAD 마스크(스무딩/팽창) + 노이즈 프로파일, SNR 추정
      2) SNR 높거나 노이즈 샘플 부족 → BYPASS (원신호 스케일만 정리)
      3) 저 SNR에서만 pre-emphasis 후, 서로 다른 강도의 NR 후보들을 생성
      4) 말소리 보존·비음성 감쇠를 동시에 고려하는 오디오 지표로 베스트 후보 선택
         - 비음성 RMS 감쇠 ↑ (좋음)
         - 말소리 RMS 보존(≈1.0) 및 원신호와의 상관 ↑ (왜곡↓)
      5) 최종 스케일 정리
    """
    seg = _load_audio_segment(file_path)

    # 16k/mono 정규화
    if seg.frame_rate != TARGET_SR:
        seg = seg.set_frame_rate(TARGET_SR)
    if seg.channels != TARGET_CHANNELS:
        seg = seg.set_channels(TARGET_CHANNELS)

    # 밴드패스 + 라우드니스 정규화
    seg = _apply_band_filters(seg)
    seg = effects.normalize(seg)

    # float32 변환
    y = _segment_to_float32(seg)
    if y.size == 0:
        return y

    # --- VAD 마스크(스무딩/팽창) ---
    speech_mask = _vad_mask_float32(y, frame_ms=30)
    try:
        sm_fun = _smooth_and_dilate_mask  # 파일에 이미 있을 경우 사용
    except NameError:
        # 로컬 폴백
        def sm_fun(mask: np.ndarray, smooth_ms: int = 60, dilate_ms: int = 30) -> np.ndarray:
            if mask.size == 0:
                return mask
            k1 = max(1, int(TARGET_SR * smooth_ms / 1000))
            k2 = max(1, int(TARGET_SR * dilate_ms / 1000))
            sm  = (np.convolve(mask.astype(float), np.ones(k1), mode="same") >= 0.5 * k1)
            dl  = (np.convolve(sm.astype(float),   np.ones(k2), mode="same") > 0)
            return dl.astype(bool)
    speech_mask = sm_fun(speech_mask, smooth_ms=80, dilate_ms=40)

    # 노이즈 프로파일 & SNR
    noise_clip = _collect_noise_clip(y, speech_mask)
    need = int(MIN_NOISE_SEC * TARGET_SR)
    snr  = _snr_estimate(y, noise_clip) if noise_clip.size > 0 else 99.0

    # BYPASS: SNR 높거나 노이즈 샘플 부족 → 왜곡 방지
    if (snr >= SNR_BYPASS_DB) or (noise_clip.size < need):
        out = np.clip(y, -1.0, 1.0).astype(np.float32)
        pk = float(np.max(np.abs(out))) if out.size else 0.0
        if pk > 0:
            out *= 0.98 / pk
        return out

    # 저 SNR에서만 pre-emphasis
    y_proc = _pre_emphasis(y, PREEMPHASIS)

    # ===== 후보 생성 유틸 =====
    def _nr_version(y_in: np.ndarray, prop: float) -> np.ndarray:
        try:
            return nr.reduce_noise(
                y=y_in, sr=TARGET_SR, y_noise=noise_clip,
                stationary=NR_STATIONARY, prop_decrease=float(prop),
                n_fft=int(NR_N_FFT), hop_length=int(NR_HOP_LENGTH),
                freq_mask_smooth_hz=int(NR_FREQ_MASK_SMOOTH_HZ),
                time_mask_smooth_ms=int(NR_TIME_MASK_SMOOTH_MS),
            ).astype(np.float32)
        except TypeError:
            try:
                return nr.reduce_noise(
                    y=y_in, sr=TARGET_SR, y_noise=noise_clip,
                    stationary=NR_STATIONARY, prop_decrease=float(prop),
                    n_fft=int(NR_N_FFT), hop_length=int(NR_HOP_LENGTH),
                ).astype(np.float32)
            except TypeError:
                return nr.reduce_noise(
                    y=y_in, sr=TARGET_SR, y_noise=noise_clip,
                    stationary=NR_STATIONARY, prop_decrease=float(prop),
                ).astype(np.float32)

    def _rms(arr: np.ndarray, m: np.ndarray) -> float:
        if arr.size == 0 or m.size == 0 or not m.any():
            return 1e-9
        v = arr[m]
        return float(np.sqrt(np.mean(np.square(v)) + 1e-12))

    def _corr(a: np.ndarray, b: np.ndarray, m: np.ndarray) -> float:
        if a.size == 0 or b.size == 0 or m.size == 0 or not m.any():
            return 0.0
        x, y2 = a[m], b[m]
        x = x - np.mean(x)
        y2 = y2 - np.mean(y2)
        den = (np.linalg.norm(x) * np.linalg.norm(y2)) + 1e-9
        return float(np.dot(x, y2) / den)

    def _score_candidate(y_ref: np.ndarray, y_hat: np.ndarray, m_speech: np.ndarray) -> float:
        # 비음성 감쇠: 클수록 좋음(원/후 RMS 비율의 감소)
        rms_ns_ref = _rms(y_ref, ~m_speech)
        rms_ns_hat = _rms(y_hat, ~m_speech)
        ns_atten   = 1.0 - (rms_ns_hat / max(rms_ns_ref, 1e-9))  # 0~1

        # 말소리 보존: RMS 비율이 1.0에 가까울수록 좋음, 상관계수 높을수록 좋음
        rms_sp_ref = _rms(y_ref, m_speech)
        rms_sp_hat = _rms(y_hat, m_speech)
        sp_ratio   = rms_sp_hat / max(rms_sp_ref, 1e-9)
        sp_keep    = 1.0 - min(abs(sp_ratio - 1.0), 1.0)         # 0~1
        sp_corr    = ( _corr(y_ref, y_hat, m_speech) + 1.0 ) / 2.0  # -1~1 → 0~1

        # 가중 합산 (필요 시 def_config로 노출 가능)
        w_ns, w_keep, w_corr = 0.45, 0.30, 0.25
        return w_ns*ns_atten + w_keep*sp_keep + w_corr*sp_corr

    # ===== 서로 다른 강도의 후보 생성 (soft/base/hard) + 게이팅 조합 =====
    prop_base = float(NR_PROP_DECREASE)
    prop_soft = float(getattr(cfg, "NR_PROP_SOFT", max(0.50, prop_base * 0.9)))
    prop_hard = float(getattr(cfg, "NR_PROP_HARD", min(0.85, prop_base * 1.15)))

    gate_soft = float(getattr(cfg, "GATE_ATTN_SOFT", 0.45))
    gate_base = float(getattr(cfg, "GATE_ATTN",      0.40))
    gate_hard = float(getattr(cfg, "GATE_ATTN_HARD", 0.35))
    speech_blend = float(getattr(cfg, "SPEECH_BLEND", 0.70))
    speech_gain  = float(getattr(cfg, "SPEECH_GAIN",  1.03))

    # NR
    r_soft = _nr_version(y_proc, prop_soft)
    r_base = _nr_version(y_proc, prop_base)
    r_hard = _nr_version(y_proc, prop_hard)

    # 게이팅+블렌드 적용 함수
    def _mix(reduced: np.ndarray, gate_attn: float) -> np.ndarray:
        out = reduced.copy()
        if out.size == y.size and speech_mask.size == y.size:
            # 비음성 강감쇠
            out[~speech_mask] *= gate_attn
            # 말소리 왜곡 최소화: soft blend + 미세 gain
            out[speech_mask] = (
                speech_blend * out[speech_mask] + (1.0 - speech_blend) * y[speech_mask]
            ) * speech_gain
        return out

    cand = [
        _mix(r_soft, gate_soft),
        _mix(r_base, gate_base),
        _mix(r_hard, gate_hard),
    ]

    # 후보 스코어링
    scores = [ _score_candidate(y, c, speech_mask) for c in cand ]
    best   = cand[int(np.argmax(scores))]

    # 출력 스케일 정리
    best = np.clip(best, -1.0, 1.0).astype(np.float32)
    pk = float(np.max(np.abs(best))) if best.size else 0.0
    if pk > 0:
        best *= 0.98 / pk
    return best
