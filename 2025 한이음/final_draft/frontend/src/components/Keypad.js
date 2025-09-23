// src/components/Keypad.js
import React from 'react';
import '../styles/Keypad.css';

/**
 * Keypad 컴포넌트
 * - value: 현재 입력된 PIN 문자열
 * - onKeyPress: 키가 눌렸을 때 호출되는 콜백 (키값 전달)
 */
function Keypad({value, onKeyPress}) {
    // 버튼 배열 정의 (숫자, 정정, 확인)
    const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'clear', '0', 'submit'];

    return (
        <div className="keypad-wrapper">
            {/* 입력된 숫자를 실시간으로 표시 */}
            <div className="keypad-display">
                {value}
            </div>

            {/* 버튼 렌더링 */}
            <div className="keypad">
                {keys.map((key) => {
                    const classNames = ['keypad-button'];
                    if (key === 'clear') classNames.push('btn-clear');
                    else if (key === 'submit') classNames.push('btn-submit');

                    return (
                        <button
                            key={key}
                            onClick={() => onKeyPress(key)}
                            className={classNames.join(' ')}
                        >
                            {key === 'clear' ? '정정'
                                : key === 'submit' ? '확인'
                                    : key}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

export default Keypad;
