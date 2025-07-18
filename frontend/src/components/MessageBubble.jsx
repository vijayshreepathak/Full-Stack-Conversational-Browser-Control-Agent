import React from 'react';
import ScreenshotDisplay from './ScreenshotDisplay';
import './MessageBubble.css';

const MessageBubble = ({ sender, text, screenshot }) => {
  return (
    <div className={`message-bubble ${sender}`}> 
      <div className="message-text">{text}</div>
      {screenshot && <ScreenshotDisplay src={screenshot} />}
    </div>
  );
};

export default MessageBubble; 