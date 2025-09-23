// src/services/ttsClient.js
// 백엔드 TTS 엔드포인트와 오디오 프리페치 유틸

const TTS_ENDPOINT = "/api/tts";

// 서버 응답(JSON 또는 Blob)을 <audio>로 변환
async function audioFromResponse(res) {
  const ct = (res.headers.get("content-type") || "").toLowerCase();
  if (ct.includes("application/json")) {
    const j = await res.json();
    const url = j.audioUrl || j.url || j.audio_url || j.location;
    if (!url) throw new Error("TTS JSON 응답에 audioUrl 없음");
    const a = new Audio(url);
    a.preload = "auto";
    return a;
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = new Audio(url);
  a.preload = "auto";
  return a;
}

export async function fetchTTSAudio({ text, voice, speed }) {
  let res = await fetch(TTS_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice, speed }),
  });

  if (res.status === 422 || res.status === 415) {
    const fd = new FormData();
    fd.append("text", text);
    if (voice) fd.append("voice", voice);
    if (speed != null) fd.append("speed", String(speed));
    res = await fetch(TTS_ENDPOINT, { method: "POST", body: fd });
  }

  if (!res.ok) {
    const q = new URLSearchParams({
      text,
      ...(voice ? { voice } : {}),
      ...(speed != null ? { speed } : {}),
    }).toString();
    res = await fetch(`${TTS_ENDPOINT}?${q}`, { method: "GET" });
  }

  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(`TTS 실패: ${res.status} ${t}`);
  }
  return audioFromResponse(res);
}

// 간단 프리페치 캐시
const _ttsCache = new Map();

/**
 * 텍스트에 대한 오디오를 미리 받아와 <audio>를 반환하는 Promise를 캐시에 저장.
 * 이미 진행 중이면 기존 Promise를 반환.
 */
export function prefetchTTSAudio(text, opts = {}) {
  if (!text || !text.trim()) return Promise.resolve(null);
  if (_ttsCache.has(text)) return _ttsCache.get(text);
  const p = (async () => {
    const a = await fetchTTSAudio({ text, ...opts });
    // canplay를 기다리되, 500ms 타임아웃으로 너무 오래 안기다림
    // Promise 약속 객체
    await new Promise((resolve) => {
      let done = false;
      const finish = () => { if (!done) { done = true; resolve(); } };
      a.addEventListener("canplay", finish, { once: true });
      setTimeout(finish, 500);
      try { a.load(); } catch {}
    });
    return a;
  })();
  _ttsCache.set(text, p);
  return p;
}

// 필요시 default로도 제공
export default { fetchTTSAudio, prefetchTTSAudio };
