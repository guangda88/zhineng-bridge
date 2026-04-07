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
            // First generate with extractable=true so we can export the public key
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

            // Export public key immediately, then regenerate with extractable=false
            // so the private key can never be extracted from browser crypto storage
            const publicKeyData = await window.crypto.subtle.exportKey(
                "spki", keyPair.publicKey
            );

            const publicKey = await window.crypto.subtle.importKey(
                "spki", publicKeyData,
                { name: "RSA-OAEP", hash: "SHA-256" },
                true,
                ["encrypt"]
            );

            // Re-import private key as non-extractable
            const privateKeyData = await window.crypto.subtle.exportKey(
                "pkcs8", keyPair.privateKey
            );
            const privateKey = await window.crypto.subtle.importKey(
                "pkcs8", privateKeyData,
                { name: "RSA-OAEP", hash: "SHA-256" },
                false,
                ["decrypt"]
            );

            // Zero out raw key material from memory
            privateKeyData.fill(0);

            const safeKeyPair = { publicKey, privateKey };
            this._exportedPublicKey = this.arrayBufferToBase64(publicKeyData);

            console.log('✅ RSA 密钥对已生成（私钥不可导出）');
            return safeKeyPair;
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
        if (typeof crypto !== 'undefined' && crypto.randomUUID) {
            return crypto.randomUUID();
        }
        const bytes = new Uint8Array(16);
        crypto.getRandomValues(bytes);
        bytes[6] = (bytes[6] & 0x0f) | 0x40;
        bytes[8] = (bytes[8] & 0x3f) | 0x80;
        const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
        return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
    }
}

// 导出加密管理器
window.EncryptionManager = EncryptionManager;
