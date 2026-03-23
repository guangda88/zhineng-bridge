const { createLogger } = require('../cli/logger');
const logger = createLogger('RelayServer');
const { SERVER_CONFIG, WS_CONFIG } = require('../config/constants');
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

const PORT = process.env.PORT || SERVER_CONFIG.DEFAULT_PORT;
const HTTP_STATUS_NOT_FOUND = 404;
const HTTP_STATUS_OK = 200;
const RECONNECT_DELAY_MS = SERVER_CONFIG.RECONNECT_DELAY_MS;

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
 * 验证输入参数
 * @param {*} value - 待验证的值
 * @param {string} type - 期望的类型 ('string', 'number', 'object', 'array')
 * @param {Object} options - 验证选项
 * @param {number} [options.minLength] - 最小长度
 * @param {number} [options.maxLength] - 最大长度
 * @param {RegExp} [options.pattern] - 正则表达式模式
 * @returns {{valid: boolean, error: string|null}} 验证结果
 */
function validateInput(value, type, options = {}) {
    // 类型检查
    if (type === 'string' && typeof value !== 'string') {
        return { valid: false, error: `Expected string, got ${typeof value}` };
    }
    if (type === 'number' && typeof value !== 'number') {
        return { valid: false, error: `Expected number, got ${typeof value}` };
    }
    if (type === 'object' && typeof value !== 'object') {
        return { valid: false, error: `Expected object, got ${typeof value}` };
    }
    if (type === 'array' && !Array.isArray(value)) {
        return { valid: false, error: `Expected array, got ${typeof value}` };
    }

    // 长度检查
    if (options.minLength && value.length < options.minLength) {
        return { valid: false, error: `Length must be at least ${options.minLength}` };
    }
    if (options.maxLength && value.length > options.maxLength) {
        return { valid: false, error: `Length must not exceed ${options.maxLength}` };
    }

    // 模式检查
    if (options.pattern && !options.pattern.test(value)) {
        return { valid: false, error: 'Value does not match required pattern' };
    }

    return { valid: true, error: null };
}

/**
 * 广播消息到频道内所有客户端
 * @param {string} channel - 频道名称
 * @param {Object} message - 消息对象
 * @param {WebSocket} [excludeClient] - 排除的客户端
 */
function broadcast(channel, message, excludeClient = null) {
    const data = JSON.stringify(message);
    const channelClients = CHANNELS.get(channel);
    if (!channelClients) {
        logger.info(`Broadcast: No clients in channel ${channel}`);
        return;
    }
    let sentCount = 0;
    channelClients.forEach(client => {
        if (client !== excludeClient && client.readyState === WebSocket.OPEN) {
            client.send(data);
            sentCount++;
        }
    });
    logger.info(`Broadcast to ${channel}: ${sentCount} clients (excluded: ${excludeClient ? excludeClient.clientId : 'none'})`);
}

/**
 * 处理客户端加入频道
 * @param {WebSocket} ws - WebSocket客户端
 * @param {string} channel - 频道名称
 * @param {string} sessionId - 会话ID
 */
function handleJoin(ws, channel, sessionId) {
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
    logger.info(`Client ${ws.clientId} joined channel ${channel}`);
}

/**
 * 处理客户端离开频道
 * @param {WebSocket} ws - WebSocket客户端
 * @param {string} channel - 频道名称
 */
function handleLeave(ws, channel) {
    if (CHANNELS.has(channel)) {
        CHANNELS.get(channel).delete(ws);
    }
    ws.send(JSON.stringify({ type: 'left', channel }));
}

/**
 * 处理频道消息
 * @param {string} channel - 频道名称
 * @param {Object} payload - 消息内容
 * @param {string} senderId - 发送者ID
 */
function handleChannelMessage(channel, payload, senderId) {
    if (MESSAGE_QUEUE.has(channel)) {
        MESSAGE_QUEUE.get(channel).push({ ...payload, timestamp: Date.now() });
    }
}

/**
 * 处理直接消息
 * @param {string} targetClientId - 目标客户端ID
 * @param {Object} payload - 消息内容
 * @param {string} senderId - 发送者ID
 */
function handleDirectMessage(targetClientId, payload, senderId) {
    const targetClient = Array.from(CLIENTS.values()).find(c => c.clientId === targetClientId);
    if (targetClient && targetClient.readyState === WebSocket.OPEN) {
        targetClient.send(JSON.stringify({ type: 'direct', payload, senderId }));
    }
}

/**
 * 处理终端状态更新
 * @param {string} channel - 频道名称
 * @param {string} sessionId - 会话ID
 * @param {Object} payload - 终端状态
 * @param {string} senderId - 发送者ID
 */
function handleTerminalState(channel, sessionId, payload, senderId) {
    const currentSession = SESSIONS.get(sessionId || channel);
    if (currentSession) {
        currentSession.terminalState = payload;
        currentSession.lastUpdate = Date.now();
    }
}

/**
 * 处理创建会话
 * @param {WebSocket} ws - WebSocket客户端
 * @param {Object} payload - 会话信息
 */
function handleCreateSession(ws, payload) {
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
}

/**
 * 处理获取会话列表
 * @param {WebSocket} ws - WebSocket客户端
 */
function handleGetSessions(ws) {
    const sessions = Array.from(SESSIONS.values());
    ws.send(JSON.stringify({ type: 'sessions_list', sessions }));
}

/**
 * 处理切换会话
 * @param {WebSocket} ws - WebSocket客户端
 * @param {string} sessionId - 目标会话ID
 */
function handleSwitchSession(ws, sessionId) {
    const targetSession = SESSIONS.get(sessionId);
    if (targetSession) {
        ws.currentSessionId = sessionId;
        ws.send(JSON.stringify({ type: 'session_state', payload: targetSession }));
    }
}

/**
 * 处理暂停会话
 * @param {WebSocket} ws - WebSocket客户端
 * @param {string} sessionId - 会话ID
 */
function handlePauseSession(ws, sessionId) {
    const pauseSession = SESSIONS.get(sessionId);
    if (pauseSession) {
        pauseSession.isActive = false;
        pauseSession.lastUpdate = Date.now();
        ws.send(JSON.stringify({ type: 'session_paused', sessionId }));
    }
}

/**
 * 处理恢复会话
 * @param {WebSocket} ws - WebSocket客户端
 * @param {string} sessionId - 会话ID
 */
function handleResumeSession(ws, sessionId) {
    const resumeSession = SESSIONS.get(sessionId);
    if (resumeSession) {
        resumeSession.isActive = true;
        resumeSession.lastUpdate = Date.now();
        ws.send(JSON.stringify({ type: 'session_resumed', session: resumeSession }));
    }
}

/**
 * 处理离线消息
 * @param {string} channel - 频道名称
 * @param {Object} payload - 离线消息
 * @param {string} senderId - 发送者ID
 */
function handleOfflineMessage(channel, payload, senderId) {
    if (MESSAGE_QUEUE.has(channel)) {
        MESSAGE_QUEUE.get(channel).push({
            type: 'offline',
            encryptedContent: payload.encryptedContent,
            timestamp: payload.timestamp || Date.now(),
            senderId
        });
    }
}

/**
 * 处理获取离线消息
 * @param {WebSocket} ws - WebSocket客户端
 * @param {string} channel - 频道名称
 * @param {Object} payload - 查询参数
 * @param {string} senderId - 发送者ID
 */
function handleGetOfflineMessages(ws, channel, payload, senderId) {
    const offlineMessages = MESSAGE_QUEUE.get(channel) || [];
    const clientMessages = offlineMessages.filter(m =>
        m.senderId === senderId || m.timestamp > (payload.since || 0)
    );
    ws.send(JSON.stringify({ type: 'offline_messages', messages: clientMessages }));
}

/**
 * 处理客户端消息
 * @param {WebSocket} ws - WebSocket客户端
 * @param {Object} message - 消息对象
 */
function handleMessage(ws, message) {
    const { type, channel, targetClientId, payload, sessionId } = message;
    const senderId = ws.clientId;

    switch (type) {
    case 'join':
        handleJoin(ws, channel, sessionId);
        break;

    case 'leave':
        handleLeave(ws, channel);
        break;

    case 'message':
        handleChannelMessage(channel, payload, senderId);
        broadcast(channel, { type: 'message', payload, senderId, timestamp: Date.now() }, ws);
        break;

    case 'direct':
        handleDirectMessage(targetClientId, payload, senderId);
        break;

    case 'terminal_state':
        handleTerminalState(channel, sessionId, payload, senderId);
        broadcast(channel, { type: 'terminal_state', payload, senderId, timestamp: Date.now() }, ws);
        break;

    case 'command':
        broadcast(channel, { type: 'command', payload, senderId, timestamp: Date.now() }, ws);
        break;

    case 'create_session':
        handleCreateSession(ws, payload);
        break;

    case 'get_sessions':
        handleGetSessions(ws);
        break;

    case 'switch_session':
        handleSwitchSession(ws, payload.sessionId);
        break;

    case 'pause_session':
        handlePauseSession(ws, payload.sessionId);
        break;

    case 'resume_session':
        handleResumeSession(ws, payload.sessionId);
        break;

    case 'offline_message':
        handleOfflineMessage(channel, payload, senderId);
        ws.send(JSON.stringify({ type: 'offline_queued', timestamp: Date.now() }));
        break;

    case 'get_offline_messages':
        handleGetOfflineMessages(ws, channel, payload, senderId);
        break;

    case 'ping':
        ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
        break;

    default:
        logger.info(`Unknown message type: ${type}`);
    }
}

/**
 * HTTP请求处理 - 提供静态文件服务
 * @param {http.IncomingMessage} req
 * @param {http.ServerResponse} res
 */
function handleHttpRequest(req, res) {
    try {
        // 验证URL路径，防止路径遍历攻击
        const urlValidation = validateInput(req.url, 'string', {
            minLength: 1,
            maxLength: 500,
            pattern: /^[a-zA-Z0-9\-_\/\.]+$/
        });

        if (!urlValidation.valid) {
            logger.warn(`Invalid URL path: ${req.url}`);
            res.writeHead(HTTP_STATUS_NOT_FOUND);
            res.end('Invalid URL');
            return;
        }

        if (req.url === '/health') {
            res.writeHead(HTTP_STATUS_OK, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'ok' }));
            return;
        }

        let filePath = req.url === '/' ? '/test-client.html' : req.url;

        // 防止路径遍历
        const normalizedPath = path.normalize(filePath);
        if (normalizedPath.includes('..')) {
            logger.warn(`Path traversal attempt blocked: ${req.url}`);
            res.writeHead(HTTP_STATUS_NOT_FOUND);
            res.end('Not Found');
            return;
        }

        filePath = path.join(__dirname, '..', normalizedPath);

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
    } catch (error) {
        logger.error('HTTP request handling error:', error.message);
        res.writeHead(500);
        res.end('Internal Server Error');
    }
}

const httpServer = http.createServer(handleHttpRequest);

const wss = new WebSocket.Server({ server: httpServer });

wss.on('connection', (ws) => {
    logger.info('New client connected');
    ws.clientId = generateId();
    CLIENTS.set(ws.clientId, ws);

    ws.on('message', (data) => {
        try {
            const message = JSON.parse(data);
            handleMessage(ws, message);
        } catch (e) {
            logger.error('Failed to parse message:', e.message);
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
        logger.info('Client disconnected');
    });

    ws.on('error', (error) => {
        logger.error('WebSocket error:', error.message);
    });

    ws.send(JSON.stringify({ type: 'connected', clientId: ws.clientId }));
});

httpServer.listen(PORT, () => {
    logger.info(`Zhineng Bridge Relay Server running on port ${PORT}`);
    logger.info(`WebSocket endpoint: ws://localhost:${PORT}`);
    logger.info(`HTTP server: http://localhost:${PORT}`);
});
