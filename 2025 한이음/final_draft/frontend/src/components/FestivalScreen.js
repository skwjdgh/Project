// src/components/FestivalScreen.js
import React, { useState } from 'react';
import hamsterImage from '../assets/hamster12.png';
import '../styles/FestivalScreen.css';

// onBack prop은 더 이상 사용되지 않으므로 제거합니다.
function FestivalScreen({ festivals, keyword }) {
    // 오늘 날짜 기준
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // "서울" 축제만 필터링 + 날짜 처리
    const seoulFestivals = festivals
        .filter(f => (f['위치'] || '').trim() === '서울')
        .map(f => {
            // 날짜 문자열 정리 (소수점 제거)
            const startStr = String(f["시작일_정리"] || '').split('.')[0];
            const endStr = String(f["종료일_정리"] || '').split('.')[0];

            const startDate = startStr && startStr.length === 8
                ? new Date(`${startStr.slice(0,4)}-${startStr.slice(4,6)}-${startStr.slice(6,8)}`)
                : null;
            const endDate = endStr && endStr.length === 8
                ? new Date(`${endStr.slice(0,4)}-${endStr.slice(4,6)}-${endStr.slice(6,8)}`)
                : null;

            return { ...f, startDate, endDate };
        })
        // 오늘 기준 지난 축제 제외
        .filter(f => !f.endDate || f.endDate >= today)
        // 시작일 가까운 순 정렬
        .sort((a, b) => (a.startDate || Infinity) - (b.startDate || Infinity));

    const [page, setPage] = useState(0);
    const pageSize = 3;
    const totalPages = Math.ceil(seoulFestivals.length / pageSize);
    const pagedFestivals = seoulFestivals.slice(page * pageSize, (page + 1) * pageSize);

    return (
        <div className="festival-screen">
            <img src={hamsterImage} alt="안내 햄스터" className="hamster-image-top" />

            <div className="festival-content-box">
                <h2>‘{keyword}’ 관련 서울 축제</h2>
                
                {/* --- 이 부분의 뒤로가기 버튼이 삭제되었습니다 --- */}
                
                <div className="festival-list">
                    {pagedFestivals.length === 0 ? (
                        <p className="no-result">예정된 축제가 없습니다.</p>
                    ) : (
                        pagedFestivals.map((f, i) => {
                            const url = f["홈페이지주소"] || '';
                            const qrUrl = url
                                ? `https://api.qrserver.com/v1/create-qr-code/?size=80x80&data=${encodeURIComponent(url)}`
                                : '';

                            const startDateStr = f.startDate
                                ? f.startDate.toISOString().split('T')[0]
                                : '미정';
                            const endDateStr = f.endDate
                                ? f.endDate.toISOString().split('T')[0]
                                : '미정';

                            const address = f["소재지도로명주소"]?.trim() || '미정';

                            return (
                                <div className="festival-card" key={i}>
                                    {/* 왼쪽: 텍스트 정보 */}
                                    <div className="card-text-content">
                                        <div className="festival-name">{f["축제명"]}</div>
                                        <div className="festival-info">
                                            <div><span className="festival-label">장소:</span>{f["개최장소"] || '미정'}</div>
                                            <div><span className="festival-label">주소:</span>{address}</div>
                                            <div><span className="festival-label">기간:</span>{`${startDateStr} ~ ${endDateStr}`}</div>
                                        </div>
                                    </div>

                                    {/* 오른쪽: CSV URL 기반 QR 코드 */}
                                    <div className="qr-code-placeholder">
                                        {url ? (
                                            <a href={url} target="_blank" rel="noopener noreferrer">
                                                <img src={qrUrl} alt="QR 코드" />
                                            </a>
                                        ) : (
                                            <div className="no-qr">URL 없음</div>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>

                <div className="pagination-btns">
                    <button
                        className="page-nav"
                        onClick={() => setPage(p => Math.max(p - 1, 0))}
                        disabled={page === 0}
                    >
                        〈 이전
                    </button>
                    <span className="page-info">{page + 1} / {totalPages || 1}</span>
                    <button
                        className="page-nav"
                        onClick={() => setPage(p => Math.min(p + 1, totalPages - 1))}
                        disabled={page >= totalPages - 1}
                    >
                        다음 〉
                    </button>
                </div>
            </div>
        </div>
    );
}

export default FestivalScreen;
