/**
 * 智桥 - 加密模块
 * 使用 Web Crypto API 实现端到端加密
 */

class EncryptionManager {
    constructor() {
        this.keyPair = null;
        this.sessionKeys = new Map();
        this.initialized = false;
    }

    /**
     * 初始化加密管理器
     */
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

    /**
     * 生成 RSA 密钥对
     */
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

    /**
     * 导出公钥
     */
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

    /**
     * 导入公钥
     */
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

    /**
     * 加密消息
     */
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

    /**
     * 解密消息
     */
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

    /**
     * 生成会话密钥
     */
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

    /**
     * 使用会话密钥加密数据
     */
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

    /**
     * 使用会话密钥解密数据
     */
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

    /**
     * ArrayBuffer 转 Base64
     */
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    /**
     * Base64 转 ArrayBuffer
     */
    base64ToArrayBuffer(base64) {
        const binary = window.atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    /**
     * 生成 UUID
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}

// 导出加密管理器
window.EncryptionManager = EncryptionManager;
