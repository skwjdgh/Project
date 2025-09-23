// src/hooks/useVoiceFlow.js
import {useState, useCallback, useEffect, useRef} from 'react';
import {useAudioRecorder} from './useAudioRecorder';
import {transcribeAudio, speakText} from '../utils/voiceApi';

const VOICE_FLOW_STATE = {
    IDLE: 'IDLE',
    SPEAKING: 'SPEAKING',
    LISTENING: 'LISTENING',
    PROCESSING: 'PROCESSING',
    ERROR: 'ERROR',
};

const LISTEN_AFTER_TTS_DELAY_MS = 300; // 에코 방지

export const useVoiceFlow = ({onCommandReceived, onError}) => {
    const [flowState, setFlowState] = useState(VOICE_FLOW_STATE.IDLE);
    const [isSttQueued, setIsSttQueued] = useState(false);
    const [error, setError] = useState(null);
    const {startRecording, stopRecording, isRecording} = useAudioRecorder();

    const flowStateRef = useRef(flowState);
    useEffect(() => {
        flowStateRef.current = flowState;
    }, [flowState]);

    const isSttQueuedRef = useRef(isSttQueued);
    useEffect(() => {
        isSttQueuedRef.current = isSttQueued;
    }, [isSttQueued]);

    const onCommandReceivedRef = useRef(onCommandReceived);
    useEffect(() => {
        onCommandReceivedRef.current = onCommandReceived;
    }, [onCommandReceived]);

    const onErrorRef = useRef(onError);
    useEffect(() => {
        onErrorRef.current = onError;
    }, [onError]);

    // TTS 제어
    const ttsTimeoutRef = useRef(null);
    const ttsActiveRef = useRef(false);
    const postTtsListenTidRef = useRef(null);

    const clearTtsTimeout = () => {
        if (ttsTimeoutRef.current) {
            clearTimeout(ttsTimeoutRef.current);
            ttsTimeoutRef.current = null;
        }
    };
    const clearPostTtsListen = () => {
        if (postTtsListenTidRef.current) {
            clearTimeout(postTtsListenTidRef.current);
            postTtsListenTidRef.current = null;
        }
    };

    const stopSpeaking = useCallback(() => {
        try {
            window?.speechSynthesis?.cancel();
        } catch {
        }
        ttsActiveRef.current = false;
        clearTtsTimeout();
        clearPostTtsListen();
        if (flowStateRef.current === VOICE_FLOW_STATE.SPEAKING) setFlowState(VOICE_FLOW_STATE.IDLE);
        setIsSttQueued(false);
    }, []);

    const handleError = useCallback((errorCode, errorObject) => {
        setFlowState(VOICE_FLOW_STATE.ERROR);
        const err = {code: errorCode, originalError: errorObject};
        setError(err);
        onErrorRef.current?.(err);
        console.error(`VoiceFlow Error [${errorCode}]`, errorObject);
        setTimeout(() => setFlowState(VOICE_FLOW_STATE.IDLE), 1200);
    }, []);

    const listenAndRecognize = useCallback(async () => {
        console.log('STT listenAndRecognize called!');
        if (flowStateRef.current === VOICE_FLOW_STATE.SPEAKING) {
            console.log('TTS is playing. Queuing STT request.');
            setIsSttQueued(true);
            return;
        }
        if (isRecording) {
            console.log('Already recording, skipping...');
            return;
        }

        setIsSttQueued(false);
        setFlowState(VOICE_FLOW_STATE.LISTENING);

        try {
            // ✅ VAD가 말이 끝난 뒤 0.8초 내 자동 stop (useAudioRecorder에서 수행)
            const audioBlob = await startRecording();

            setFlowState(VOICE_FLOW_STATE.PROCESSING);

            if (!audioBlob || audioBlob.size < 2000) {
                handleError('STT_NO_SPEECH', new Error('No speech detected'));
                setTimeout(() => listenAndRecognize(), 800);
                return;
            }

            const transcript = await transcribeAudio(audioBlob);
            if (transcript && transcript.trim()) {
                onCommandReceivedRef.current?.(transcript);
            } else {
                handleError('STT_LOW_CONFIDENCE', new Error('Could not recognize speech'));
            }

            if (flowStateRef.current === VOICE_FLOW_STATE.PROCESSING) {
                setFlowState(VOICE_FLOW_STATE.IDLE);
            }
        } catch (e) {
            const msg = String(e?.message || e);
            if (msg === 'MIC_PERMISSION_DENIED' || msg === 'NO_MICROPHONE') {
                handleError(msg, e);
            } else if (msg === 'NO_SPEECH_DETECTED' || msg === 'SPEECH_TOO_SHORT') {
                handleError('STT_NO_SPEECH', e);
                setTimeout(() => listenAndRecognize(), 800);
            } else {
                handleError('STT_NETWORK_ERROR', e);
            }
        } finally {
            try {
                stopRecording();
            } catch {
            }
            console.log('Recording stopped in finally block');
        }
    }, [startRecording, stopRecording, isRecording, handleError]);

    const speak = useCallback(async (text, {listenAfter = false} = {}) => {
        console.log('TTS speak called!', {listenAfter});
        stopSpeaking();

        setFlowState(VOICE_FLOW_STATE.SPEAKING);
        ttsActiveRef.current = true;

        try {
            const speakPromise = speakText(text);

            clearTtsTimeout();
            // (옵션) 안전 타임아웃 – 이벤트 누락 대비
            ttsTimeoutRef.current = setTimeout(() => {
                if (ttsActiveRef.current) {
                    console.warn('TTS timeout -> forcing stop');
                    stopSpeaking();
                }
            }, 8000);

            await speakPromise;
            console.log('TTS speakText completed!');
        } catch (e) {
            console.warn('TTS speak failed:', e);
        } finally {
            clearTtsTimeout();
            ttsActiveRef.current = false;
            if (flowStateRef.current === VOICE_FLOW_STATE.SPEAKING) setFlowState(VOICE_FLOW_STATE.IDLE);

            if (isSttQueuedRef.current || listenAfter) {
                setIsSttQueued(false);
                console.log('Running queued STT after TTS with delay.');
                clearPostTtsListen();
                postTtsListenTidRef.current = setTimeout(() => {
                    postTtsListenTidRef.current = null;
                    listenAndRecognize();
                }, LISTEN_AFTER_TTS_DELAY_MS);
            }
        }
    }, [listenAndRecognize, stopSpeaking]);

    return {
        flowState,
        error,
        speak,
        listenAndRecognize,
        stopListening: stopRecording,
        stopSpeaking,
    };
};
