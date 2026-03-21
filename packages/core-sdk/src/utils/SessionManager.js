const crypto = require('crypto');

class SessionManager {
  constructor() {
    this.sessions = new Map();
    this.listeners = new Map();
  }

  createSession(options = {}) {
    const id = options.id || crypto.randomBytes(8).toString('hex');
    const session = {
      id,
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
        screenSize: { rows: 24, cols: 80 }
      },
      messageHistory: [],
      variables: {},
      metadata: options.metadata || {}
    };

    this.sessions.set(id, session);
    this.emit('session_created', session);
    return session;
  }

  getSession(id) {
    return this.sessions.get(id);
  }

  getAllSessions() {
    return Array.from(this.sessions.values());
  }

  getActiveSessions() {
    return this.getAllSessions().filter(s => s.isActive && !s.isPaused);
  }

  updateSession(id, updates) {
    const session = this.sessions.get(id);
    if (session) {
      Object.assign(session, updates, { lastUpdate: Date.now() });
      this.emit('session_updated', session);
      return session;
    }
    return null;
  }

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

  deleteSession(id) {
    const session = this.sessions.get(id);
    if (session) {
      this.sessions.delete(id);
      this.emit('session_deleted', session);
      return true;
    }
    return false;
  }

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
      
      if (session.messageHistory.length > 1000) {
        session.messageHistory.shift();
      }
      
      this.emit('message_added', { sessionId: id, message: entry });
      return entry;
    }
    return null;
  }

  getMessages(id, options = {}) {
    const session = this.sessions.get(id);
    if (!session) return [];

    let messages = session.messageHistory;
    
    if (options.since) {
      messages = messages.filter(m => m.timestamp > options.since);
    }
    
    if (options.limit) {
      messages = messages.slice(-options.limit);
    }
    
    return messages;
  }

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

  setVariable(id, key, value) {
    const session = this.sessions.get(id);
    if (session) {
      session.variables[key] = value;
      session.lastUpdate = Date.now();
      return true;
    }
    return false;
  }

  getVariable(id, key) {
    const session = this.sessions.get(id);
    return session ? session.variables[key] : undefined;
  }

  serializeSession(id) {
    const session = this.sessions.get(id);
    if (!session) return null;

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
      console.error('Failed to deserialize session:', e);
      return null;
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index !== -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }
}

module.exports = { SessionManager };
