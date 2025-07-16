import React, { useState, useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import { connectWebSocket, sendMessage, subscribeToMessages } from '../services/websocket_client';
import './ChatInterface.css';

const WS_URL = 'ws://localhost:9000';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const chatWindowRef = useRef(null);

  useEffect(() => {
    connectWebSocket(WS_URL);
    // Subscribe to agent messages
    const unsubscribe = subscribeToMessages((msg) => {
      setMessages((prev) => [...prev, msg]);
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    // Scroll to bottom on new message
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (input.trim()) {
      setMessages((prev) => [...prev, { sender: 'user', text: input }]);
      sendMessage({ text: input });
      setInput('');
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-window" ref={chatWindowRef}>
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} sender={msg.sender} text={msg.text} screenshot={msg.screenshot} />
        ))}
      </div>
      <form className="chat-input" onSubmit={handleSend}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your message..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};

export default ChatInterface; 