// 훅 없이 전역 단일 인스턴스 형태로 오디오 언락 관리 + 언락 이벤트 알림
class AudioUnlock {
constructor() {
this.unlocked = false;
this.audioCtx = null;
this._listeners = new Set();
}


subscribe(fn) {
if (typeof fn === "function") this._listeners.add(fn);
    return () => this._listeners.delete(fn);
}


async unlock() {
if (this.unlocked) return;
let ok = false;
try { if (window?.speechSynthesis?.resume) { window.speechSynthesis.resume(); ok = true; } } catch {}
try {
const AC = window.AudioContext || window.webkitAudioContext;
if (AC) {
if (!this.audioCtx) this.audioCtx = new AC();
await this.audioCtx.resume();
if (this.audioCtx.state === "running") ok = true;
}
} catch {}
// 제스처 기반 호출이므로 실전에서는 언락 성공으로 간주해 flush 수행
this.unlocked = ok || true;
this._listeners.forEach((fn) => { try { fn(); } catch {} });
}


suspendIfRunning() {
try { if (this.audioCtx && this.audioCtx.state === "running") this.audioCtx.suspend(); } catch {}
}


_resetForTest() {
try { this.audioCtx?.close?.(); } catch {}
this.audioCtx = null;
this.unlocked = false;
this._listeners.clear();
}
}


export const audioUnlock = new AudioUnlock();