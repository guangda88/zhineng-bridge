#!/usr/bin/env node
/**
 * 智桥 CLI 工具
 * 用于与智桥服务进行交互，支持终端状态同步
 */

const WebSocket = require('ws');
const readline = require('readline');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

class ZhinengBridgeCLI {
  constructor() {
    this.ws = null;
    this.clientId = null;
    this.sessionId = null;
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: 'zhineng> '
    });
    this.config = this.loadConfig();
    this.terminalState = {
      commandHistory: [],
      currentInput: '',
      cursorPosition: 0,
      selection: null,
      outputHistory: []
    };
  }

  loadConfig() {
    const configPath = path.join(process.env.HOME || process.env.USERPROFILE, '.zhineng-bridge.json');
    try {
      if (fs.existsSync(configPath)) {
        return JSON.parse(fs.readFileSync(configPath, 'utf8'));
      }
    } catch (error) {
      console.error('Failed to load config:', error.message);
    }
    return {
      serverUrl: 'ws://100.66.1.8:8001',
      defaultChannel: 'default'
    };
  }

  saveConfig(config) {
    const configPath = path.join(process.env.HOME || process.env.USERPROFILE, '.zhineng-bridge.json');
    try {
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    } catch (error) {
      console.error('Failed to save config:', error.message);
    }
  }

  connect() {
    console.log(`Connecting to ${this.config.serverUrl}...`);
    
    this.ws = new WebSocket(this.config.serverUrl);

    this.ws.on('open', () => {
      console.log('Connected to Zhineng Bridge server');
      this.joinChannel(this.config.defaultChannel);
      this.startPrompt();
    });

    this.ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString());
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse message:', error.message);
      }
    });

    this.ws.on('error', (error) => {
      console.error('WebSocket error:', error.message);
    });

    this.ws.on('close', () => {
      console.log('Disconnected from server');
      this.rl.close();
    });
  }

  joinChannel(channel) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const joinMessage = {
        type: 'join',
        channel
      };
      this.ws.send(JSON.stringify(joinMessage));
      console.log(`Joining channel: ${channel}`);
    }
  }

  handleMessage(message) {
    switch (message.type) {
      case 'connected':
        this.clientId = message.clientId;
        console.log(`Assigned client ID: ${this.clientId}`);
        break;
      case 'joined':
        console.log(`Successfully joined channel: ${message.channel}`);
        break;
      case 'message':
        if (message.senderId !== this.clientId) {
          console.log(`\n[${message.senderId}] ${message.payload}`);
          this.rl.prompt();
        }
        break;
      case 'terminal_state':
        this.updateTerminalState(message.payload);
        break;
      case 'error':
        console.error(`Error: ${message.message}`);
        break;
      default:
        console.log(`Received message: ${JSON.stringify(message)}`);
    }
  }

  updateTerminalState(state) {
    this.terminalState = { ...this.terminalState, ...state };
    console.log('Terminal state updated:', state);
  }

  sendTerminalState() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const stateMessage = {
        type: 'terminal_state',
        payload: this.terminalState
      };
      this.ws.send(JSON.stringify(stateMessage));
    }
  }

  startPrompt() {
    this.rl.prompt();
    
    this.rl.on('line', (line) => {
      const command = line.trim();
      
      if (command === 'exit') {
        this.disconnect();
        return;
      }
      
      if (command === 'help') {
        this.showHelp();
        this.rl.prompt();
        return;
      }
      
      if (command === 'status') {
        this.showStatus();
        this.rl.prompt();
        return;
      }
      
      // 发送消息
      this.sendMessage(command);
      
      // 更新终端状态
      this.terminalState.commandHistory.push(command);
      this.terminalState.currentInput = '';
      this.terminalState.cursorPosition = 0;
      this.sendTerminalState();
      
      this.rl.prompt();
    }).on('close', () => {
      console.log('Exiting Zhineng Bridge CLI');
      process.exit(0);
    });
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const payload = {
        type: 'message',
        channel: this.config.defaultChannel,
        payload: message
      };
      this.ws.send(JSON.stringify(payload));
      console.log(`[You] ${message}`);
    } else {
      console.error('Not connected to server');
    }
  }

  showHelp() {
    console.log('\nZhineng Bridge CLI Commands:');
    console.log('  exit        - Disconnect and exit');
    console.log('  help        - Show this help message');
    console.log('  status      - Show connection status');
    console.log('  Any other text will be sent as a message');
  }

  showStatus() {
    console.log('\nConnection Status:');
    console.log(`  Server: ${this.config.serverUrl}`);
    console.log(`  Client ID: ${this.clientId}`);
    console.log(`  Channel: ${this.config.defaultChannel}`);
    console.log(`  WebSocket State: ${this.ws ? this.getWebSocketState() : 'Disconnected'}`);
  }

  getWebSocketState() {
    if (!this.ws) return 'Disconnected';
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'Connecting';
      case WebSocket.OPEN:
        return 'Connected';
      case WebSocket.CLOSING:
        return 'Closing';
      case WebSocket.CLOSED:
        return 'Closed';
      default:
        return 'Unknown';
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
    this.rl.close();
  }
}

// 启动CLI
if (require.main === module) {
  const cli = new ZhinengBridgeCLI();
  cli.connect();
}

module.exports = ZhinengBridgeCLI;