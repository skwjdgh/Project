// src/components/PresenceCamera.jsx
import React from 'react';
import {useFacePresence} from '../hooks/useFacePresence';

/**
 * 얼굴 감지 + (옵션) 코너 프리뷰
 * - showPreview=true 이면 같은 스트림을 구석에 띄움(추가 스트림 X)
 */
export default function PresenceCamera({
                                           enabled = true,
                                           onPresentOnce,
                                           debug = false,
                                           intervalMs,
                                           consecutive,
                                           width,
                                           height,
                                           // 👇 코너 프리뷰 옵션
                                           showPreview = false,
                                           previewPosition = 'bottom-right', // 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
                                           previewWidth = 240,
                                           previewHeight = 180,
                                           previewMirror = true,
                                       }) {
    const previewRef = React.useRef(null);

    const {present} = useFacePresence({
        enabled,
        debug,
        intervalMs,
        consecutive,
        width,
        height,
        previewVideoRef: showPreview ? previewRef : null, // 같은 스트림으로 프리뷰
    });

    const firedRef = React.useRef(false);
    React.useEffect(() => {
        if (!enabled) {
            firedRef.current = false;
            return;
        }
        if (present && !firedRef.current) {
            firedRef.current = true;
            onPresentOnce?.();
        }
    }, [present, enabled, onPresentOnce]);

    // 프리뷰 위치 스타일
    const cornerStyle = {
        position: 'fixed',
        zIndex: 9998,
        width: previewWidth,
        height: previewHeight,
        borderRadius: 12,
        overflow: 'hidden',
        boxShadow: '0 8px 20px rgba(0,0,0,0.35)',
        background: '#000',
        pointerEvents: 'none', // 클릭 방해 X
        ...(previewPosition.includes('top') ? {top: 12} : {bottom: 12}),
        ...(previewPosition.includes('left') ? {left: 12} : {right: 12}),
    };

    return (
        <>
            {showPreview && (
                <div style={cornerStyle} aria-label="카메라 프리뷰">
                    <video
                        ref={previewRef}
                        playsInline
                        muted
                        style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                            transform: previewMirror ? 'scaleX(-1)' : 'none',
                        }}
                    />
                </div>
            )}
        </>
    );
}
