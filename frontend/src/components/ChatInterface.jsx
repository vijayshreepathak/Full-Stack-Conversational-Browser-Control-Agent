import React, { useState, useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import { connectWebSocket, sendMessage, subscribeToMessages } from '../services/websocket_client';
import './ChatInterface.css';

const WS_URL = 'ws://localhost:9000';

const PASSWORD_TRIGGERS = ['password', 'pass'];

const isPasswordPrompt = (messages) => {
  const last = [...messages].reverse().find(m => m.sender === 'agent');
  if (!last) return false;
  return PASSWORD_TRIGGERS.some(kw => last.text.toLowerCase().includes(kw));
};

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const chatWindowRef = useRef(null);

  useEffect(() => {
    connectWebSocket(WS_URL);
    const unsubscribe = subscribeToMessages((msg) => {
      setMessages((prev) => [...prev, msg]);
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (input.trim()) {
      setMessages((prev) => [...prev, { sender: 'user', text: isPasswordPrompt(messages) ? '••••••••' : input }]);
      sendMessage({ text: input });
      setInput('');
    }
  };

  const inputType = isPasswordPrompt(messages) ? 'password' : 'text';

  return (
    <div className="chat-interface">
      <div className="chat-window" ref={chatWindowRef}>
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} sender={msg.sender} text={msg.text} screenshot={msg.screenshot} />
        ))}
      </div>
      <form className="chat-input" onSubmit={handleSend}>
        <input
          type={inputType}
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your message..."
          autoComplete={inputType === 'password' ? 'current-password' : 'off'}
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};

export default ChatInterface; 

// What happens here?
// Connect to backend
// Listen for incoming messages
// Update UI when message arrives
// Cleanup on unmount