# -*- coding: utf-8 -*-
"""
Noise Canceller (Pure NC, Self-tuning)
"""
import math, numpy as np
from pydub import AudioSegment, effects
import noisereduce as nr
import def_config as cfg

TARGET_SR = int(getattr(cfg,"TARGET_SR",16000))
TARGET_CHANNELS = int(getattr(cfg,"TARGET_CHANNELS",1))
HPF_CUTOFF_HZ = int(getattr(cfg,"HPF_CUTOFF_HZ",80))
LPF_CUTOFF_HZ = int(getattr(cfg,"LPF_CUTOFF_HZ",6500))
PREEMPHASIS = float(getattr(cfg,"PREEMPHASIS",0.97))
USE_WEBRTCVAD = bool(getattr(cfg,"USE_WEBRTCVAD",True))
VAD_AGGR = int(getattr(cfg,"VAD_AGGR",1))
MIN_NOISE_SEC = float(getattr(cfg,"MIN_NOISE_SEC",0.5))
SNR_BYPASS_DB = float(getattr(cfg,"SNR_BYPASS_DB",12.0))
NR_PROP_DECREASE = float(getattr(cfg,"NR_PROP_DECREASE",0.6))
NR_STATIONARY = bool(getattr(cfg,"NR_STATIONARY",False))
NR_WIN_SIZE = int(getattr(cfg,"NR_WIN_SIZE",1024))
NR_N_FFT = int(getattr(cfg,"NR_N_FFT",2048))
NR_HOP_LENGTH = int(getattr(cfg,"NR_HOP_LENGTH",512))
NR_FREQ_MASK_SMOOTH_HZ = int(getattr(cfg,"NR_FREQ_MASK_SMOOTH_HZ",600))
NR_TIME_MASK_SMOOTH_MS = int(getattr(cfg,"NR_TIME_MASK_SMOOTH_MS",64))
NR_PROP_SOFT = float(getattr(cfg,"NR_PROP_SOFT",0.55))
NR_PROP_HARD = float(getattr(cfg,"NR_PROP_HARD",0.80))
GATE_ATTN_SOFT = float(getattr(cfg,"GATE_ATTN_SOFT",0.45))
GATE_ATTN_HARD = float(getattr(cfg,"GATE_ATTN_HARD",0.35))
SPEECH_BLEND = float(getattr(cfg,"SPEECH_BLEND",0.70))
SPEECH_GAIN = float(getattr(cfg,"SPEECH_GAIN",1.03))

try:
    import webrtcvad
    _VAD_OK = USE_WEBRTCVAD
except Exception:
    webrtcvad=None; _VAD_OK=False

def _load_audio_segment(p): return AudioSegment.from_file(p)
def _segment_to_float32(seg):
    seg=seg.set_sample_width(2)
    x=np.array(seg.get_array_of_samples()).astype(np.float32)
    return x/np.iinfo(np.int16).max

def _pre_emphasis(y, coef=0.97):
    if y.size==0: return y
    out=y.copy(); out[1:]=y[1:]-coef*y[:-1]; return out

def _apply_band_filters(seg):
    if HPF_CUTOFF_HZ>0: seg=seg.high_pass_filter(HPF_CUTOFF_HZ)
    if LPF_CUTOFF_HZ>0: seg=seg.low_pass_filter(LPF_CUTOFF_HZ)
    return seg

def _frame_gen(y16k_bytes, ms=30):
    n=int(TARGET_SR*(ms/1000.0))*2
    for i in range(0,len(y16k_bytes),n):
        c=y16k_bytes[i:i+n]
        if len(c)==n: yield c

def _vad_mask_float32(y, frame_ms=30):
    if y.size==0: return np.zeros(0,bool)
    if _VAD_OK and webrtcvad is not None:
        mode = min(3, max(0, int(VAD_AGGR)))  # (중요) 범위 보정으로 드물게 발생하는 블로킹 방지
        vad=webrtcvad.Vad(mode)
        y16=(np.clip(y,-1,1)*32767.0).astype(np.int16).tobytes()
        frames=[vad.is_speech(fr, TARGET_SR) for fr in _frame_gen(y16, frame_ms)]
        spf=int(TARGET_SR*frame_ms/1000)
        mask=np.repeat(frames, spf)
        if mask.size<y.size:
            pad = frames[-1] if frames else False
            mask=np.concatenate([mask, np.full(y.size-mask.size,pad,bool)])
        return mask[:y.size]
    # energy fallback
    win=max(1,int(TARGET_SR*0.03))
    rms=np.sqrt(np.convolve(y**2, np.ones(win)/win, mode="same")+1e-12)
    thr=float(np.quantile(rms,0.2))
    return rms>max(thr,1e-4)

def _smooth_and_dilate_mask(mask, smooth_ms=80, dilate_ms=40):
    if mask.size==0: return mask
    k1=max(1,int(TARGET_SR*smooth_ms/1000)); k2=max(1,int(TARGET_SR*dilate_ms/1000))
    sm=(np.convolve(mask.astype(float), np.ones(k1), mode="same")>=0.5*k1)
    dl=(np.convolve(sm.astype(float), np.ones(k2), mode="same")>0)
    return dl.astype(bool)

def _collect_noise_clip(y, speech_mask):
    ns=~speech_mask; noise=y[ns]
    need=int(MIN_NOISE_SEC*TARGET_SR)
    if noise.size<need:
        win=max(1,int(TARGET_SR*0.03))
        rms=np.sqrt(np.convolve(y**2, np.ones(win)/win, mode="same")+1e-12)
        idx=np.argsort(rms)[:int(0.1*y.size)]
        noise=np.concatenate([noise, y[np.sort(idx)]])
    return noise.astype(np.float32)

def _snr_estimate(y, noise):
    if y.size==0 or noise.size==0: return 0.0
    nvar=float(np.var(noise)+1e-9); svar=float(np.var(y)+1e-9)
    sig=max(svar-nvar,1e-9); return 10.0*np.log10(sig/nvar)

def enhance_speech_in_memory(file_path: str) -> np.ndarray:
    seg=_load_audio_segment(file_path)
    if seg.frame_rate!=TARGET_SR: seg=seg.set_frame_rate(TARGET_SR)
    if seg.channels!=TARGET_CHANNELS: seg=seg.set_channels(TARGET_CHANNELS)
    seg=_apply_band_filters(seg); seg=effects.normalize(seg)
    y=_segment_to_float32(seg)
    if y.size==0: return y

    speech=_vad_mask_float32(y, frame_ms=30)
    speech=_smooth_and_dilate_mask(speech, 80, 40)
    noise=_collect_noise_clip(y, speech)
    snr=_snr_estimate(y, noise) if noise.size>0 else 99.0
    need=int(MIN_NOISE_SEC*TARGET_SR)

    if (snr>=SNR_BYPASS_DB) or (noise.size<need):
        out=np.clip(y,-1,1).astype(np.float32)
        pk=float(np.max(np.abs(out))) if out.size else 0.0
        if pk>0: out*=0.98/pk
        return out

    yp=_pre_emphasis(y, PREEMPHASIS)

    def _nr(v, prop):
        try:
            return nr.reduce_noise(y=v, sr=TARGET_SR, y_noise=noise,
                stationary=NR_STATIONARY, prop_decrease=float(prop),
                n_fft=int(NR_N_FFT), hop_length=int(NR_HOP_LENGTH),
                freq_mask_smooth_hz=int(NR_FREQ_MASK_SMOOTH_HZ),
                time_mask_smooth_ms=int(NR_TIME_MASK_SMOOTH_MS),).astype(np.float32)
        except TypeError:
            try:
                return nr.reduce_noise(y=v, sr=TARGET_SR, y_noise=noise,
                    stationary=NR_STATIONARY, prop_decrease=float(prop),
                    n_fft=int(NR_N_FFT), hop_length=int(NR_HOP_LENGTH),).astype(np.float32)
            except TypeError:
                return nr.reduce_noise(y=v, sr=TARGET_SR, y_noise=noise,
                    stationary=NR_STATIONARY, prop_decrease=float(prop),).astype(np.float32)

    r_soft=_nr(yp, NR_PROP_SOFT); r_base=_nr(yp, NR_PROP_DECREASE); r_hard=_nr(yp, NR_PROP_HARD)

    def _mix(red, gate):
        out=red.copy()
        if out.size==y.size and speech.size==y.size:
            out[~speech]*=gate
            out[speech]=(SPEECH_BLEND*out[speech] + (1.0-SPEECH_BLEND)*y[speech]) * SPEECH_GAIN
        return out

    cand=[_mix(r_soft,GATE_ATTN_SOFT), _mix(r_base,GATE_ATTN_SOFT), _mix(r_hard,GATE_ATTN_HARD)]

    def _rms(a,m): 
        if a.size==0 or m.size==0 or not m.any(): return 1e-9
        v=a[m]; return float(np.sqrt(np.mean(v*v)+1e-12))
    def _corr(a,b,m):
        if a.size==0 or b.size==0 or m.size==0 or not m.any(): return 0.0
        x=a[m]-np.mean(a[m]); y2=b[m]-np.mean(b[m])
        den=(np.linalg.norm(x)*np.linalg.norm(y2))+1e-9
        return float(np.dot(x,y2)/den)
    def _score(y_ref, y_hat, m):
        ns_att = 1.0 - (_rms(y_hat, ~m)/max(_rms(y_ref, ~m),1e-9))
        sp_keep= 1.0 - min(abs((_rms(y_hat,m)/max(_rms(y_ref,m),1e-9))-1.0),1.0)
        sp_corr=( _corr(y_ref,y_hat,m)+1.0)/2.0
        return 0.45*ns_att + 0.30*sp_keep + 0.25*sp_corr

    scores=[_score(y,c,speech) for c in cand]
    best=cand[int(np.argmax(scores))]
    best=np.clip(best,-1,1).astype(np.float32)
    pk=float(np.max(np.abs(best))) if best.size else 0.0
    if pk>0: best*=0.98/pk
    return best
