import React from 'react';
import './ScreenshotDisplay.css';

const ScreenshotDisplay = ({ src }) => {
  // In production, src will be a base64 string or URL from backend
  return (
    <div className="screenshot-display">
      <img src={src} alt="Screenshot" />
    </div>
  );
};

export default ScreenshotDisplay; 