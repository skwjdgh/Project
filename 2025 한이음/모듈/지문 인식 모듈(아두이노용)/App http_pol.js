// src/App.js
import React, {useState, useEffect, useCallback, useRef} from 'react';
import {useVoiceFlow} from './hooks/useVoiceFlow';
import './styles/App.css';
import WelcomeScreen from './components/WelcomeScreen';
import RecognitionScreen from './components/RecognitionScreen';
import Keypad from './components/Keypad';
import DocumentViewer from './components/DocumentViewer';
import FestivalScreen from './components/FestivalScreen';
import Papa from 'papaparse';
import WeatherScreen from './components/WeatherScreen';

function App() {
    const [flowState, setFlowState] = useState('WELCOME');
    const [isRecognizing, setIsRecognizing] = useState(false);
    const [recognizedText, setRecognizedText] = useState('');
    const [purpose, setPurpose] = useState('');
    const [pinValue, setPinValue] = useState('');
    const [userName, setUserName] = useState('');
    const [festivalData, setFestivalData] = useState([]);
    const [festivalKeyword, setFestivalKeyword] = useState('');
    const [weatherKeyword, setWeatherKeyword] = useState('');
    const [weatherData, setWeatherData] = useState(null);
    const [weatherAiSummary, setWeatherAiSummary] = useState('');

    // ====================================================================
    // ==================== 지문 인증 상태 변수 추가 ========================
    // ====================================================================
    const [isVerifying, setIsVerifying] = useState(false); // 지문 인증 절차 진행 여부
    const [authAttempts, setAuthAttempts] = useState(5);   // 남은 인증 시도 횟수
    const [authMessage, setAuthMessage] = useState('');   // 백엔드로부터 받은 인증 관련 메시지
    const [f_stop_fp, setF_stop_fp] = useState(false);     // 지문 인증 강제 중단 신호
    
    // --- 통신 관련 ref ---
    const ws = useRef(null); // 1. 웹소켓 인스턴스 저장용
    const verificationTaskId = useRef(null); // 2. HTTP 방식에서 사용할 작업 ID
    const pollingInterval = useRef(null); // 2. HTTP 폴링 인터벌 저장용
    // ====================================================================


    // 최신 상태 가드
    const flowStateRef = useRef(flowState);
    useEffect(() => {
        flowStateRef.current = flowState;
    }, [flowState]);

    const prevFlowState = useRef(null);
    const weatherSummarySpokenRef = useRef(false);
    const welcomeListenStartedRef = useRef(false);

    // 타이머
    const debouncedSpeakTidRef = useRef(null);
    const weatherSummaryTidRef = useRef(null);

    // 오디오 자동재생 언락
    const [audioUnlocked, setAudioUnlocked] = useState(false);
    const pendingSpeakRef = useRef(null);
    const audioCtxRef = useRef(null);

    // 웰컴 오디오 핸들
    const welcomeAudioRef = useRef(null);

    // 음성 흐름 훅
    const {
        flowState: voiceFlowState,
        speak,               // 일반 멘트(백엔드 TTS)
        listenAndRecognize,  // 마이크+STT 시작
        stopSpeaking,        // 진행중 음성 중단
    } = useVoiceFlow({onCommandReceived, onError});

    // 최신 voiceFlowState 가드
    const voiceFlowStateRef = useRef(voiceFlowState);
    useEffect(() => {
        voiceFlowStateRef.current = voiceFlowState;
    }, [voiceFlowState]);

    const WELCOME_MSG = '안녕하세요! 무엇을 도와드릴까요? 아래 버튼을 누르거나 음성으로 말씀해주세요.';

    const dummyUsers = {
        '9011111111111': '홍길동',
        '8505051222222': '김상철',
        '9701012345678': '이영희',
    };

    // ====== 핸들러들 ======
    function onCommandReceived(command) {
        setIsRecognizing(false);
        setRecognizedText(command);
    }

    function onError(error) {
        setIsRecognizing(false);
        let errorMessage = '음성 인식 중 오류가 발생했습니다.';
        switch (error?.code) {
            case 'MIC_PERMISSION_DENIED':
                errorMessage = '마이크 사용 권한을 허용해주세요.';
                break;
            case 'NO_MICROPHONE':
                errorMessage = '사용 가능한 마이크 장치가 없습니다.';
                break;
            case 'STT_NO_SPEECH':
                return;
            case 'STT_LOW_CONFIDENCE':
                errorMessage = '음성을 명확히 인식하지 못했습니다. 다시 말씀해주세요.';
                break;
            default:
                break;
        }
        alert(errorMessage);
    }

    // ====== 공용 정리 ======
    const stopAllSpeechAndTimers = useCallback(() => {
        try {
            stopSpeaking?.();
        } catch (_) {
        }
        try {
            window?.speechSynthesis?.cancel();
        } catch (_) {
        }
        [debouncedSpeakTidRef, weatherSummaryTidRef].forEach(ref => {
            if (ref.current) {
                clearTimeout(ref.current);
                ref.current = null;
            }
        });
        const a = welcomeAudioRef.current;
        if (a) {
            try {
                a.onended = null;
                a.onerror = null;
                a.pause();
                a.src = '';
            } catch (_) {
            }
            welcomeAudioRef.current = null;
        }
    }, [stopSpeaking]);

    // ====== 오디오 언락 ======
    const unlockAudio = useCallback(async () => {
        if (audioUnlocked) return;
        try {
            window?.speechSynthesis?.resume?.();
        } catch (_) {
        }
        try {
            const AC = window.AudioContext || window.webkitAudioContext;
            if (AC) {
                if (!audioCtxRef.current) audioCtxRef.current = new AC();
                await audioCtxRef.current.resume();
            }
        } catch (_) {
        }
        setAudioUnlocked(true);
        if (pendingSpeakRef.current) {
            const text = pendingSpeakRef.current;
            pendingSpeakRef.current = null;
            speak(text);
        }
    }, [audioUnlocked, speak]);

    // ====== 일반 멘트 ======
    const safeSpeak = useCallback((text) => {
        stopAllSpeechAndTimers();
        if (!audioUnlocked) {
            pendingSpeakRef.current = text;
            return;
        }
        speak(text);
    }, [stopAllSpeechAndTimers, speak, audioUnlocked]);

    // 최초 사용자 제스처에서 언락
    useEffect(() => {
        const handler = () => unlockAudio();
        window.addEventListener('pointerdown', handler, {once: true});
        window.addEventListener('keydown', handler, {once: true});
        return () => {
            window.removeEventListener('pointerdown', handler);
            window.removeEventListener('keydown', handler);
        };
    }, [unlockAudio]);

    // 홈으로
    const handleBackToHome = () => {
        setFlowState('WELCOME');
        setIsRecognizing(false);
        setRecognizedText('');
        setPurpose('');
        setPinValue('');
        setUserName('');
        setWeatherKeyword('');
        setWeatherData(null);
        setWeatherAiSummary('');
        weatherSummarySpokenRef.current = false;
        welcomeListenStartedRef.current = false;
        stopAllSpeechAndTimers();

        // =========================================
        // ========== 지문 인증 상태 초기화 ==========
        setIsVerifying(false);
        setAuthAttempts(5);
        setAuthMessage('');
        setF_stop_fp(false);

        if (pollingInterval.current) {
            clearInterval(pollingInterval.current);
        pollingInterval.current = null;
        }
        if (verificationTaskId.current) {
            verificationTaskId.current = null;
        }
        // =========================================
        // =========================================

    };

    // 서버 요청 처리
    const handleRequest = async (text) => {
        try {
            const res = await fetch('http://localhost:8000/receive-text/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text}),
            });
            if (!res.ok) throw new Error(`서버 응답 오류: ${res.status}`);
            const data = await res.json();
            const summary = data.summary || text;
            const docType = data.purpose || '';

            setPurpose(docType);

            // 축제
            if (summary.includes('축제') || summary.includes('행사')) {
                setFestivalKeyword(text);
                Papa.parse('/festival.csv', {
                    download: true, header: true,
                    complete: (result) => {
                        setFestivalData(result.data);
                        setFlowState('FESTIVAL');
                    },
                });
                return;
            }

            // 날씨
            if (summary.includes('날씨')) {
                setWeatherKeyword(text);
                const weatherRes = await fetch('http://localhost:8000/weather/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({city: 'Seoul'}),
                });
                if (!weatherRes.ok) {
                    const t = await weatherRes.text();
                    throw new Error(`날씨 API 오류: ${weatherRes.status} ${t}`);
                }
                const weatherResult = await weatherRes.json();
                setWeatherData(JSON.stringify(weatherResult, null, 2));
                const aiSummary = weatherResult?._meta?.ai_summary_ko ?? '';
                setWeatherAiSummary(aiSummary);
                setFlowState('WEATHER_VIEW');
                return;
            }

            // 증명서/문서
            let docName = '';
            if (summary.includes('등본')) docName = '주민등록등본';
            else if (summary.includes('초본')) docName = '주민등록초본';
            else if (summary.includes('가족관계')) docName = '가족관계증명서';
            else if (summary.includes('건강보험')) docName = '건강보험자격득실확인서';

            if (docName) {
                setPurpose(docName);
                setFlowState('PIN_INPUT');
            } else {
                alert('알 수 없는 요청입니다. 다시 시도해주세요.');
                handleBackToHome();
            }
        } catch (error) {
            console.error('처리 중 오류 발생:', error);
            alert('요청 처리 중 오류가 발생했습니다. 다시 시도해 주세요.');
            handleBackToHome();
            setTimeout(() => {
                listenAndRecognize();
            }, 3000);
        }
    };

    // 화면 전환 정리
    useEffect(() => {
        stopAllSpeechAndTimers();
        if (flowState === 'WEATHER_VIEW') weatherSummarySpokenRef.current = false;
        if (flowState === 'WELCOME') welcomeListenStartedRef.current = false;
    }, [flowState, stopAllSpeechAndTimers]);

    // 음성 인식 결과 처리
    useEffect(() => {
        if (recognizedText && recognizedText.trim()) {
            handleRequest(recognizedText);
            setRecognizedText('');
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [recognizedText]);

    // 상태별 멘트 (WELCOME 자동 멘트 없음 — 얼굴 인식 때만)
    useEffect(() => {
        if (debouncedSpeakTidRef.current) {
            clearTimeout(debouncedSpeakTidRef.current);
            debouncedSpeakTidRef.current = null;
        }
        debouncedSpeakTidRef.current = setTimeout(() => {
            if (flowState === prevFlowState.current) return;
            prevFlowState.current = flowState;

            if (flowState === 'PIN_INPUT') {
                safeSpeak('주민등록번호 열 세자리를 입력해주세요.');
            } else if (flowState === 'DOCUMENT_VIEW') {
                if (purpose) {
                    if (purpose.includes('등본') || purpose.includes('초본')) {
                        safeSpeak(`${purpose}이 준비되었습니다. 인쇄를 원하시면 인쇄 버튼을 눌러주세요.`);
                    } else {
                        safeSpeak(`${purpose}가 준비되었습니다. 인쇄를 원하시면 인쇄 버튼을 눌러주세요.`);
                    }
                }
            } else if (flowState === 'FESTIVAL') {
                safeSpeak('서울시 축제 정보를 안내합니다.');
            } else if (flowState === 'WEATHER_VIEW') {
                safeSpeak('현재 날씨와 주간 예보를 알려드립니다.');
            }
        }, 300);

        return () => {
            if (debouncedSpeakTidRef.current) {
                clearTimeout(debouncedSpeakTidRef.current);
                debouncedSpeakTidRef.current = null;
            }
        };
    }, [flowState, purpose, safeSpeak]);

    // 날씨 요약 도착 시 1회만 읽기
    useEffect(() => {
        if (flowState !== 'WEATHER_VIEW') return;
        if (weatherSummarySpokenRef.current) return;
        if (!weatherAiSummary || !weatherAiSummary.trim()) return;

        if (weatherSummaryTidRef.current) {
            clearTimeout(weatherSummaryTidRef.current);
            weatherSummaryTidRef.current = null;
        }
        weatherSummaryTidRef.current = setTimeout(() => {
            safeSpeak(weatherAiSummary);
            weatherSummarySpokenRef.current = true;
        }, 1500);

        return () => {
            if (weatherSummaryTidRef.current) {
                clearTimeout(weatherSummaryTidRef.current);
                weatherSummaryTidRef.current = null;
            }
        };
    }, [flowState, weatherAiSummary, safeSpeak]);

    // 표시용
    useEffect(() => {
        setIsRecognizing(voiceFlowState === 'LISTENING' || voiceFlowState === 'PROCESSING');
    }, [voiceFlowState]);

    // ====== 지연 최소화를 위한 TTS 사전 로드 & 폴백 ======

    // JSON → FormData → GET 폴백, 응답(JSON/바이너리) 자동 처리
    async function fetchTTSAudio({text, voice, speed}) {
        const endpoint = '/api/tts';

        const makeAudioFromResponse = async (res) => {
            const ct = (res.headers.get('content-type') || '').toLowerCase();
            if (ct.includes('application/json')) {
                const j = await res.json();
                const url = j.audioUrl || j.url || j.audio_url || j.location;
                if (!url) throw new Error('TTS JSON 응답에 audioUrl 없음');
                const a = new Audio(url);
                a.preload = 'auto';
                return a;
            }
            // 오디오 스트림/바이너리(혹은 content-type 미설정)
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = new Audio(url);
            a.preload = 'auto';
            return a;
        };

        // ① JSON 바디 시도
        let res = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text, voice, speed}),
        });

        // 422/415 → ② FormData 재시도 (FastAPI Form(...) 대응)
        if (res.status === 422 || res.status === 415) {
            const fd = new FormData();
            fd.append('text', text);
            if (voice) fd.append('voice', voice);
            if (speed != null) fd.append('speed', String(speed));
            res = await fetch(endpoint, {method: 'POST', body: fd});
        }

        // 실패면 ③ GET 폴백
        if (!res.ok) {
            const q = new URLSearchParams({text, ...(voice ? {voice} : {}), ...(speed != null ? {speed} : {})}).toString();
            res = await fetch(`${endpoint}?${q}`, {method: 'GET'});
        }

        if (!res.ok) {
            const t = await res.text().catch(() => '');
            throw new Error(`TTS 실패: ${res.status} ${t}`);
        }
        return makeAudioFromResponse(res);
    }

    // 사전 로드 캐시(Map: text -> Promise<HTMLAudioElement>)
    const ttsCacheRef = useRef(new Map());

    // 웰컴 멘트 사전 로드: 오디오를 미리 받아두고 canplay(=버퍼 일부 준비) 시점까지만 대기
    const prefetchTTSAudio = useCallback(async (text) => {
        const cache = ttsCacheRef.current;
        if (cache.has(text)) return cache.get(text);
        const p = (async () => {
            const a = await fetchTTSAudio({text /*, voice: 'your-voice-id', speed: 1.0 */});
            await new Promise((resolve) => {
                let resolved = false;
                const done = () => {
                    if (!resolved) {
                        resolved = true;
                        resolve();
                    }
                };
                // canplay면 충분(완전 다운로드 필요 X)
                a.addEventListener('canplay', done, {once: true});
                // 혹시 로딩이 너무 오래 걸리면 700ms 후 진행
                setTimeout(done, 700);
                try {
                    a.load();
                } catch {
                }
            });
            return a;
        })();
        cache.set(text, p);
        return p;
    }, []);

    // 앱 시작 시/ WELCOME 진입 시 사전 로드
    useEffect(() => {
        prefetchTTSAudio(WELCOME_MSG).catch(() => {
        });
    }, [prefetchTTSAudio]);
    useEffect(() => {
        if (flowState === 'WELCOME') prefetchTTSAudio(WELCOME_MSG).catch(() => {
        });
    }, [flowState, prefetchTTSAudio]);

    // 기존 목소리로 웰컴 멘트 재생(언락과 병렬) → 끝나면 resolve
    const speakWelcomeWithBackend = useCallback(async (text) => {
        stopAllSpeechAndTimers(); // 중복 방지

        // 언락과 사전 로드를 병렬로
        const unlockP = unlockAudio();
        const prefetchP = prefetchTTSAudio(text);

        const a0 = await prefetchP; // 사전 로딩된 오디오
        await unlockP.catch(() => {
        });

        // 새 인스턴스로 즉시 재생(기존 엘리먼트 재생 재시도 지연 방지)
        const a = new Audio(a0.src);
        a.preload = 'auto';

        return new Promise((resolve, reject) => {
            try {
                const prev = welcomeAudioRef.current;
                if (prev) {
                    try {
                        prev.onended = null;
                        prev.onerror = null;
                        prev.pause();
                        prev.src = '';
                    } catch {
                    }
                }

                a.onended = () => resolve();
                a.onerror = (e) => reject(e);
                welcomeAudioRef.current = a;

                // 이미 버퍼가 준비됐으므로 바로 재생 시도
                a.play().catch(async (err) => {
                    // 정책으로 막히면 언락 재시도 후 한번 더
                    try {
                        await unlockAudio();
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
    }, [stopAllSpeechAndTimers, unlockAudio, prefetchTTSAudio]);

    // 멘트 후 자동으로 마이크 시작
    const startMicIfWelcome = useCallback(() => {
        if (flowStateRef.current !== 'WELCOME') return;
        if (welcomeListenStartedRef.current) return;
        if (voiceFlowStateRef.current === 'LISTENING' || voiceFlowStateRef.current === 'PROCESSING') return;

        welcomeListenStartedRef.current = true;
        setIsRecognizing(true);
        listenAndRecognize();
    }, [listenAndRecognize]);

    // 얼굴 인식/마이크 버튼 공용 트리거
    const handleVoiceClick = useCallback(async () => {
        if (voiceFlowStateRef.current === 'LISTENING' || voiceFlowStateRef.current === 'PROCESSING') return;

        try {
            await speakWelcomeWithBackend(WELCOME_MSG); // 기존 목소리 웰컴(사전 로드로 즉시 재생)
            startMicIfWelcome();                        // 끝나자마자 마이크 시작
        } catch (e) {
            console.warn('welcome TTS failed, start mic immediately:', e);
            startMicIfWelcome();                        // 실패 시 바로 마이크 시작
        }
    }, [speakWelcomeWithBackend, startMicIfWelcome]);

    // 출력
    const handlePrint = () => {
        if (purpose.includes('등본') || purpose.includes('초본')) {
            safeSpeak(`${purpose}이 출력되었습니다.`);
        } else {
            safeSpeak(`${purpose}가 출력되었습니다.`);
        }
        window.print();
    };

    // 키패드
    const handleKeyPress = (key) => {
        if (key === 'clear') setPinValue('');
        else if (key === 'submit') handlePinSubmit(pinValue);
        else if (pinValue.length < 13) setPinValue(prev => prev + key);
    };


    // ======================================================================
    // ==================== 지문 인증 통신 로직 (주석 처리) ===================
    // ======================================================================


    // ======================================================================
    // ================ 2. 실시간 화면 전환 미구현 (HTTP 폴링) ================
    // ======================================================================

    const startVerificationTask = async (name, rrn) => {
        try {
            const response = await fetch('http://localhost:8000/start-verification', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, rrn: rrn }),
            });
            const data = await response.json();
            if (response.ok) {
                verificationTaskId.current = data.task_id;
                setAuthMessage('지문 인증을 시작합니다. 센서에 손가락을 대주세요.');
                // 2초마다 상태를 확인하는 폴링 시작
                pollingInterval.current = setInterval(pollVerificationStatus, 2000);
            } else {
                throw new Error(data.detail || '인증 시작에 실패했습니다.');
            }
        } catch (error) {
            console.error(error);
            setAuthMessage(error.message);
            setIsVerifying(false);
        }
    };
    
    const pollVerificationStatus = async () => {
        if (!verificationTaskId.current) return;
        try {
            const response = await fetch(`http://localhost:8000/verification-status/${verificationTaskId.current}`);
            const data = await response.json();
            
            setAuthMessage(data.message);
            if (data.attempts_left !== undefined) setAuthAttempts(data.attempts_left);

            if (data.status === 'pos_auth' || data.status === 'neg_auth' || data.status === 'canceled') {
                clearInterval(pollingInterval.current); // 폴링 중단
                verificationTaskId.current = null;
                if (data.status === 'pos_auth') {
                    setUserName(data.userName);
                    setFlowState('DOCUMENT_VIEW');
                } else {
                    setTimeout(handleBackToHome, 2000);
                }
            }
        } catch (error) {
            console.error('Polling error:', error);
            setAuthMessage('상태 확인 중 오류가 발생했습니다.');
            clearInterval(pollingInterval.current);
            setIsVerifying(false);
        }
    };


    // ======================================================================
    // ====================== 지문 인증 강제 중단 함수 ========================
    // ======================================================================

    const handleStopVerification = () => {
        setF_stop_fp(true);
        setAuthMessage('인증이 중단되었습니다.');
        
        // 2. HTTP 방식
        if (verificationTaskId.current) {
            fetch(`http://localhost:8000/stop-verification/${verificationTaskId.current}`, { method: 'POST' });
            clearInterval(pollingInterval.current);
        }

        setTimeout(handleBackToHome, 1500);
    };

    // ======================================================================

    const handlePinSubmit = (pin) => {
        if (dummyUsers[pin]) {
            // --- 지문 인증 로직을 사용하지 않는 경우 (기존 방식) ---
            // setUserName(dummyUsers[pin]);
            // setFlowState('DOCUMENT_VIEW');

            // --- 지문 인증 로직을 사용하는 경우 (아래 주석 해제) ---
            const currentUserName = dummyUsers[pin];
            console.log(`${currentUserName} 님의 지문 인증을 시작합니다.`);
            
            // 지문 인증 상태로 전환
            setAuthAttempts(5);
            setF_stop_fp(false);
            setIsVerifying(true);
            
            // --- 아래 두 방식 중 하나를 선택하여 주석 해제 ---
            // 1. 웹소켓 연결 함수 호출
            // connectWebSocket(currentUserName, pin);

            // 2. HTTP 작업 시작 함수 호출
            startVerificationTask(currentUserName, pin);
            
        } else {
            alert('등록되지 않은 주민번호입니다.');
            setPinValue('');
        }
    };



    // 화면 렌더
    const renderCurrentScreen = () => {
        switch (flowState) {
            case 'WELCOME':
                return (
                    <WelcomeScreen
                        onMenuClick={(text) => setRecognizedText(text)}
                        onSubmitText={(text) => setRecognizedText(text)}
                        onVoiceClick={handleVoiceClick}    // 얼굴 인식 시 호출
                        isRecognizing={isRecognizing}
                    />
                );
            case 'FESTIVAL':
                return <FestivalScreen festivals={festivalData} keyword={festivalKeyword}/>;
            case 'WEATHER_VIEW':
                return <WeatherScreen weatherInfo={weatherData} keyword={weatherKeyword} summary={weatherAiSummary}/>;
            case 'PIN_INPUT':
                return (
                    <div className="pin-screen">
                        <div className="recognition-wrapper">
                            <RecognitionScreen status="finished" text={recognizedText}/>
                        </div>
                        <div className="pin-wrapper">
                            <h2>주민번호를 입력해주세요 (- 없이)</h2>
                            <Keypad value={pinValue} onKeyPress={handleKeyPress}/>

                            {/* --- 지문 인증 메시지를 표시할 공간 (UI 미구현) --- */}
                            <div className="auth-message-placeholder">
                                <p>(미구현) 지문 인증 상태 메시지 표시 영역</p>
                                <p>현재 메시지: {authMessage}</p>
                                {isVerifying && <p>남은 횟수: {authAttempts}</p>}
                            </div>


                        </div>
                    </div>
                );
            case 'DOCUMENT_VIEW':
                return <DocumentViewer name={userName} purpose={purpose} onPrint={handlePrint}/>;
            default:
                return (
                    <WelcomeScreen
                        onMenuClick={(text) => setRecognizedText(text)}
                        onSubmitText={(text) => setRecognizedText(text)}
                        onVoiceClick={handleVoiceClick}
                        isRecognizing={isRecognizing}
                    />
                );
        }
    };

    return (
        <div className="kiosk-frame">
            {flowState !== 'WELCOME' && (
                <button className="home-button" onClick={handleBackToHome}></button>
            )}
            {renderCurrentScreen()}
        </div>
    );
}

export default App;
