let socket;
let subscribers = [];
let pendingMessages = [];

export function connectWebSocket(url) {
  if (socket && socket.readyState !== WebSocket.CLOSED) return;

  socket = new WebSocket(url);

  socket.onopen = () => {
    pendingMessages.forEach(msg => socket.send(msg));
    pendingMessages = [];
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      subscribers.forEach(fn => fn(data));
    } catch (e) {
      console.error('WebSocket message parse error:', e);
    }
  };

  socket.onclose = () => {
    subscribers.forEach(fn => fn({ sender: 'agent', text: 'Connection closed. Please refresh to reconnect.', screenshot: null }));
  };

  socket.onerror = () => {
    subscribers.forEach(fn => fn({ sender: 'agent', text: 'Connection error. Is the backend running?', screenshot: null }));
  };
}

export function sendMessage(message) {
  const payload = JSON.stringify(message);
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(payload);
  } else if (socket && socket.readyState === WebSocket.CONNECTING) {
    pendingMessages.push(payload);
  }
}

export function subscribeToMessages(fn) {
  subscribers.push(fn);
  return () => {
    subscribers = subscribers.filter(sub => sub !== fn);
  };
}