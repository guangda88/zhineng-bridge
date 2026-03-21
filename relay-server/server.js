const WebSocket = require('ws');
const crypto = require('crypto');
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8001;
const CLIENTS = new Map();
const SESSIONS = new Map();
const CHANNELS = new Map();
const MESSAGE_QUEUE = new Map();

const wss = new WebSocket.Server({ port: PORT });

function generateId() {
  return crypto.randomBytes(8).toString('hex');
}

function broadcast(channel, message, excludeClient = null) {
  const data = JSON.stringify(message);
  CHANNELS.get(channel)?.forEach(client => {
    if (client !== excludeClient && client.readyState === WebSocket.OPEN) {
      client.send(data);
    }
  });
}

function handleMessage(ws, message) {
  const { type, channel, targetClientId, payload, sessionId } = message;

  switch (type) {
    case 'join':
      if (!CHANNELS.has(channel)) {
        CHANNELS.set(channel, new Set());
        MESSAGE_QUEUE.set(channel, []);
      }
      CHANNELS.get(channel).add(ws);
      ws.channel = channel;
      ws.clientId = ws.clientId || generateId();
      
      const session = SESSIONS.get(sessionId || channel);
      if (session) {
        ws.send(JSON.stringify({ type: 'session_state', payload: session }));
      }
      
      ws.send(JSON.stringify({ type: 'joined', clientId: ws.clientId, channel }));
      broadcast(channel, { type: 'client_joined', clientId: ws.clientId }, ws);
      console.log(`Client ${ws.clientId} joined channel ${channel}`);
      break;

    case 'leave':
      if (CHANNELS.has(channel)) {
        CHANNELS.get(channel).delete(ws);
      }
      ws.send(JSON.stringify({ type: 'left', channel }));
      break;

    case 'message':
      if (MESSAGE_QUEUE.has(channel)) {
        MESSAGE_QUEUE.get(channel).push({ ...payload, timestamp: Date.now() });
      }
      broadcast(channel, { type: 'message', payload, senderId: ws.clientId, timestamp: Date.now() }, ws);
      break;

    case 'direct':
      const targetClient = Array.from(CLIENTS.values()).find(c => c.clientId === targetClientId);
      if (targetClient && targetClient.readyState === WebSocket.OPEN) {
        targetClient.send(JSON.stringify({ type: 'direct', payload, senderId: ws.clientId }));
      }
      break;

    case 'terminal_state':
      const currentSession = SESSIONS.get(sessionId || channel);
      if (currentSession) {
        currentSession.terminalState = payload;
        currentSession.lastUpdate = Date.now();
      }
      broadcast(channel, { type: 'terminal_state', payload, senderId: ws.clientId, timestamp: Date.now() }, ws);
      break;

    case 'command':
      broadcast(channel, { type: 'command', payload, senderId: ws.clientId, timestamp: Date.now() }, ws);
      break;

    case 'create_session':
      const newSessionId = generateId();
      const newSession = {
        id: newSessionId,
        name: payload.name || `Session ${newSessionId}`,
        projectContext: payload.projectContext || '',
        createdAt: Date.now(),
        lastUpdate: Date.now(),
        terminalState: null,
        messageHistory: [],
        isActive: true
      };
      SESSIONS.set(newSessionId, newSession);
      ws.send(JSON.stringify({ type: 'session_created', session: newSession }));
      break;

    case 'get_sessions':
      const sessions = Array.from(SESSIONS.values());
      ws.send(JSON.stringify({ type: 'sessions_list', sessions }));
      break;

    case 'switch_session':
      const targetSession = SESSIONS.get(payload.sessionId);
      if (targetSession) {
        ws.currentSessionId = payload.sessionId;
        ws.send(JSON.stringify({ type: 'session_state', payload: targetSession }));
      }
      break;

    case 'pause_session':
      const pauseSession = SESSIONS.get(payload.sessionId);
      if (pauseSession) {
        pauseSession.isActive = false;
        pauseSession.lastUpdate = Date.now();
        ws.send(JSON.stringify({ type: 'session_paused', sessionId: payload.sessionId }));
      }
      break;

    case 'resume_session':
      const resumeSession = SESSIONS.get(payload.sessionId);
      if (resumeSession) {
        resumeSession.isActive = true;
        resumeSession.lastUpdate = Date.now();
        ws.send(JSON.stringify({ type: 'session_resumed', session: resumeSession }));
      }
      break;

    case 'offline_message':
      if (MESSAGE_QUEUE.has(channel)) {
        MESSAGE_QUEUE.get(channel).push({
          type: 'offline',
          encryptedContent: payload.encryptedContent,
          timestamp: payload.timestamp || Date.now(),
          senderId: ws.clientId
        });
      }
      ws.send(JSON.stringify({ type: 'offline_queued', timestamp: Date.now() }));
      break;

    case 'get_offline_messages':
      const offlineMessages = MESSAGE_QUEUE.get(channel) || [];
      const clientMessages = offlineMessages.filter(m => 
        m.senderId === ws.clientId || m.timestamp > (payload.since || 0)
      );
      ws.send(JSON.stringify({ type: 'offline_messages', messages: clientMessages }));
      break;

    case 'ping':
      ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
      break;

    default:
      console.log(`Unknown message type: ${type}`);
  }
}

wss.on('connection', (ws) => {
  console.log('New client connected');
  ws.clientId = generateId();
  CLIENTS.set(ws.clientId, ws);

  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data);
      handleMessage(ws, message);
    } catch (e) {
      console.error('Failed to parse message:', e);
    }
  });

  ws.on('close', () => {
    if (ws.clientId) {
      CLIENTS.delete(ws.clientId);
      if (ws.channel && CHANNELS.has(ws.channel)) {
        CHANNELS.get(ws.channel).delete(ws);
        broadcast(ws.channel, { type: 'client_left', clientId: ws.clientId });
      }
    }
    console.log('Client disconnected');
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });

  ws.send(JSON.stringify({ type: 'connected', clientId: ws.clientId }));
});

const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', clients: CLIENTS.size, sessions: SESSIONS.size }));
  } else {
    res.writeHead(404);
    res.end();
  }
});

server.listen(PORT + 1, () => {
  console.log(`HTTP health check server running on port ${PORT + 1}`);
});

console.log(`Zhineng Bridge Relay Server running on port ${PORT}`);
console.log(`WebSocket endpoint: ws://localhost:${PORT}`);
