/**
 * @fileoverview Zhineng Bridge Session Manager
 * 提供会话管理、状态同步和消息历史功能
 * @module core-sdk/src/utils/SessionManager
 */

const crypto = require('crypto');

// Simple logger for SessionManager
class Logger {
    constructor(name) {
        this.name = name;
    }
    error(message, ...args) {
        // console.error(`[ERROR] ${this.name}:`, message, ...args);
    }
}

const logger = new Logger('SessionManager');

const DEFAULT_SCREEN_ROWS = 24;
const DEFAULT_SCREEN_COLS = 80;
const MAX_MESSAGE_HISTORY = 1000;

class SessionManager {
    constructor() {
        this.sessions = new Map();
        this.listeners = new Map();
    }

    /**
   * 创建新会话
   * @param {Object} options - 会话选项
   * @returns {Object} 创建的会话对象
   */
    createSession(options = {}) {
        const id = options.id || crypto.randomBytes(8).toString('hex');
        const session = {
            id: id,
            name: options.name || `Session ${id.slice(0, 8)}`,
            projectContext: options.projectContext || '',
            workingDirectory: options.workingDirectory || process.cwd(),
            createdAt: Date.now(),
            lastUpdate: Date.now(),
            isActive: true,
            isPaused: false,
            terminalState: {
                commandHistory: [],
                currentInput: '',
                cursorPosition: 0,
                selection: null,
                outputHistory: [],
                screenSize: { rows: DEFAULT_SCREEN_ROWS, cols: DEFAULT_SCREEN_COLS }
            },
            messageHistory: [],
            variables: {},
            metadata: options.metadata || {}
        };

        this.sessions.set(id, session);
        this.emit('session_created', session);
        return session;
    }

    /**
   * 获取会话
   * @param {string} id - 会话ID
   * @returns {Object|null} 会话对象
   */
    getSession(id) {
        return this.sessions.get(id);
    }

    /**
   * 获取所有会话
   * @returns {Array} 会话列表
   */
    getAllSessions() {
        return Array.from(this.sessions.values());
    }

    /**
   * 获取活动会话
   * @returns {Array} 活动会话列表
   */
    getActiveSessions() {
        return this.getAllSessions().filter(s => s.isActive && !s.isPaused);
    }

    /**
   * 更新会话
   * @param {string} id - 会话ID
   * @param {Object} updates - 更新内容
   * @returns {Object|null} 更新后的会话
   */
    updateSession(id, updates) {
        const session = this.sessions.get(id);
        if (session) {
            Object.assign(session, updates, { lastUpdate: Date.now() });
            this.emit('session_updated', session);
            return session;
        }
        return null;
    }

    /**
   * 暂停会话
   * @param {string} id - 会话ID
   * @returns {Object|null} 暂停的会话
   */
    pauseSession(id) {
        const session = this.sessions.get(id);
        if (session) {
            session.isPaused = true;
            session.lastUpdate = Date.now();
            this.emit('session_paused', session);
            return session;
        }
        return null;
    }

    /**
   * 恢复会话
   * @param {string} id - 会话ID
   * @returns {Object|null} 恢复的会话
   */
    resumeSession(id) {
        const session = this.sessions.get(id);
        if (session) {
            session.isPaused = false;
            session.isActive = true;
            session.lastUpdate = Date.now();
            this.emit('session_resumed', session);
            return session;
        }
        return null;
    }

    /**
   * 删除会话
   * @param {string} id - 会话ID
   * @returns {boolean} 是否成功删除
   */
    deleteSession(id) {
        const session = this.sessions.get(id);
        if (session) {
            this.sessions.delete(id);
            this.emit('session_deleted', session);
            return true;
        }
        return false;
    }

    /**
   * 添加消息到会话
   * @param {string} id - 会话ID
   * @param {Object} message - 消息对象
   * @returns {Object|null} 添加的消息条目
   */
    addMessage(id, message) {
        const session = this.sessions.get(id);
        if (session) {
            const entry = {
                id: crypto.randomBytes(8).toString('hex'),
                type: message.type || 'user',
                content: message.content,
                timestamp: Date.now(),
                metadata: message.metadata || {}
            };
            session.messageHistory.push(entry);
            session.lastUpdate = Date.now();

            if (session.messageHistory.length > MAX_MESSAGE_HISTORY) {
                session.messageHistory.shift();
            }

            this.emit('message_added', { sessionId: id, message: entry });
            return entry;
        }
        return null;
    }

    /**
   * 获取会话消息
   * @param {string} id - 会话ID
   * @param {Object} options - 查询选项
   * @returns {Array} 消息列表
   */
    getMessages(id, options = {}) {
        const session = this.sessions.get(id);
        if (!session) {return [];}

        let messages = session.messageHistory;

        if (options.since) {
            messages = messages.filter(m => m.timestamp > options.since);
        }

        if (options.limit) {
            messages = messages.slice(-options.limit);
        }

        return messages;
    }

    /**
   * 更新终端状态
   * @param {string} id - 会话ID
   * @param {Object} state - 终端状态
   * @returns {Object|null} 更新后的终端状态
   */
    updateTerminalState(id, state) {
        const session = this.sessions.get(id);
        if (session) {
            session.terminalState = { ...session.terminalState, ...state };
            session.lastUpdate = Date.now();
            this.emit('terminal_state_updated', { sessionId: id, state: session.terminalState });
            return session.terminalState;
        }
        return null;
    }

    /**
   * 设置会话变量
   * @param {string} id - 会话ID
   * @param {string} key - 变量名
   * @param {*} value - 变量值
   * @returns {boolean} 是否设置成功
   */
    setVariable(id, key, value) {
        const session = this.sessions.get(id);
        if (session) {
            session.variables[key] = value;
            session.lastUpdate = Date.now();
            return true;
        }
        return false;
    }

    /**
   * 获取会话变量
   * @param {string} id - 会话ID
   * @param {string} key - 变量名
   * @returns {*} 变量值
   */
    getVariable(id, key) {
        const session = this.sessions.get(id);
        return session ? session.variables[key] : undefined;
    }

    /**
   * 序列化会话
   * @param {string} id - 会话ID
   * @returns {string|null} JSON字符串
   */
    serializeSession(id) {
        const session = this.sessions.get(id);
        if (!session) {return null;}

        return JSON.stringify({
            id: session.id,
            name: session.name,
            projectContext: session.projectContext,
            workingDirectory: session.workingDirectory,
            createdAt: session.createdAt,
            lastUpdate: session.lastUpdate,
            isActive: session.isActive,
            isPaused: session.isPaused,
            terminalState: session.terminalState,
            messageHistory: session.messageHistory,
            variables: session.variables,
            metadata: session.metadata
        });
    }

    /**
   * 反序列化会话
   * @param {string} json - JSON字符串
   * @returns {Object|null} 会话对象
   */
    deserializeSession(json) {
        try {
            const data = JSON.parse(json);
            const session = this.createSession({
                id: data.id,
                name: data.name,
                projectContext: data.projectContext,
                workingDirectory: data.workingDirectory,
                metadata: data.metadata
            });

            session.createdAt = data.createdAt;
            session.lastUpdate = data.lastUpdate;
            session.isActive = data.isActive;
            session.isPaused = data.isPaused;
            session.terminalState = data.terminalState;
            session.messageHistory = data.messageHistory;
            session.variables = data.variables;

            return session;
        } catch (e) {
            logger.error('Failed to deserialize session:', e.message);
            return null;
        }
    }

    /**
   * 注册事件监听器
   * @param {string} event - 事件名称
   * @param {Function} callback - 回调函数
   */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
   * 移除事件监听器
   * @param {string} event - 事件名称
   * @param {Function} callback - 回调函数
   */
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index !== -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
   * 触发事件
   * @param {string} event - 事件名称
   * @param {*} data - 事件数据
   */
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => callback(data));
        }
    }
}

module.exports = { SessionManager };
