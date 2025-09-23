// src/hooks/useAudioRecorder.js
// 마이크 녹음 + (옵션) 무음 감지(VAD) 자동 종료 지원 (ES2019 호환: ?. 사용 안함)

import {useState, useRef} from 'react';

/**
 * @typedef {Object} VadOptions
 * @property {number} [analysisInterval=50]   // ms, 무음 감지 주기
 * @property {number} [energyThreshold=0.015] // RMS 임계치(환경 소음에 맞게 조정)
 * @property {number} [endSilenceMs=800]      // 말 멈춘 뒤 이 시간만큼 무음이면 자동 stop
 * @property {number} [maxRecordingMs=15000]  // 안전장치: 최대 녹음 길이
 */

/**
 * @typedef {Object} StartOptions
 * @property {boolean} [vad=true]             // 무음 감지 활성화
 * @property {VadOptions} [vadOptions]        // 무음 감지 파라미터
 */

export const useAudioRecorder = () => {
    const [isRecording, setIsRecording] = useState(false);
    const [permissionStatus, setPermissionStatus] = useState('idle');

    const mediaRecorderRef = useRef(null); // MediaRecorder
    const audioChunksRef = useRef([]);     // Blob Part[]
    const recordingPromiseResolverRef = useRef(null); // resolve func

    // VAD 리소스
    const audioCtxRef = useRef(null);   // AudioContext
    const analyserRef = useRef(null);   // AnalyserNode
    const sourceRef = useRef(null);     // MediaStreamAudioSourceNode
    const vadTimerRef = useRef(null);   // setInterval id
    const maxTimerRef = useRef(null);   // setTimeout id

    const cleanupVad = () => {
        if (vadTimerRef.current) {
            clearInterval(vadTimerRef.current);
            vadTimerRef.current = null;
        }
        if (maxTimerRef.current) {
            clearTimeout(maxTimerRef.current);
            maxTimerRef.current = null;
        }
        try {
            if (sourceRef.current) sourceRef.current.disconnect();
            if (analyserRef.current) analyserRef.current.disconnect();
        } catch (e) {
        }
        sourceRef.current = null;
        analyserRef.current = null;
        if (audioCtxRef.current) {
            try {
                audioCtxRef.current.close();
            } catch (e) {
            }
            audioCtxRef.current = null;
        }
    };

    const computeRms = (arr) => {
        var sum = 0;
        for (var i = 0; i < arr.length; i++) sum += arr[i] * arr[i];
        return Math.sqrt(sum / arr.length);
    };

    /**
     * 녹음을 시작하고, stopRecording() 또는 VAD 자동 종료 시 Blob resolve
     * @param {StartOptions} opts
     * @returns {Promise<Blob>}
     */
    const startRecording = async (opts) => {
        if (isRecording) {
            // 이미 녹음 중이면 새 Promise를 만들지 않음
            return new Promise(function () {
            }); // pending
        }

        opts = opts || {};
        var vad = typeof opts.vad === 'boolean' ? opts.vad : true;
        var vod = opts.vadOptions || {};
        var analysisInterval = typeof vod.analysisInterval === 'number' ? vod.analysisInterval : 50;
        var energyThreshold = typeof vod.energyThreshold === 'number' ? vod.energyThreshold : 0.015;
        var endSilenceMs = typeof vod.endSilenceMs === 'number' ? vod.endSilenceMs : 800;
        var maxRecordingMs = typeof vod.maxRecordingMs === 'number' ? vod.maxRecordingMs : 15000;

        setPermissionStatus('pending');

        try {
            const stream = await navigator.mediaDevices.getUserMedia({audio: true});
            setPermissionStatus('granted');

            // MediaRecorder MIME 선택 (광범위 호환)
            const candidates = ['audio/webm;codecs=opus', 'audio/webm', ''];
            var chosenOptions = null;
            for (var i = 0; i < candidates.length; i++) {
                var mime = candidates[i];
                if (!mime || (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(mime))) {
                    chosenOptions = mime ? {mimeType: mime} : undefined;
                    break;
                }
            }

            const mediaRecorder = new MediaRecorder(stream, chosenOptions);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];
            setIsRecording(true);

            mediaRecorder.ondataavailable = function (e) {
                if (e && e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = function () {
                cleanupVad();
                const audioBlob = new Blob(audioChunksRef.current, {type: 'audio/webm'});
                if (recordingPromiseResolverRef.current) {
                    recordingPromiseResolverRef.current(audioBlob);
                }
                recordingPromiseResolverRef.current = null;
                audioChunksRef.current = [];
                try {
                    stream.getTracks().forEach(function (t) {
                        t.stop();
                    });
                } catch (e) {
                }
                setIsRecording(false);
            };

            mediaRecorder.start();

            // ---- (옵션) VAD 시작: 말이 끊기면 ~endSilenceMs 후 자동 stop ----
            if (vad) {
                try {
                    const AC = window.AudioContext || window.webkitAudioContext;
                    if (AC) {
                        const audioCtx = new AC();
                        audioCtxRef.current = audioCtx;

                        const analyser = audioCtx.createAnalyser();
                        analyser.fftSize = 2048;
                        analyser.smoothingTimeConstant = 0.6;
                        analyserRef.current = analyser;

                        const src = audioCtx.createMediaStreamSource(stream);
                        sourceRef.current = src;
                        src.connect(analyser);

                        const buf = new Float32Array(analyser.fftSize);
                        var silentAccum = 0;
                        var last = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
                        var everSpoken = false;

                        vadTimerRef.current = setInterval(function () {
                            var now = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
                            var dt = now - last;
                            last = now;

                            analyser.getFloatTimeDomainData(buf);
                            var rms = computeRms(buf);

                            if (rms >= energyThreshold) {
                                everSpoken = true;
                                silentAccum = 0;
                            } else if (everSpoken) {
                                silentAccum += dt;
                            }

                            if (everSpoken && silentAccum >= endSilenceMs) {
                                try {
                                    stopRecording();
                                } catch (e) {
                                }
                            }
                        }, analysisInterval);

                        // 최대 녹음 길이 안전장치
                        maxTimerRef.current = setTimeout(function () {
                            try {
                                stopRecording();
                            } catch (e) {
                            }
                        }, maxRecordingMs);
                    }
                } catch (e) {
                    // VAD 초기화 실패해도 녹음은 계속
                    // console.warn('[useAudioRecorder] VAD init failed:', e);
                }
            }

            // 녹음이 중지되면 Blob resolve
            return new Promise(function (resolve) {
                recordingPromiseResolverRef.current = resolve;
            });
        } catch (err) {
            // 권한 거부 / 디바이스 없음
            // console.error('마이크 접근 오류:', err);
            setPermissionStatus(err && err.name === 'NotAllowedError' ? 'denied' : 'idle');
            setIsRecording(false);
            if (err && err.name === 'NotAllowedError') throw new Error('MIC_PERMISSION_DENIED');
            throw new Error('NO_MICROPHONE');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
        }
    };

    return {isRecording, startRecording, stopRecording, permissionStatus};
};
