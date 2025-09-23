// src/components/WeatherScreen.js
import React from 'react';
import hamster6 from '../assets/hamster6.png';
import '../styles/WeatherScreen.css';

function WeatherScreen({weatherInfo, keyword, summary}) {
    // JSON 파싱
    let currentWeatherData = null;
    try {
        if (weatherInfo && typeof weatherInfo === 'string') {
            currentWeatherData = JSON.parse(weatherInfo);
        } else if (weatherInfo && typeof weatherInfo === 'object') {
            currentWeatherData = weatherInfo;
        }
    } catch (e) {
        console.error('날씨 정보 파싱 실패:', e);
    }

    // 요약 텍스트: prop 우선, 없으면 백엔드 _meta.ai_summary_ko 사용
    const summaryText =
        (typeof summary === 'string' && summary.trim()) ||
        (currentWeatherData?._meta?.ai_summary_ko?.trim?.() ?? '');

    const getFormattedDate = () => {
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth() + 1;
        const day = today.getDate();
        const dayOfWeek = ['일', '월', '화', '수', '목', '금', '토'][today.getDay()];
        return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}, ${dayOfWeek}요일`;
    };

    const renderCurrentWeather = () => {
        const cod = currentWeatherData?.cod;
        if (!currentWeatherData || !(cod === 200 || cod === '200')) {
            return <p className="weather-error">날씨 정보를 불러오는 데 실패했습니다.</p>;
        }
        const {weather = [], main = {}, wind = {}} = currentWeatherData;
        const w0 = weather[0] || {};
        const iconUrl = w0.icon ? `http://openweathermap.org/img/wn/${w0.icon}@2x.png` : '';

        return (
            <div className="weather-details-grid">
                <div className="weather-main-info">
                    {iconUrl && <img src={iconUrl} alt={w0.description || 'weather'} className="weather-icon"/>}
                    <span className="weather-temp">{Math.round(main.temp)}°</span>
                    <span className="weather-desc">{w0.description}</span>
                </div>
                <div className="weather-sub-info">
                    <div className="info-item">
                        <span className="label">체감</span>
                        <span className="value">{Math.round(main.feels_like)}°</span>
                    </div>
                    <div className="info-item">
                        <span className="label">습도</span>
                        <span className="value">{main.humidity}%</span>
                    </div>
                    <div className="info-item">
                        <span className="label">풍속</span>
                        <span className="value">{wind.speed}m/s</span>
                    </div>
                </div>
            </div>
        );
    };

    const getCityNameInKorean = (cityName) => {
        const cityMap = {Seoul: '서울'};
        return cityMap[cityName] || cityName;
    };

    // ✅ 요약이 있을 때만 중앙 정렬 적용
    const summaryBoxStyle = summaryText
        ? {display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center'}
        : undefined;

    return (
        <div className="welcome-container weather-container">
            <img src={hamster6} alt="날씨 안내 햄스터" className="hamster-image-large"/>
            <div className="speech-bubble-large weather-bubble">
                <h2 className="weather-title">
                    {getCityNameInKorean(currentWeatherData?.name || '도시')} 날씨 정보
                    <span className="date-display">({getFormattedDate()})</span>
                </h2>

                {/* 현재 날씨 카드(상단 박스) */}
                <div className="weather-info-card">{renderCurrentWeather()}</div>

                {/* 하단 박스: 요약을 중앙에 표시(없으면 플레이스홀더) */}
                <div className="chat-log-container" style={summaryBoxStyle}>
                    {summaryText ? (
                        <p className="summary-text" style={{whiteSpace: 'pre-line', margin: 0}}>
                            {summaryText}
                        </p>
                    ) : (
                        <p className="chat-placeholder">요약내용이 여기 표시됩니다.</p>
                    )}
                </div>
            </div>
        </div>
    );
}

export default WeatherScreen;
