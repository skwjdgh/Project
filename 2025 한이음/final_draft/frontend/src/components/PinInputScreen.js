// src/components/PinInputScreen.jsx
import React, { useState } from 'react';
import '../styles/PinInputScreen.css';

function PinInputScreen({ onPinSubmit }) {
  const [value, setValue] = useState('');
  const keys = ['1','2','3','4','5','6','7','8','9','clear','0','submit'];

  const handleKeyPress = (key) => {
    if (key === 'clear') {
      setValue('');
    } else if (key === 'submit') {
      onPinSubmit(value);
      setValue('');
    } else {
      if (value.length < 13) {
        setValue(prev => prev + key);
      }
    }
  };

  return (
    <div className="pin-input-screen">
      {/* 입력된 값을 표시하는 실시간 디스플레이 */}
      <input
        type="text"
        className="pin-display"
        value={value}
        readOnly
        placeholder="주민번호를 입력하세요"
      />

      {/* 3×4 그리드 키패드 */}
      <div className="keypad">
        {keys.map(key => (
          <button
            key={key}
            className={`keypad-button ${key === 'clear' || key === 'submit' ? 'special' : ''}`}
            onClick={() => handleKeyPress(key)}
          >
            {key === 'clear' ? '정정' : key === 'submit' ? '확인' : key}
          </button>
        ))}
      </div>
    </div>
  );
}

export default PinInputScreen;
