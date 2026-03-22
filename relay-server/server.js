/**
 * @fileoverview Zhineng Bridge Relay Server
 * WebSocket服务器，提供实时消息中继、会话管理和终端状态同步
 * @module relay-server/server
 */

const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = process.env.PORT || 8001;
const HTTP_STATUS_NOT_FOUND = 404;
const HTTP_STATUS_OK = 200;

const CLIENTS = new Map();
const SESSIONS = new Map();
const CHANNELS = new Map();
const MESSAGE_QUEUE = new Map();

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json'
};

/**
 * 生成唯一ID
 * @returns {string} 8字节随机十六进制字符串
 */
function generateId() {
  return crypto.randomBytes(8).toString('hex');
}

/**
 * 广播消息到频道内所有客户端
 * @param {string} channel - 频道名称
 * @param {Object} message - 消息对象
 * @param {WebSocket} [excludeClient] - 排除的客户端
 */
function broadcast(channel, message, excludeClient = null) {
  const data = JSON.stringify(message);
  CHANNELS.get(channel)?.forEach(client => {
    if (client !== excludeClient && client.readyState === WebSocket.OPEN) {
      client.send(data);
    }
  });
}

/**
 * 处理客户端消息
 * @param {WebSocket} ws - WebSocket客户端
 * @param {Object} message - 消息对象
 */
function handleMessage(ws, message) {
  const { type, channel, targetClientId, payload, sessionId } = message;

  switch (type) {
    case 'join': {
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
    }

    case 'leave': {
      if (CHANNELS.has(channel)) {
        CHANNELS.get(channel).delete(ws);
      }
      ws.send(JSON.stringify({ type: 'left', channel }));
      break;
    }

    case 'message': {
      if (MESSAGE_QUEUE.has(channel)) {
        MESSAGE_QUEUE.get(channel).push({ ...payload, timestamp: Date.now() });
      }
      broadcast(channel, { type: 'message', payload, senderId: ws.clientId, timestamp: Date.now() }, ws);
      break;
    }

    case 'direct': {
      const targetClient = Array.from(CLIENTS.values()).find(c => c.clientId === targetClientId);
      if (targetClient && targetClient.readyState === WebSocket.OPEN) {
        targetClient.send(JSON.stringify({ type: 'direct', payload, senderId: ws.clientId }));
      }
      break;
    }

    case 'terminal_state': {
      const currentSession = SESSIONS.get(sessionId || channel);
      if (currentSession) {
        currentSession.terminalState = payload;
        currentSession.lastUpdate = Date.now();
      }
      broadcast(channel, { type: 'terminal_state', payload, senderId: ws.clientId, timestamp: Date.now() }, ws);
      break;
    }

    case 'command': {
      broadcast(channel, { type: 'command', payload, senderId: ws.clientId, timestamp: Date.now() }, ws);
      break;
    }

    case 'create_session': {
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
    }

    case 'get_sessions': {
      const sessions = Array.from(SESSIONS.values());
      ws.send(JSON.stringify({ type: 'sessions_list', sessions }));
      break;
    }

    case 'switch_session': {
      const targetSession = SESSIONS.get(payload.sessionId);
      if (targetSession) {
        ws.currentSessionId = payload.sessionId;
        ws.send(JSON.stringify({ type: 'session_state', payload: targetSession }));
      }
      break;
    }

    case 'pause_session': {
      const pauseSession = SESSIONS.get(payload.sessionId);
      if (pauseSession) {
        pauseSession.isActive = false;
        pauseSession.lastUpdate = Date.now();
        ws.send(JSON.stringify({ type: 'session_paused', sessionId: payload.sessionId }));
      }
      break;
    }

    case 'resume_session': {
      const resumeSession = SESSIONS.get(payload.sessionId);
      if (resumeSession) {
        resumeSession.isActive = true;
        resumeSession.lastUpdate = Date.now();
        ws.send(JSON.stringify({ type: 'session_resumed', session: resumeSession }));
      }
      break;
    }

    case 'offline_message': {
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
    }

    case 'get_offline_messages': {
      const offlineMessages = MESSAGE_QUEUE.get(channel) || [];
      const clientMessages = offlineMessages.filter(m =>
        m.senderId === ws.clientId || m.timestamp > (payload.since || 0)
      );
      ws.send(JSON.stringify({ type: 'offline_messages', messages: clientMessages }));
      break;
    }

    case 'ping': {
      ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
      break;
    }

    default:
      console.log(`Unknown message type: ${type}`);
  }
}

/**
 * HTTP请求处理 - 提供静态文件服务
 * @param {http.IncomingMessage} req
 * @param {http.ServerResponse} res
 */
function handleHttpRequest(req, res) {
  if (req.url === '/health') {
    res.writeHead(HTTP_STATUS_OK, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok' }));
    return;
  }

  let filePath = req.url === '/' ? '/test-client.html' : req.url;
  filePath = path.join(__dirname, '..', filePath);

  const ext = path.extname(filePath);
  const contentType = MIME_TYPES[ext] || 'text/plain';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(HTTP_STATUS_NOT_FOUND);
      res.end('Not Found');
    } else {
      res.writeHead(HTTP_STATUS_OK, { 'Content-Type': contentType });
      res.end(content);
    }
  });
}

const httpServer = http.createServer(handleHttpRequest);

const wss = new WebSocket.Server({ server: httpServer });

wss.on('connection', (ws) => {
  console.log('New client connected');
  ws.clientId = generateId();
  CLIENTS.set(ws.clientId, ws);

  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data);
      handleMessage(ws, message);
    } catch (e) {
      console.error('Failed to parse message:', e.message);
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
    console.error('WebSocket error:', error.message);
  });

  ws.send(JSON.stringify({ type: 'connected', clientId: ws.clientId }));
});

httpServer.listen(PORT, () => {
  console.log(`Zhineng Bridge Relay Server running on port ${PORT}`);
  console.log(`WebSocket endpoint: ws://localhost:${PORT}`);
  console.log(`HTTP server: http://localhost:${PORT}`);
});
