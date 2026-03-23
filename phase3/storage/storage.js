/**
 * 智桥 - IndexedDB 存储模块
 * 实现离线数据存储
 */

class StorageManager {
    constructor() {
        this.dbName = 'zhineng-bridge-db';
        this.dbVersion = 1;
        this.db = null;
        this.initialized = false;
    }

    /**
     * 初始化存储管理器
     */
    async init() {
        if (this.initialized) {
            console.warn('⚠️  存储管理器已初始化');
            return;
        }

        console.log('💾 初始化存储管理器');

        // 打开数据库
        this.db = await this.openDatabase();
        
        this.initialized = true;
        console.log('✅ 存储管理器已初始化');
    }

    /**
     * 打开数据库
     */
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

                // 创建会话存储
                if (!db.objectStoreNames.contains('sessions')) {
                    const sessionStore = db.createObjectStore('sessions', { keyPath: 'session_id' });
                    sessionStore.createIndex('tool_name', 'tool_name', { unique: false });
                    sessionStore.createIndex('status', 'status', { unique: false });
                    sessionStore.createIndex('created_at', 'created_at', { unique: false });
                    console.log('✅ 会话存储已创建');
                }

                // 创建输出存储
                if (!db.objectStoreNames.contains('outputs')) {
                    const outputStore = db.createObjectStore('outputs', { keyPath: 'output_id', autoIncrement: true });
                    outputStore.createIndex('session_id', 'session_id', { unique: false });
                    outputStore.createIndex('timestamp', 'timestamp', { unique: false });
                    console.log('✅ 输出存储已创建');
                }

                // 创建命令存储
                if (!db.objectStoreNames.contains('commands')) {
                    const commandStore = db.createObjectStore('commands', { keyPath: 'command_id', autoIncrement: true });
                    commandStore.createIndex('session_id', 'session_id', { unique: false });
                    commandStore.createIndex('timestamp', 'timestamp', { unique: false });
                    console.log('✅ 命令存储已创建');
                }

                // 创建密钥存储
                if (!db.objectStoreNames.contains('keys')) {
                    const keyStore = db.createObjectStore('keys', { keyPath: 'key_id' });
                    keyStore.createIndex('type', 'type', { unique: false });
                    keyStore.createIndex('created_at', 'created_at', { unique: false });
                    console.log('✅ 密钥存储已创建');
                }

                // 创建设置存储
                if (!db.objectStoreNames.contains('settings')) {
                    const settingStore = db.createObjectStore('settings', { keyPath: 'setting_id' });
                    console.log('✅ 设置存储已创建');
                }
            };
        });
    }

    /**
     * 保存会话
     */
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

    /**
     * 获取会话
     */
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

    /**
     * 获取所有会话
     */
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

    /**
     * 删除会话
     */
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

    /**
     * 保存输出
     */
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

    /**
     * 获取会话输出
     */
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

    /**
     * 保存命令
     */
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

    /**
     * 获取会话命令
     */
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

    /**
     * 保存密钥
     */
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

    /**
     * 获取密钥
     */
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

    /**
     * 保存设置
     */
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

    /**
     * 获取设置
     */
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

    /**
     * 清空所有数据
     */
    async clearAll() {
        if (!this.initialized) {
            await this.init();
        }

        const stores = ['sessions', 'outputs', 'commands', 'keys', 'settings'];
        
        for (const storeName of stores) {
            await new Promise((resolve, reject) => {
                const transaction = this.db.transaction([storeName], 'readwrite');
                const store = transaction.objectStore(store);
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

// 导出存储管理器
window.StorageManager = StorageManager;
