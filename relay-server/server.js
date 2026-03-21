/**
 * 智桥 Relay Server
 * WebSocket中继服务器，支持消息路由和终端状态同步
 */

const WebSocket = require('ws');
const http = require('http');
const { v4: uuidv4 } = require('uuid');

const PORT = process.env.PORT || 8001;

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Zhineng Bridge Relay Server');
});

const wss = new WebSocket.Server({ server });

const clients = new Map();
const channels = new Map();

wss.on('connection', (ws) => {
  const clientId = uuidv4();
  ws.clientId = clientId;
  ws.channels = new Set();
  
  clients.set(clientId, ws);
  
  console.log(`Client connected: ${clientId}`);
  
  ws.send(JSON.stringify({
    type: 'connected',
    clientId
  }));
  
  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data.toString());
      handleMessage(ws, message);
    } catch (error) {
      console.error('Failed to parse message:', error.message);
      ws.send(JSON.stringify({
        type: 'error',
        message: 'Invalid message format'
      }));
    }
  });
  
  ws.on('close', () => {
    console.log(`Client disconnected: ${clientId}`);
    
    ws.channels.forEach(channel => {
      leaveChannel(ws, channel);
    });
    
    clients.delete(clientId);
  });
  
  ws.on('error', (error) => {
    console.error(`WebSocket error for client ${clientId}:`, error.message);
  });
});

function handleMessage(ws, message) {
  const { type, channel, targetClientId, payload } = message;
  
  switch (type) {
    case 'join':
      joinChannel(ws, channel);
      break;
    
    case 'leave':
      leaveChannel(ws, channel);
      break;
    
    case 'message':
      sendMessage(ws, channel, payload);
      break;
    
    case 'direct':
      sendDirectMessage(ws, targetClientId, payload);
      break;
    
    case 'terminal_state':
      broadcastTerminalState(ws, channel, payload);
      break;
    
    case 'ping':
      ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
      break;
    
    default:
      console.log(`Unknown message type: ${type}`);
  }
}

function joinChannel(ws, channel) {
  if (!channels.has(channel)) {
    channels.set(channel, new Set());
  }
  
  channels.get(channel).add(ws.clientId);
  ws.channels.add(channel);
  
  console.log(`Client ${ws.clientId} joined channel ${channel}`);
  
  ws.send(JSON.stringify({
    type: 'joined',
    channel
  }));
}

function leaveChannel(ws, channel) {
  if (channels.has(channel)) {
    channels.get(channel).delete(ws.clientId);
    
    if (channels.get(channel).size === 0) {
      channels.delete(channel);
    }
  }
  
  ws.channels.delete(channel);
  
  console.log(`Client ${ws.clientId} left channel ${channel}`);
}

function sendMessage(ws, channel, payload) {
  const message = {
    type: 'message',
    channel,
    payload,
    senderId: ws.clientId,
    timestamp: Date.now()
  };
  
  broadcast(channel, message);
  console.log(`Client ${ws.clientId} sent message to channel ${channel}`);
}

function sendDirectMessage(ws, targetClientId, payload) {
  const targetClient = clients.get(targetClientId);
  
  if (targetClient && targetClient.readyState === WebSocket.OPEN) {
    targetClient.send(JSON.stringify({
      type: 'direct',
      payload,
      senderId: ws.clientId,
      timestamp: Date.now()
    }));
    
    console.log(`Client ${ws.clientId} sent direct message to ${targetClientId}`);
  } else {
    ws.send(JSON.stringify({
      type: 'error',
      message: `Client ${targetClientId} not found or not connected`
    }));
  }
}

function broadcastTerminalState(ws, channel, payload) {
  const message = {
    type: 'terminal_state',
    channel,
    payload,
    senderId: ws.clientId,
    timestamp: Date.now()
  };
  
  broadcast(channel, message);
  console.log(`Client ${ws.clientId} updated terminal state in channel ${channel}`);
}

function broadcast(channel, message) {
  if (!channels.has(channel)) {
    return;
  }
  
  const clientIds = channels.get(channel);
  const messageStr = JSON.stringify(message);
  
  clientIds.forEach(clientId => {
    const client = clients.get(clientId);
    if (client && client.readyState === WebSocket.OPEN) {
      client.send(messageStr);
    }
  });
}

server.listen(PORT, () => {
  console.log(`Zhineng Bridge Relay Server is running on port ${PORT}`);
  console.log(`WebSocket URL: ws://localhost:${PORT}`);
  console.log(`External WebSocket URL: ws://100.66.1.8:${PORT}`);
});

process.on('SIGINT', () => {
  console.log('\nShutting down server...');
  wss.close(() => {
    server.close(() => {
      console.log('Server closed');
      process.exit(0);
    });
  });
});