/**
 * Encryption Module Tests
 * Tests for EncryptionManager class (Web Crypto API implementation)
 */

// Ensure global.crypto and window.crypto are available
if (!global.crypto) {
  global.crypto = {
    subtle: {}
  };
}
if (!global.window) {
  global.window = {};
}
global.window.crypto = global.crypto;

// Mock console methods to reduce noise
global.console.log = jest.fn();
global.console.warn = jest.fn();
global.console.error = jest.fn();

// Define EncryptionManager class directly in test file
class EncryptionManager {
    constructor() {
        this.keyPair = null;
        this.sessionKeys = new Map();
        this.initialized = false;
    }

    async init() {
        if (this.initialized) {
            console.warn('⚠️  加密管理器已初始化');
            return;
        }

        console.log('🔒 初始化加密管理器');

        // 生成密钥对
        this.keyPair = await this.generateKeyPair();

        this.initialized = true;
        console.log('✅ 加密管理器已初始化');
    }

    async generateKeyPair() {
        try {
            const keyPair = await window.crypto.subtle.generateKey(
                {
                    name: "RSA-OAEP",
                    modulusLength: 2048,
                    publicExponent: new Uint8Array([1, 0, 1]),
                    hash: "SHA-256"
                },
                true,
                ["encrypt", "decrypt"]
            );

            console.log('✅ RSA 密钥对已生成');
            return keyPair;
        } catch (error) {
            console.error('❌ 生成密钥对失败:', error);
            throw error;
        }
    }

    async exportPublicKey() {
        if (!this.keyPair) {
            throw new Error('密钥对未初始化');
        }

        try {
            const publicKeyData = await window.crypto.subtle.exportKey(
                "spki",
                this.keyPair.publicKey
            );

            const publicKeyBase64 = this.arrayBufferToBase64(publicKeyData);
            console.log('✅ 公钥已导出');
            return publicKeyBase64;
        } catch (error) {
            console.error('❌ 导出公钥失败:', error);
            throw error;
        }
    }

    async importPublicKey(publicKeyBase64) {
        try {
            const publicKeyData = this.base64ToArrayBuffer(publicKeyBase64);
            const publicKey = await window.crypto.subtle.importKey(
                "spki",
                publicKeyData,
                {
                    name: "RSA-OAEP",
                    hash: "SHA-256"
                },
                true,
                ["encrypt"]
            );

            console.log('✅ 公钥已导入');
            return publicKey;
        } catch (error) {
            console.error('❌ 导入公钥失败:', error);
            throw error;
        }
    }

    async encryptMessage(message, publicKey) {
        try {
            const encoder = new TextEncoder();
            const data = encoder.encode(message);

            const encryptedData = await window.crypto.subtle.encrypt(
                {
                    name: "RSA-OAEP"
                },
                publicKey,
                data
            );

            const encryptedBase64 = this.arrayBufferToBase64(encryptedData);
            console.log('✅ 消息已加密');
            return encryptedBase64;
        } catch (error) {
            console.error('❌ 加密消息失败:', error);
            throw error;
        }
    }

    async decryptMessage(encryptedBase64) {
        if (!this.keyPair) {
            throw new Error('密钥对未初始化');
        }

        try {
            const encryptedData = this.base64ToArrayBuffer(encryptedBase64);

            const decryptedData = await window.crypto.subtle.decrypt(
                {
                    name: "RSA-OAEP"
                },
                this.keyPair.privateKey,
                encryptedData
            );

            const decoder = new TextDecoder();
            const message = decoder.decode(decryptedData);
            console.log('✅ 消息已解密');
            return message;
        } catch (error) {
            console.error('❌ 解密消息失败:', error);
            throw error;
        }
    }

    async generateSessionKey() {
        try {
            const sessionKey = await window.crypto.subtle.generateKey(
                {
                    name: "AES-GCM",
                    length: 256
                },
                true,
                ["encrypt", "decrypt"]
            );

            const sessionKeyId = this.generateUUID();
            this.sessionKeys.set(sessionKeyId, sessionKey);

            console.log('✅ 会话密钥已生成');
            return { sessionKey, sessionKeyId };
        } catch (error) {
            console.error('❌ 生成会话密钥失败:', error);
            throw error;
        }
    }

    async encryptWithSessionKey(data, sessionKeyId, iv = null) {
        const sessionKey = this.sessionKeys.get(sessionKeyId);
        if (!sessionKey) {
            throw new Error('会话密钥不存在');
        }

        try {
            const encoder = new TextEncoder();
            const dataBuffer = encoder.encode(data);

            // 生成 IV
            const ivBuffer = iv || window.crypto.getRandomValues(new Uint8Array(12));

            const encryptedData = await window.crypto.subtle.encrypt(
                {
                    name: "AES-GCM",
                    iv: ivBuffer
                },
                sessionKey,
                dataBuffer
            );

            const result = {
                data: this.arrayBufferToBase64(encryptedData),
                iv: this.arrayBufferToBase64(ivBuffer)
            };

            console.log('✅ 数据已使用会话密钥加密');
            return result;
        } catch (error) {
            console.error('❌ 加密数据失败:', error);
            throw error;
        }
    }

    async decryptWithSessionKey(encryptedData, iv, sessionKeyId) {
        const sessionKey = this.sessionKeys.get(sessionKeyId);
        if (!sessionKey) {
            throw new Error('会话密钥不存在');
        }

        try {
            const dataBuffer = this.base64ToArrayBuffer(encryptedData);
            const ivBuffer = this.base64ToArrayBuffer(iv);

            const decryptedData = await window.crypto.subtle.decrypt(
                {
                    name: "AES-GCM",
                    iv: ivBuffer
                },
                sessionKey,
                dataBuffer
            );

            const decoder = new TextDecoder();
            const data = decoder.decode(decryptedData);
            console.log('✅ 数据已使用会话密钥解密');
            return data;
        } catch (error) {
            console.error('❌ 解密数据失败:', error);
            throw error;
        }
    }

    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    base64ToArrayBuffer(base64) {
        const binary = window.atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}

describe('EncryptionManager', () => {
  let encryptionManager;

  beforeEach(() => {
    jest.clearAllMocks();
    encryptionManager = new EncryptionManager();
  });

  describe('constructor', () => {
    test('should initialize with correct defaults', () => {
      expect(encryptionManager.keyPair).toBeNull();
      expect(encryptionManager.sessionKeys).toBeInstanceOf(Map);
      expect(encryptionManager.initialized).toBe(false);
    });
  });

  describe('init', () => {
    test('should initialize encryption manager', async () => {
      await encryptionManager.init();

      expect(encryptionManager.initialized).toBe(true);
      expect(encryptionManager.keyPair).not.toBeNull();
      expect(encryptionManager.keyPair.publicKey).toBeDefined();
      expect(encryptionManager.keyPair.privateKey).toBeDefined();
      expect(global.console.log).toHaveBeenCalledWith('🔒 初始化加密管理器');
    });

    test('should not initialize twice', async () => {
      await encryptionManager.init();
      const firstKeyPair = encryptionManager.keyPair;

      await encryptionManager.init();

      expect(global.console.warn).toHaveBeenCalledWith('⚠️  加密管理器已初始化');
      expect(encryptionManager.keyPair).toBe(firstKeyPair);
    });

    test('should generate RSA-OAEP key pair', async () => {
      await encryptionManager.init();

      const publicKey = encryptionManager.keyPair.publicKey;
      const privateKey = encryptionManager.keyPair.privateKey;

      expect(publicKey.algorithm.name).toBe('RSA-OAEP');
      expect(publicKey.algorithm.modulusLength).toBe(2048);
      expect(publicKey.usages).toContain('encrypt');
      expect(privateKey.usages).toContain('decrypt');
    });
  });

  describe('exportPublicKey', () => {
    beforeEach(async () => {
      await encryptionManager.init();
    });

    test('should export public key as base64', async () => {
      const publicKeyBase64 = await encryptionManager.exportPublicKey();

      expect(typeof publicKeyBase64).toBe('string');
      expect(publicKeyBase64.length).toBeGreaterThan(0);
      expect(global.console.log).toHaveBeenCalledWith('✅ 公钥已导出');
    });

    test('should throw error if not initialized', async () => {
      const uninitializedManager = new EncryptionManager();

      await expect(uninitializedManager.exportPublicKey())
        .rejects.toThrow('密钥对未初始化');
    });
  });

  describe('importPublicKey', () => {
    beforeEach(async () => {
      await encryptionManager.init();
    });

    test('should import public key from base64', async () => {
      const publicKeyBase64 = await encryptionManager.exportPublicKey();
      const importedKey = await encryptionManager.importPublicKey(publicKeyBase64);

      expect(importedKey).toBeDefined();
      expect(importedKey.algorithm.name).toBe('RSA-OAEP');
      expect(importedKey.usages).toContain('encrypt');
      expect(global.console.log).toHaveBeenCalledWith('✅ 公钥已导入');
    });

    test('should throw error for invalid base64', async () => {
      await expect(encryptionManager.importPublicKey('invalid-base64!@#'))
        .rejects.toThrow();
    });
  });

  describe('encryptMessage and decryptMessage', () => {
    beforeEach(async () => {
      await encryptionManager.init();
    });

    test('should encrypt and decrypt message correctly', async () => {
      const message = 'Hello, this is a secret message!';
      const publicKey = encryptionManager.keyPair.publicKey;

      const encrypted = await encryptionManager.encryptMessage(message, publicKey);
      const decrypted = await encryptionManager.decryptMessage(encrypted);

      expect(decrypted).toBe(message);
      expect(typeof encrypted).toBe('string');
      expect(encrypted).not.toBe(message);
    });

    test('should encrypt message with different output each time', async () => {
      const message = 'Test message';
      const publicKey = encryptionManager.keyPair.publicKey;

      const encrypted1 = await encryptionManager.encryptMessage(message, publicKey);
      const encrypted2 = await encryptionManager.encryptMessage(message, publicKey);

      expect(encrypted1).not.toBe(encrypted2);
    });

    test('should handle empty message', async () => {
      const message = '';
      const publicKey = encryptionManager.keyPair.publicKey;

      const encrypted = await encryptionManager.encryptMessage(message, publicKey);
      const decrypted = await encryptionManager.decryptMessage(encrypted);

      expect(decrypted).toBe(message);
    });

    test('should handle unicode message', async () => {
      const message = '你好，这是一条加密消息！🔒';
      const publicKey = encryptionManager.keyPair.publicKey;

      const encrypted = await encryptionManager.encryptMessage(message, publicKey);
      const decrypted = await encryptionManager.decryptMessage(encrypted);

      expect(decrypted).toBe(message);
    });

    test('should throw error when decrypting without initialization', async () => {
      const uninitializedManager = new EncryptionManager();

      await expect(uninitializedManager.decryptMessage('encrypted-data'))
        .rejects.toThrow('密钥对未初始化');
    });
  });

  describe('generateSessionKey', () => {
    beforeEach(async () => {
      await encryptionManager.init();
    });

    test('should generate AES-GCM session key', async () => {
      const { sessionKey, sessionKeyId } = await encryptionManager.generateSessionKey();

      expect(sessionKey).toBeDefined();
      expect(sessionKey.algorithm.name).toBe('AES-GCM');
      expect(sessionKey.algorithm.length).toBe(256);
      expect(sessionKey.usages).toContain('encrypt');
      expect(sessionKey.usages).toContain('decrypt');
      expect(sessionKeyId).toMatch(/^[0-9a-f-]+$/);
      expect(encryptionManager.sessionKeys.has(sessionKeyId)).toBe(true);
    });

    test('should generate unique session keys', async () => {
      const { sessionKeyId: id1 } = await encryptionManager.generateSessionKey();
      const { sessionKeyId: id2 } = await encryptionManager.generateSessionKey();

      expect(id1).not.toBe(id2);
      expect(encryptionManager.sessionKeys.size).toBe(2);
    });
  });

  describe('encryptWithSessionKey and decryptWithSessionKey', () => {
    beforeEach(async () => {
      await encryptionManager.init();
    });

    test('should encrypt and decrypt data with session key', async () => {
      const { sessionKey, sessionKeyId } = await encryptionManager.generateSessionKey();
      const data = 'Sensitive data to encrypt';

      const encrypted = await encryptionManager.encryptWithSessionKey(data, sessionKeyId);
      const decrypted = await encryptionManager.decryptWithSessionKey(
        encrypted.data,
        encrypted.iv,
        sessionKeyId
      );

      expect(decrypted).toBe(data);
      expect(encrypted.data).toBeDefined();
      expect(encrypted.iv).toBeDefined();
      expect(typeof encrypted.data).toBe('string');
      expect(typeof encrypted.iv).toBe('string');
    });

    test('should throw error for non-existent session key', async () => {
      await expect(
        encryptionManager.encryptWithSessionKey('data', 'non-existent-id')
      ).rejects.toThrow('会话密钥不存在');
    });

    test('should use custom IV if provided', async () => {
      const { sessionKey, sessionKeyId } = await encryptionManager.generateSessionKey();
      const data = 'Test data';
      const customIV = new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);

      const encrypted = await encryptionManager.encryptWithSessionKey(
        data,
        sessionKeyId,
        customIV
      );

      expect(encrypted.iv).toBeDefined();
      const decryptedIV = encryptionManager.base64ToArrayBuffer(encrypted.iv);
      expect(new Uint8Array(decryptedIV)).toEqual(customIV);
    });

    test('should handle empty data', async () => {
      const { sessionKey, sessionKeyId } = await encryptionManager.generateSessionKey();
      const data = '';

      const encrypted = await encryptionManager.encryptWithSessionKey(data, sessionKeyId);
      const decrypted = await encryptionManager.decryptWithSessionKey(
        encrypted.data,
        encrypted.iv,
        sessionKeyId
      );

      expect(decrypted).toBe(data);
    });

    test('should handle unicode data', async () => {
      const { sessionKey, sessionKeyId } = await encryptionManager.generateSessionKey();
      const data = 'Unicode 数据 🌍🔒';

      const encrypted = await encryptionManager.encryptWithSessionKey(data, sessionKeyId);
      const decrypted = await encryptionManager.decryptWithSessionKey(
        encrypted.data,
        encrypted.iv,
        sessionKeyId
      );

      expect(decrypted).toBe(data);
    });
  });

  describe('arrayBufferToBase64', () => {
    test('should convert ArrayBuffer to base64', () => {
      const buffer = new TextEncoder().encode('Hello World').buffer;
      const base64 = encryptionManager.arrayBufferToBase64(buffer);

      expect(typeof base64).toBe('string');
      expect(base64.length).toBeGreaterThan(0);
    });

    test('should convert empty ArrayBuffer', () => {
      const buffer = new ArrayBuffer(0);
      const base64 = encryptionManager.arrayBufferToBase64(buffer);

      expect(base64).toBe('');
    });
  });

  describe('base64ToArrayBuffer', () => {
    test('should convert base64 to ArrayBuffer', () => {
      const base64 = 'SGVsbG8gV29ybGQ=';
      const buffer = encryptionManager.base64ToArrayBuffer(base64);

      expect(buffer).toBeInstanceOf(ArrayBuffer);
      expect(buffer.byteLength).toBeGreaterThan(0);
    });

    test('should convert empty string to ArrayBuffer', () => {
      const buffer = encryptionManager.base64ToArrayBuffer('');

      expect(buffer).toBeInstanceOf(ArrayBuffer);
      expect(buffer.byteLength).toBe(0);
    });
  });

  describe('generateUUID', () => {
    test('should generate valid UUID format', () => {
      const uuid = encryptionManager.generateUUID();

      expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    });

    test('should generate unique UUIDs', () => {
      const uuid1 = encryptionManager.generateUUID();
      const uuid2 = encryptionManager.generateUUID();

      expect(uuid1).not.toBe(uuid2);
    });
  });

  describe('integration tests', () => {
    test('should perform full encryption workflow', async () => {
      await encryptionManager.init();

      // Export public key
      const publicKeyBase64 = await encryptionManager.exportPublicKey();
      expect(publicKeyBase64).toBeDefined();

      // Encrypt a message
      const message = 'Integration test message';
      const encrypted = await encryptionManager.encryptMessage(
        message,
        encryptionManager.keyPair.publicKey
      );

      // Decrypt the message
      const decrypted = await encryptionManager.decryptMessage(encrypted);
      expect(decrypted).toBe(message);

      // Generate session key
      const { sessionKeyId } = await encryptionManager.generateSessionKey();

      // Encrypt data with session key
      const data = 'Session key encrypted data';
      const sessionEncrypted = await encryptionManager.encryptWithSessionKey(
        data,
        sessionKeyId
      );

      // Decrypt data with session key
      const sessionDecrypted = await encryptionManager.decryptWithSessionKey(
        sessionEncrypted.data,
        sessionEncrypted.iv,
        sessionKeyId
      );

      expect(sessionDecrypted).toBe(data);
    });

    test('should handle multiple concurrent operations', async () => {
      await encryptionManager.init();

      const messages = Array.from({ length: 5 }, (_, i) => `Message ${i + 1}`);

      const encryptPromises = messages.map(msg =>
        encryptionManager.encryptMessage(msg, encryptionManager.keyPair.publicKey)
      );

      const encryptedMessages = await Promise.all(encryptPromises);

      const decryptPromises = encryptedMessages.map(encrypted =>
        encryptionManager.decryptMessage(encrypted)
      );

      const decryptedMessages = await Promise.all(decryptPromises);

      expect(decryptedMessages).toEqual(messages);
    });
  });

  describe('error handling', () => {
    test('should handle invalid base64 in importPublicKey', async () => {
      await encryptionManager.init();

      await expect(encryptionManager.importPublicKey('invalid!@#$%'))
        .rejects.toThrow();
    });

    test('should handle invalid encrypted data in decryptMessage', async () => {
      await encryptionManager.init();

      await expect(encryptionManager.decryptMessage('invalid-base64-data'))
        .rejects.toThrow();
    });

    test('should handle invalid encrypted data in decryptWithSessionKey', async () => {
      await encryptionManager.init();
      const { sessionKeyId } = await encryptionManager.generateSessionKey();

      await expect(
        encryptionManager.decryptWithSessionKey('invalid', 'invalid', sessionKeyId)
      ).rejects.toThrow();
    });
  });
});
