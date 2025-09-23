// src/utils/voiceApi.js

/**
 * 백엔드 STT API(/api/stt)를 호출하여 오디오 데이터를 텍스트로 변환합니다.
 * @param {Blob} audioBlob - 변환할 오디오 데이터 (Blob 객체).
 * @returns {Promise<string>} 인식된 텍스트를 담은 Promise.
 * @throws {Error} API 호출 또는 변환 실패 시 에러를 던집니다.
 */
export const transcribeAudio = async (audioBlob) => {

    // Blob 크기 체크 강화 (alert 추가로 사용자 안내, 재녹음 유도).
    // 동작 처리를 위해 이중으로 존재함, 로그만 던짐
    if (audioBlob.size < 2000) {
        console.log('Blob size too small:', audioBlob.size); // 디버깅 로그 추가
        alert('음성 입력이 너무 짧아요. 다시 말씀해주세요.'); // 사용자 안내 추가
        throw new Error('오디오 데이터가 너무 작습니다. 다시 녹음해주세요.');
    }

    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm'); // 'file'은 main.py에서 기대하는 필드명, 객체, 실제 파일명

    try {
        const response = await fetch('http://localhost:8000/api/stt', {
            method: 'POST',
            body: formData,
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `서버 오류: ${response.status}`);
        }

        const data = await response.json();
        return data.text;
    } catch (error) {
        console.error("STT API 호출 실패:", error);
        throw error;
    }
};

/**
 * 백엔드 TTS API(/api/tts)를 호출하여 텍스트를 음성으로 변환하고 재생합니다.
 * @param {string} text - 음성으로 변환할 텍스트.
 * @returns {Promise<void>} 음성 재생이 완료되면 resolve되는 Promise.
 * @throws {Error} API 호출 또는 오디오 재생 실패 시 에러를 던집니다.
 */
export const speakText = async (text) => {
    // 텍스트가 비어있으면
    if (!text || !text.trim()) {
        return;
    }

    const formData = new FormData();
    formData.append('text', text);

    // ----- 수정 시작 -----
    // 기존: 최대 2회 재시도 로직 추가 (useVoiceFlow.js 데드락 방지 연계).
    // 수정: 디버깅 로그 추가 (TTS 호출 확인).
    let attempts = 0;
    const maxAttempts = 2;
    while (attempts < maxAttempts) {
        try {
            console.log('TTS speakText attempt:', attempts + 1); // 디버깅 로그 추가
            const response = await fetch('http://localhost:8000/api/tts', {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `서버 오류: ${response.status}`);
            }

            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            return new Promise((resolve, reject) => {
                audio.onended = () => {
                    URL.revokeObjectURL(audioUrl); // 메모리 누수 방지
                    resolve();
                };
                audio.onerror = (err) => {
                    URL.revokeObjectURL(audioUrl);
                    console.error("오디오 재생 실패:", err);
                    reject(new Error("음성 재생에 실패했습니다."));
                };
                audio.play();
            });
        } catch (error) {
            attempts++;
            console.error(`TTS 시도 ${attempts} 실패:`, error);
            if (attempts >= maxAttempts) {
                throw error; // 최종 실패
            }
        }
    }
};