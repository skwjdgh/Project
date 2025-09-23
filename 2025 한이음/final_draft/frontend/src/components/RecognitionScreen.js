import React from 'react';
import '../styles/RecognitionScreen.css';
import hamsterImage from '../assets/hamster123.png';

// status: 'recognizing' | 'finished'
function RecognitionScreen({ status, text }) {
  return (
    <div className="recognition-container">
      <div className="hamster-area">
        <img src={hamsterImage} alt="안내 햄스터" className="hamster-image-small" />
        {status === 'recognizing' && <div className="loading-spinner"></div>}
        <div className="speech-bubble-fixed">
            <p>네, 듣고 있어요!</p>
        </div>
      </div>
      {status === 'finished' && (
        <div className="user-speech-bubble">
          <p>{text}</p>
        </div>
      )}
    </div>
  );
}

export default RecognitionScreen;