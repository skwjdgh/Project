import {useEffect, useRef, useState} from 'react';
import * as blazeface from '@tensorflow-models/blazeface';
import * as tf from '@tensorflow/tfjs';

/**
 * 얼굴(사람 얼굴) 존재 여부 판별 훅 (지연 최소화 버전)
 * - previewVideoRef를 넘기면 같은 스트림을 그 <video>에도 붙여 프리뷰를 보여줌
 * - onEnter: 최초 감지 시 1회 콜백 (웰컴 멘트 트리거 용)
 * - onExit: 얼굴 사라졌을 때 콜백
 */
export function useFacePresence({
                                    // (호환용) intervalMs = 300,  // 더 이상 사용하지 않지만 시그니처는 유지
                                    consecutive = 2,        // 연속 감지 프레임 수(민감도)
                                    missConsecutive = 3,    // 연속 미감지 프레임 수(상태 해제)
                                    width = 320,
                                    height = 240,
                                    enabled = true,
                                    debug = false,
                                    previewVideoRef = null, // 외부 프리뷰 비디오
                                    detectEveryN = 2,       // N프레임마다 추론(과부하 방지)
                                    maxFps = 30,            // 추론 상한 FPS
                                    onEnter,                // present -> true 전이 시 콜백
                                    onExit,                 // present -> false 전이 시 콜백
                                } = {}) {
    const [present, setPresent] = useState(false);
    const [ready, setReady] = useState(false);
    const [error, setError] = useState(null);

    const videoRef = useRef(null);     // 추론용 비표시 <video>
    const modelRef = useRef(null);
    const streamRef = useRef(null);
    const rafRef = useRef(null);

    const frameCountRef = useRef(0);
    const lastInferTsRef = useRef(0);
    const seenCountRef = useRef(0);
    const missCountRef = useRef(0);

    useEffect(() => {
        let cancelled = false;

        async function start() {
            if (!enabled) return;
            try {
                // 가능하면 WebGL 백엔드로 (속도 ↑)
                try {
                    await tf.setBackend('webgl');
                    await tf.ready();
                } catch {
                }

                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {width, height, facingMode: 'user'},
                    audio: false,
                });
                streamRef.current = stream;

                // 추론용 비표시 비디오
                const v = document.createElement('video');
                v.srcObject = stream;
                v.playsInline = true;
                v.muted = true;
                await v.play();
                videoRef.current = v;

                // 프리뷰 비디오에도 같은 스트림 연결
                if (previewVideoRef?.current) {
                    try {
                        previewVideoRef.current.srcObject = stream;
                        previewVideoRef.current.muted = true;
                        previewVideoRef.current.playsInline = true;
                        await previewVideoRef.current.play();
                    } catch (e) {
                        if (debug) console.warn('[useFacePresence] preview play() blocked:', e);
                    }
                }

                modelRef.current = await blazeface.load();
                if (debug) console.log('[useFacePresence] BlazeFace loaded');
                setReady(true);

                const loop = async (ts) => {
                    if (cancelled || !enabled) return;
                    rafRef.current = requestAnimationFrame(loop);

                    // FPS 제한
                    if (lastInferTsRef.current && (ts - lastInferTsRef.current) < (1000 / Math.max(1, maxFps))) return;

                    frameCountRef.current++;
                    if (frameCountRef.current % Math.max(1, detectEveryN) !== 0) return;

                    lastInferTsRef.current = ts;

                    try {
                        const preds = await modelRef.current.estimateFaces(videoRef.current, false);
                        const hasFace = !!(preds && preds.length > 0);

                        if (hasFace) {
                            seenCountRef.current += 1;
                            missCountRef.current = 0;

                            if (seenCountRef.current >= Math.max(1, consecutive) && !present) {
                                if (debug) console.log('[useFacePresence] face present');
                                setPresent(true);
                                onEnter?.(); // ← 여기서 웰컴 멘트 바로 트리거
                            }
                        } else {
                            missCountRef.current += 1;
                            if (missCountRef.current >= Math.max(1, missConsecutive) && present) {
                                if (debug) console.log('[useFacePresence] face lost');
                                setPresent(false);
                                onExit?.();
                            }
                            seenCountRef.current = 0;
                        }
                    } catch (e) {
                        if (debug) console.warn('[useFacePresence] inference error', e);
                    }
                };

                rafRef.current = requestAnimationFrame(loop);
            } catch (e) {
                console.error('[useFacePresence] camera init failed:', e);
                setError(e?.message || String(e));
            }
        }

        start();

        return () => {
            cancelled = true;
            if (rafRef.current) cancelAnimationFrame(rafRef.current);

            if (previewVideoRef?.current) {
                try {
                    previewVideoRef.current.srcObject = null;
                } catch {
                }
            }
            const s = streamRef.current;
            if (s) {
                try {
                    s.getTracks().forEach(t => t.stop());
                } catch {
                }
            }

            videoRef.current = null;
            modelRef.current = null;
            streamRef.current = null;

            frameCountRef.current = 0;
            lastInferTsRef.current = 0;
            seenCountRef.current = 0;
            missCountRef.current = 0;

            setReady(false);
        };
        // 중요: present를 의존성에서 빼서 재시작 루프 방지
    }, [enabled, width, height, previewVideoRef, debug, consecutive, missConsecutive, detectEveryN, maxFps, onEnter, onExit]);

    return {present, ready, error};
}
