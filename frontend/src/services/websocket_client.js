let socket;
let subscribers = [];

export function connectWebSocket(url) {
  if (!socket) {
    socket = new WebSocket(url);
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      subscribers.forEach(fn => fn(data));
    };
  }
}

export function sendMessage(message) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message));
  }
}

export function subscribeToMessages(fn) {
  subscribers.push(fn);
  return () => {
    subscribers = subscribers.filter(sub => sub !== fn);
  };
} 