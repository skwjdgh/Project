// src/components/DocumentViewer.jsx
import React, { useRef } from 'react'; // 1. useRef를 import 합니다.
import '../styles/DocumentViewer.css';

/**
 * DocumentViewer 컴포넌트
 * - props.name: 사용자 이름
 * - props.purpose: 문서 요청 목적 (예: 등본, 초본, 가족관계증명서 등)
 */
function DocumentViewer({name, purpose}) {
    // 2. iframe 요소를 가리킬 ref를 생성합니다.
    const iframeRef = useRef(null);

    // 이름과 목적에 따른 문서 경로 결정
    let docSrc;

    if (name === '홍길동') {
        if (purpose.includes('등본')) {
            docSrc = '/document1.html';
        } else if (purpose.includes('초본')) {
            docSrc = '/extract1.html';
        } else if (purpose.includes('가족관계')) {
            docSrc = '/family1.html';
        } else {
            docSrc = '/healthInsurance1.html';
        }
    } else if (name === '김상철') {
        if (purpose.includes('등본')) {
            docSrc = '/document2.html';
        } else if (purpose.includes('초본')) {
            docSrc = '/extract2.html';
        } else if (purpose.includes('가족관계')) {
            docSrc = '/family2.html';
        } else {
            docSrc = '/healthInsurance2.html';
        }
    } else {
        // 다른 사용자 또는 미지정
        if (purpose.includes('등본')) {
            docSrc = '/document3.html';
        } else if (purpose.includes('초본')) {
            docSrc = '/extract3.html';
        } else if (purpose.includes('가족관계')) {
            docSrc = '/family3.html';
        } else {
            docSrc = '/healthInsurance3.html';
        }
    }

    // 3. iframe의 내용만 인쇄하는 새로운 함수를 만듭니다.
    const handlePrint = () => {
        const iframe = iframeRef.current;
        if (iframe) {
            // iframe의 내부 window에 접근하여 print() 명령을 실행합니다.
            iframe.contentWindow.print();
        }
    };

    return (
        <div className="document-container">
            {/* ✅ 요청에 따라 이름, 요청, 문서 열기 버튼 제거 */}

            {/* 앱 내 미리보기용 iframe */}
            <iframe
                ref={iframeRef} // 4. 생성한 ref를 iframe 요소에 연결합니다.
                src={docSrc}
                title="문서 뷰어"
                className="document-iframe"
            />

            {/* 인쇄 버튼 */}
            <button
                className="print-button"
                onClick={handlePrint} // 5. onClick 이벤트를 새로운 handlePrint 함수로 교체합니다.
            >
                인쇄하기
            </button>
        </div>
    );
}

export default DocumentViewer;
