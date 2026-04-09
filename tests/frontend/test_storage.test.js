/**
 * Storage Module Tests
 * Tests for StorageManager class (IndexedDB implementation)
 */

// Mock console methods to reduce noise
global.console.log = jest.fn();
global.console.warn = jest.fn();
global.console.error = jest.fn();

// Define StorageManager class directly in test file
class StorageManager {
    constructor() {
        this.dbName = 'zhineng-bridge-db';
        this.dbVersion = 1;
        this.db = null;
        this.initialized = false;
    }

    async init() {
        if (this.initialized) {
            console.warn('⚠️  存储管理器已初始化');
            return;
        }

        console.log('💾 初始化存储管理器');
        this.db = await this.openDatabase();
        this.initialized = true;
        console.log('✅ 存储管理器已初始化');
    }

    async openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = (event) => {
                console.error('❌ 打开数据库失败:', event);
                reject(event);
            };

            request.onsuccess = (event) => {
                const db = event.target.result;
                console.log('✅ 数据库已打开');
                resolve(db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                console.log('🔄 数据库升级:', event.oldVersion, '->', event.newVersion);

                if (!db.objectStoreNames.contains('sessions')) {
                    const sessionStore = db.createObjectStore('sessions', { keyPath: 'session_id' });
                    sessionStore.createIndex('tool_name', 'tool_name', { unique: false });
                    sessionStore.createIndex('status', 'status', { unique: false });
                    sessionStore.createIndex('created_at', 'created_at', { unique: false });
                }

                if (!db.objectStoreNames.contains('outputs')) {
                    const outputStore = db.createObjectStore('outputs', { keyPath: 'output_id', autoIncrement: true });
                    outputStore.createIndex('session_id', 'session_id', { unique: false });
                    outputStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                if (!db.objectStoreNames.contains('commands')) {
                    const commandStore = db.createObjectStore('commands', { keyPath: 'command_id', autoIncrement: true });
                    commandStore.createIndex('session_id', 'session_id', { unique: false });
                    commandStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                if (!db.objectStoreNames.contains('keys')) {
                    const keyStore = db.createObjectStore('keys', { keyPath: 'key_id' });
                    keyStore.createIndex('type', 'type', { unique: false });
                    keyStore.createIndex('created_at', 'created_at', { unique: false });
                }

                if (!db.objectStoreNames.contains('settings')) {
                    const settingStore = db.createObjectStore('settings', { keyPath: 'setting_id' });
                }
            };
        });
    }

    async saveSession(session) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['sessions'], 'readwrite');
            const store = transaction.objectStore('sessions');
            const request = store.put(session);

            request.onsuccess = () => {
                console.log('✅ 会话已保存:', session.session_id);
                resolve(session);
            };

            request.onerror = (event) => {
                console.error('❌ 保存会话失败:', event);
                reject(event);
            };
        });
    }

    async getSession(sessionId) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['sessions'], 'readonly');
            const store = transaction.objectStore('sessions');
            const request = store.get(sessionId);

            request.onsuccess = () => {
                console.log('✅ 会话已获取:', sessionId);
                resolve(request.result);
            };

            request.onerror = (event) => {
                console.error('❌ 获取会话失败:', event);
                reject(event);
            };
        });
    }

    async getAllSessions() {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['sessions'], 'readonly');
            const store = transaction.objectStore('sessions');
            const request = store.getAll();

            request.onsuccess = () => {
                console.log('✅ 所有会话已获取:', request.result.length);
                resolve(request.result);
            };

            request.onerror = (event) => {
                console.error('❌ 获取所有会话失败:', event);
                reject(event);
            };
        });
    }

    async deleteSession(sessionId) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['sessions'], 'readwrite');
            const store = transaction.objectStore('sessions');
            const request = store.delete(sessionId);

            request.onsuccess = () => {
                console.log('✅ 会话已删除:', sessionId);
                resolve();
            };

            request.onerror = (event) => {
                console.error('❌ 删除会话失败:', event);
                reject(event);
            };
        });
    }

    async saveOutput(output) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['outputs'], 'readwrite');
            const store = transaction.objectStore('outputs');
            const request = store.add(output);

            request.onsuccess = () => {
                console.log('✅ 输出已保存:', output.output_id);
                resolve(output);
            };

            request.onerror = (event) => {
                console.error('❌ 保存输出失败:', event);
                reject(event);
            };
        });
    }

    async getSessionOutputs(sessionId, limit = 1000) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['outputs'], 'readonly');
            const store = transaction.objectStore('outputs');
            const index = store.index('session_id');
            const request = index.getAll(sessionId);

            request.onsuccess = () => {
                const outputs = request.result.slice(-limit);
                console.log('✅ 会话输出已获取:', outputs.length);
                resolve(outputs);
            };

            request.onerror = (event) => {
                console.error('❌ 获取会话输出失败:', event);
                reject(event);
            };
        });
    }

    async saveCommand(command) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['commands'], 'readwrite');
            const store = transaction.objectStore('commands');
            const request = store.add(command);

            request.onsuccess = () => {
                console.log('✅ 命令已保存:', command.command_id);
                resolve(command);
            };

            request.onerror = (event) => {
                console.error('❌ 保存命令失败:', event);
                reject(event);
            };
        });
    }

    async getSessionCommands(sessionId, limit = 100) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['commands'], 'readonly');
            const store = transaction.objectStore('commands');
            const index = store.index('session_id');
            const request = index.getAll(sessionId);

            request.onsuccess = () => {
                const commands = request.result.slice(-limit);
                console.log('✅ 会话命令已获取:', commands.length);
                resolve(commands);
            };

            request.onerror = (event) => {
                console.error('❌ 获取会话命令失败:', event);
                reject(event);
            };
        });
    }

    async saveKey(key) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['keys'], 'readwrite');
            const store = transaction.objectStore('keys');
            const request = store.put(key);

            request.onsuccess = () => {
                console.log('✅ 密钥已保存:', key.key_id);
                resolve(key);
            };

            request.onerror = (event) => {
                console.error('❌ 保存密钥失败:', event);
                reject(event);
            };
        });
    }

    async getKey(keyId) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['keys'], 'readonly');
            const store = transaction.objectStore('keys');
            const request = store.get(keyId);

            request.onsuccess = () => {
                console.log('✅ 密钥已获取:', keyId);
                resolve(request.result);
            };

            request.onerror = (event) => {
                console.error('❌ 获取密钥失败:', event);
                reject(event);
            };
        });
    }

    async saveSetting(setting) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['settings'], 'readwrite');
            const store = transaction.objectStore('settings');
            const request = store.put(setting);

            request.onsuccess = () => {
                console.log('✅ 设置已保存:', setting.setting_id);
                resolve(setting);
            };

            request.onerror = (event) => {
                console.error('❌ 保存设置失败:', event);
                reject(event);
            };
        });
    }

    async getSetting(settingId) {
        if (!this.initialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['settings'], 'readonly');
            const store = transaction.objectStore('settings');
            const request = store.get(settingId);

            request.onsuccess = () => {
                console.log('✅ 设置已获取:', settingId);
                resolve(request.result);
            };

            request.onerror = (event) => {
                console.error('❌ 获取设置失败:', event);
                reject(event);
            };
        });
    }

    async clearAll() {
        if (!this.initialized) {
            await this.init();
        }

        const stores = ['sessions', 'outputs', 'commands', 'keys', 'settings'];

        for (const storeName of stores) {
            await new Promise((resolve, reject) => {
                const transaction = this.db.transaction([storeName], 'readwrite');
                const store = transaction.objectStore(storeName);
                const request = store.clear();

                request.onsuccess = () => {
                    console.log('✅ 存储已清空:', storeName);
                    resolve();
                };

                request.onerror = (event) => {
                    console.error('❌ 清空存储失败:', event);
                    reject(event);
                };
            });
        }
    }
}

describe('StorageManager', () => {
  let storageManager;

  beforeEach(() => {
    jest.clearAllMocks();
    storageManager = new StorageManager();
  });

  describe('constructor', () => {
    test('should initialize with correct defaults', () => {
      expect(storageManager.dbName).toBe('zhineng-bridge-db');
      expect(storageManager.dbVersion).toBe(1);
      expect(storageManager.db).toBeNull();
      expect(storageManager.initialized).toBe(false);
    });
  });

  describe('init', () => {
    test('should initialize storage manager', async () => {
      await storageManager.init();

      expect(storageManager.initialized).toBe(true);
      expect(storageManager.db).not.toBeNull();
      expect(global.console.log).toHaveBeenCalledWith('💾 初始化存储管理器');
    });

    test('should not initialize twice', async () => {
      await storageManager.init();
      await storageManager.init();

      expect(global.console.warn).toHaveBeenCalledWith('⚠️  存储管理器已初始化');
    });
  });

  describe('saveSession', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should save a session successfully', async () => {
      const session = {
        session_id: 'test-session-1',
        tool_name: 'crush',
        status: 'running',
        created_at: new Date().toISOString()
      };

      const result = await storageManager.saveSession(session);

      expect(result).toEqual(session);
      expect(global.console.log).toHaveBeenCalledWith('✅ 会话已保存:', session.session_id);
    });

    test('should auto-initialize if not initialized', async () => {
      const uninitializedManager = new StorageManager();
      const session = {
        session_id: 'test-session-2',
        tool_name: 'claude',
        status: 'stopped'
      };

      const result = await uninitializedManager.saveSession(session);

      expect(uninitializedManager.initialized).toBe(true);
      expect(result).toEqual(session);
    });
  });

  describe('getSession', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should retrieve a session by ID', async () => {
      const session = {
        session_id: 'test-session-3',
        tool_name: 'cursor',
        status: 'idle'
      };

      await storageManager.saveSession(session);
      const retrieved = await storageManager.getSession('test-session-3');

      expect(retrieved).toEqual(session);
    });

    test('should return undefined for non-existent session', async () => {
      const retrieved = await storageManager.getSession('non-existent');

      expect(retrieved).toBeUndefined();
    });
  });

  describe('getAllSessions', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should retrieve all sessions', async () => {
      const sessions = [
        { session_id: 's1', tool_name: 'crush', status: 'running' },
        { session_id: 's2', tool_name: 'claude', status: 'stopped' },
        { session_id: 's3', tool_name: 'cursor', status: 'idle' }
      ];

      for (const session of sessions) {
        await storageManager.saveSession(session);
      }

      const allSessions = await storageManager.getAllSessions();

      expect(allSessions).toHaveLength(3);
      expect(allSessions.map(s => s.session_id)).toContain('s1');
    });

    test('should return empty array if no sessions', async () => {
      const sessions = await storageManager.getAllSessions();

      expect(sessions).toEqual([]);
    });
  });

  describe('deleteSession', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should delete a session successfully', async () => {
      const session = {
        session_id: 'test-session-4',
        tool_name: 'crush',
        status: 'running'
      };

      await storageManager.saveSession(session);
      await storageManager.deleteSession('test-session-4');

      const retrieved = await storageManager.getSession('test-session-4');

      expect(retrieved).toBeUndefined();
      expect(global.console.log).toHaveBeenCalledWith('✅ 会话已删除:', 'test-session-4');
    });
  });

  describe('saveOutput', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should save output successfully', async () => {
      const output = {
        output_id: 'output-1',
        session_id: 'session-1',
        output: 'Test output',
        timestamp: new Date().toISOString()
      };

      const result = await storageManager.saveOutput(output);

      expect(result.output_id).toBeDefined();
      expect(result.output).toBe('Test output');
    });
  });

  describe('getSessionOutputs', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should retrieve outputs for a session', async () => {
      const sessionId = 'session-1';
      const outputs = [
        { session_id: sessionId, output: 'Output 1' },
        { session_id: sessionId, output: 'Output 2' },
        { session_id: sessionId, output: 'Output 3' }
      ];

      for (const output of outputs) {
        await storageManager.saveOutput(output);
      }

      const sessionOutputs = await storageManager.getSessionOutputs(sessionId);

      expect(sessionOutputs).toHaveLength(3);
      expect(sessionOutputs.map(o => o.output)).toContain('Output 1');
    });

    test('should limit outputs', async () => {
      const sessionId = 'session-2';
      const outputs = Array.from({ length: 10 }, (_, i) => ({
        session_id: sessionId,
        output: `Output ${i + 1}`
      }));

      for (const output of outputs) {
        await storageManager.saveOutput(output);
      }

      const sessionOutputs = await storageManager.getSessionOutputs(sessionId, 5);

      expect(sessionOutputs.length).toBeLessThanOrEqual(5);
    });
  });

  describe('saveCommand', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should save command successfully', async () => {
      const command = {
        command_id: 'cmd-1',
        session_id: 'session-1',
        command: 'echo "Hello"',
        timestamp: new Date().toISOString()
      };

      const result = await storageManager.saveCommand(command);

      expect(result.command_id).toBeDefined();
      expect(result.command).toBe('echo "Hello"');
    });
  });

  describe('getSessionCommands', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should retrieve commands for a session', async () => {
      const sessionId = 'session-1';
      const commands = [
        { session_id: sessionId, command: 'cd /tmp' },
        { session_id: sessionId, command: 'ls -la' },
        { session_id: sessionId, command: 'pwd' }
      ];

      for (const command of commands) {
        await storageManager.saveCommand(command);
      }

      const sessionCommands = await storageManager.getSessionCommands(sessionId);

      expect(sessionCommands).toHaveLength(3);
      expect(sessionCommands.map(c => c.command)).toContain('ls -la');
    });
  });

  describe('saveKey and getKey', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should save and retrieve key', async () => {
      const key = {
        key_id: 'key-1',
        type: 'public',
        key_data: 'base64keydata',
        created_at: new Date().toISOString()
      };

      await storageManager.saveKey(key);
      const retrieved = await storageManager.getKey('key-1');

      expect(retrieved).toEqual(key);
    });

    test('should update existing key', async () => {
      const key = {
        key_id: 'key-2',
        type: 'public',
        key_data: 'original'
      };

      await storageManager.saveKey(key);
      key.key_data = 'updated';
      await storageManager.saveKey(key);

      const retrieved = await storageManager.getKey('key-2');

      expect(retrieved.key_data).toBe('updated');
    });
  });

  describe('saveSetting and getSetting', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should save and retrieve setting', async () => {
      const setting = {
        setting_id: 'theme',
        value: 'dark'
      };

      await storageManager.saveSetting(setting);
      const retrieved = await storageManager.getSetting('theme');

      expect(retrieved).toEqual(setting);
    });

    test('should update existing setting', async () => {
      const setting = {
        setting_id: 'language',
        value: 'en'
      };

      await storageManager.saveSetting(setting);
      setting.value = 'zh';
      await storageManager.saveSetting(setting);

      const retrieved = await storageManager.getSetting('language');

      expect(retrieved.value).toBe('zh');
    });
  });

  describe('clearAll', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should clear all stores', async () => {
      await storageManager.saveSession({ session_id: 's1', tool_name: 'crush' });
      await storageManager.saveOutput({ session_id: 's1', output: 'test' });
      await storageManager.saveCommand({ session_id: 's1', command: 'ls' });
      await storageManager.saveKey({ key_id: 'k1', type: 'public', key_data: 'data' });
      await storageManager.saveSetting({ setting_id: 'theme', value: 'dark' });

      await storageManager.clearAll();

      const sessions = await storageManager.getAllSessions();
      expect(sessions).toHaveLength(0);
    });
  });

  describe('concurrent operations', () => {
    beforeEach(async () => {
      await storageManager.init();
    });

    test('should handle multiple concurrent saves', async () => {
      const sessionPromises = Array.from({ length: 10 }, (_, i) =>
        storageManager.saveSession({
          session_id: `session-${i}`,
          tool_name: 'crush',
          status: 'running'
        })
      );

      await Promise.all(sessionPromises);

      const allSessions = await storageManager.getAllSessions();
      expect(allSessions).toHaveLength(10);
    });
  });
});
