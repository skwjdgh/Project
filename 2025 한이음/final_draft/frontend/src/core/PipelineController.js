// src/core/PipelineController.js
import {prefetchTTSAudio} from "../services/ttsClient";
import {audioUnlock} from "./AudioUnlock";

export class PipelineController {
    constructor(deps) {
        this.stopSpeaking = deps.stopSpeaking;
        this.speak = deps.speak;
        this.listenAndRecognize = deps.listenAndRecognize;
        this.stopListening = deps.stopListening;

        this.debouncedSpeakTid = null;
        this.weatherSummaryTid = null;
        this.welcomeAudio = null;
        this._pendingSpeak = null;
    }

    stopAllSpeechAndTimers() {
        try {
            this.stopSpeaking?.();
        } catch {
        }
        try {
            window?.speechSynthesis?.cancel();
        } catch {
        }

        ["debouncedSpeakTid", "weatherSummaryTid"].forEach((k) => {
            if (this[k]) {
                clearTimeout(this[k]);
                this[k] = null;
            }
        });

        const a = this.welcomeAudio;
        if (a) {
            try {
                a.onended = null;
                a.onerror = null;
                a.pause();
                a.src = "";
            } catch {
            }
            this.welcomeAudio = null;
        }
    }

    // 지금 재생 중인(및 문서 내 모든) <audio>만 하드스톱
    stopBasicTTS() {
        try {
            this.stopSpeaking?.();
        } catch {
        }
        try {
            window?.speechSynthesis?.cancel();
        } catch {
        }

        const a = this.welcomeAudio;
        if (a) {
            try {
                a.pause();
                a.currentTime = 0;
                a.src = "";
            } catch {
            }
            this.welcomeAudio = null;
        }

        try {
            const audios = document.querySelectorAll("audio");
            audios.forEach((el) => {
                try {
                    el.pause();
                    el.currentTime = 0;
                    el.src = "";
                } catch {
                }
            });
        } catch {
        }
        audioUnlock.suspendIfRunning();
    }

    safeSpeak(text) {
        this.stopAllSpeechAndTimers();
        if (audioUnlock.unlocked) this.speak(text);
        else this._pendingSpeak = text;
    }

    // 백엔드 TTS 프리페치 → 실제 재생(ended까지 대기)
    async speakWelcomeWithBackend(text) {
        this.stopAllSpeechAndTimers();
        const unlockP = audioUnlock.unlock();
        const prefetchP = prefetchTTSAudio(text);
        const a0 = await prefetchP;
        await unlockP.catch(() => {
        });
        const a = new Audio(a0?.src || "");
        a.preload = "auto";

        await new Promise((resolve, reject) => {
            try {
                if (this.welcomeAudio) {
                    try {
                        this.welcomeAudio.onended = null;
                        this.welcomeAudio.onerror = null;
                        this.welcomeAudio.pause();
                        this.welcomeAudio.src = "";
                    } catch {
                    }
                }
                a.onended = () => resolve();
                a.onerror = (e) => reject(e);
                this.welcomeAudio = a;

                a.play().catch(async (err) => {
                    try {
                        await audioUnlock.unlock();
                        await a.play();
                        resolve();
                    } catch (e2) {
                        reject(err || e2);
                    }
                });
            } catch (e) {
                reject(e);
            }
        });
    }

    async sayThen(text, after) {
        try {
            await this.speakWelcomeWithBackend(text);
        } catch {
        }
        after?.();
    }
}

export default PipelineController;
