#!/usr/bin/env node

/**
 * @fileoverview Zhineng Bridge CLI
 * 命令行客户端，提供与中继服务器的WebSocket连接和交互式终端
 * @module cli/index
 */

const WebSocket = require('ws');
const readline = require('readline');
const crypto = require('crypto');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const DEFAULT_SERVER_URL = 'ws://localhost:8001';
const DEFAULT_CHANNEL = 'default';
const RECONNECT_DELAY_MS = 3000;

class ZhinengBridgeCLI {
  constructor() {
    this.ws = null;
    this.clientId = null;
    this.channel = DEFAULT_CHANNEL;
    this.sessionId = null;
    this.terminalState = {
      commandHistory: [],
      currentInput: '',
      cursorPosition: 0,
      selection: null,
      outputHistory: [],
      screenSize: { rows: 24, cols: 80 }
    };
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: 'zhineng> '
    });
    this.config = this.loadConfig();
  }

  /**
   * 加载配置文件
   * @returns {Object} 配置对象
   */
  loadConfig() {
    const configPath = path.join(process.env.HOME || process.env.USERPROFILE, '.zhineng-bridge', 'config.json');
    try {
      if (fs.existsSync(configPath)) {
        return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      }
    } catch (e) {
      console.error('Failed to load config:', e.message);
    }
    return {
      serverUrl: process.env.ZHINENG_SERVER || DEFAULT_SERVER_URL,
      defaultChannel: DEFAULT_CHANNEL,
      encryption: {
        enabled: false,
        key: null
      }
    };
  }

  saveConfig() {
    const configDir = path.join(process.env.HOME || process.env.USERPROFILE, '.zhineng-bridge');
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
    const configPath = path.join(configDir, 'config.json');
    fs.writeFileSync(configPath, JSON.stringify(this.config, null, 2));
  }

  connect() {
    return new Promise((resolve, reject) => {
      console.log(`Connecting to ${this.config.serverUrl}...`);

      this.ws = new WebSocket(this.config.serverUrl);

      this.ws.on('open', () => {
        console.log('Connected to Zhineng Bridge server');
        this.joinChannel(this.config.defaultChannel);
        resolve();
      });

      this.ws.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          this.handleMessage(message);
        } catch (e) {
          console.error('Failed to parse message:', e.message);
        }
      });

      this.ws.on('close', () => {
        console.log('Disconnected from server');
        this.reconnect();
      });

      this.ws.on('error', (error) => {
        console.error('Connection error:', error.message);
        reject(error);
      });
    });
  }

  reconnect() {
    console.log(`Reconnecting in ${RECONNECT_DELAY_MS / 1000} seconds...`);
    setTimeout(() => {
      this.connect().catch(console.error);
    }, RECONNECT_DELAY_MS);
  }

  joinChannel(channel) {
    this.channel = channel;
    this.send({ type: 'join', channel });
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  /**
   * 处理服务器消息
   * @param {Object} message - 消息对象
   */
  handleMessage(message) {
    switch (message.type) {
      case 'connected':
        this.clientId = message.clientId;
        console.log(`Client ID: ${this.clientId}`);
        break;

      case 'joined':
        console.log(`Joined channel: ${message.channel}`);
        this.startPrompt();
        break;

      case 'message':
        console.log(`\n[${message.senderId}]: ${message.payload.content}`);
        this.sendMessage(`Echo: ${message.payload.content}`);
        this.rl.prompt(true);
        break;

      case 'terminal_state':
        this.syncTerminalState(message.payload);
        break;

      case 'command':
        this.executeRemoteCommand(message.payload);
        break;

      case 'session_created':
        this.sessionId = message.session.id;
        console.log(`\nSession created: ${message.session.name} (${message.session.id})`);
        this.rl.prompt(true);
        break;

      case 'sessions_list':
        console.log('\n=== Sessions ===');
        message.sessions.forEach(s => {
          console.log(`${s.id.slice(0, 8)} - ${s.name} (${s.isActive ? 'active' : 'paused'})`);
        });
        this.rl.prompt(true);
        break;

      case 'session_state':
        this.restoreSessionState(message.payload);
        break;

      case 'offline_messages':
        if (message.messages && message.messages.length > 0) {
          console.log(`\nReceived ${message.messages.length} offline message(s)`);
          message.messages.forEach(m => {
            if (m.type === 'offline') {
              console.log(`[Offline] ${m.encryptedContent ? '(encrypted)' : m.content}`);
            }
          });
        }
        this.rl.prompt(true);
        break;

      case 'pong':
        break;

      default:
        console.log(`\nUnknown message:`, message);
        this.rl.prompt(true);
    }
  }

  syncTerminalState(state) {
    this.terminalState = { ...this.terminalState, ...state };
    console.log('\r[Terminal state synced]');
    this.rl.prompt(true);
  }

  /**
   * 执行远程命令
   * @param {Object} payload - 命令载荷
   */
  executeRemoteCommand(payload) {
    const { command, sessionId } = payload;
    console.log(`\n[Executing remote command]: ${command}`);

    const child = spawn(command, [], {
      shell: true,
      cwd: process.cwd()
    });

    let output = '';
    child.stdout.on('data', (data) => {
      output += data.toString();
      process.stdout.write(data);
    });

    child.stderr.on('data', (data) => {
      process.stderr.write(data);
    });

    child.on('close', (code) => {
      this.send({
        type: 'command_result',
        payload: { command, output, exitCode: code, sessionId }
      });
      this.rl.prompt(true);
    });
  }

  startPrompt() {
    this.rl.prompt();

    this.rl.on('line', (line) => {
      const input = line.trim();

      if (input.startsWith('/')) {
        this.handleCommand(input);
      } else if (input) {
        this.sendMessage(input);
      }

      this.terminalState.commandHistory.push(input);
      this.terminalState.currentInput = '';
      this.rl.prompt(true);
    });

    this.rl.on('close', () => {
      console.log('\nGoodbye!');
      process.exit(0);
    });
  }

  /**
   * 处理CLI命令
   * @param {string} input - 命令输入
   */
  handleCommand(input) {
    const parts = input.split(' ');
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);

    switch (cmd) {
      case '/help':
        console.log(`
Commands:
  /join <channel>     Join a channel
  /leave               Leave current channel
  /sessions            List all sessions
  /create <name>      Create a new session
  /switch <id>         Switch to a session
  /pause               Pause current session
  /resume              Resume current session
  /sync                Force terminal state sync
  /offline             Get offline messages
  /quit                Exit CLI
        `);
        break;

      case '/join':
        if (args[0]) {
          this.send({ type: 'leave', channel: this.channel });
          this.joinChannel(args[0]);
        }
        break;

      case '/leave':
        this.send({ type: 'leave', channel: this.channel });
        break;

      case '/sessions':
        this.send({ type: 'get_sessions' });
        break;

      case '/create':
        this.send({
          type: 'create_session',
          payload: { name: args.join(' ') || 'Unnamed Session' }
        });
        break;

      case '/switch':
        if (args[0]) {
          this.send({ type: 'switch_session', payload: { sessionId: args[0] } });
        }
        break;

      case '/pause':
        if (this.sessionId) {
          this.send({ type: 'pause_session', payload: { sessionId: this.sessionId } });
        }
        break;

      case '/resume':
        if (this.sessionId) {
          this.send({ type: 'resume_session', payload: { sessionId: this.sessionId } });
        }
        break;

      case '/sync':
        this.send({
          type: 'terminal_state',
          channel: this.channel,
          payload: this.terminalState
        });
        console.log('Terminal state synced');
        break;

      case '/offline':
        this.send({
          type: 'get_offline_messages',
          channel: this.channel,
          payload: { since: 0 }
        });
        break;

      case '/quit':
      case '/exit':
        this.rl.close();
        break;

      default:
        console.log(`Unknown command: ${cmd}`);
    }
  }

  sendMessage(content) {
    this.send({
      type: 'message',
      channel: this.channel,
      payload: { content }
    });

    this.terminalState.outputHistory.push({
      type: 'sent',
      content,
      timestamp: Date.now()
    });
  }

  restoreSessionState(session) {
    this.sessionId = session.id;
    if (session.terminalState) {
      this.terminalState = session.terminalState;
    }
    if (session.messageHistory) {
      this.terminalState.outputHistory = session.messageHistory;
    }
    console.log(`\nRestored session: ${session.name}`);
  }
}

const cli = new ZhinengBridgeCLI();
cli.connect().catch(console.error);
