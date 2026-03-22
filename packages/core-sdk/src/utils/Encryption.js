/**
 * @fileoverview Zhineng Bridge Encryption Module
 * 提供AES-256-GCM加密、解密和消息队列功能
 * @module core-sdk/src/utils/Encryption
 */

const crypto = require('crypto');

const ALGORITHM = 'aes-256-gcm';
const KEY_LENGTH = 32;
const IV_LENGTH = 16;
const AUTH_TAG_LENGTH = 16;
const SALT_LENGTH = 32;
const RSA_MODULUS_LENGTH = 2048;
const MAX_QUEUE_SIZE = 1000;
const CHALLENGE_LENGTH = 16;
const HASH_TRUNCATE_LENGTH = 16;

class Encryption {
  constructor() {
    this.algorithm = ALGORITHM;
    this.keyLength = KEY_LENGTH;
    this.ivLength = IV_LENGTH;
    this.authTagLength = AUTH_TAG_LENGTH;
    this.saltLength = SALT_LENGTH;
  }

  /**
   * 使用PBKDF2从密码生成密钥
   * @param {string} password - 密码
   * @param {Buffer|null} salt - 盐值
   * @returns {{key: Buffer, salt: Buffer}} 密钥和盐值
   */
  generateKey(password, salt = null) {
    salt = salt || crypto.randomBytes(this.saltLength);
    const key = crypto.pbkdf2Sync(password, salt, 100000, this.keyLength, 'sha256');
    return { key, salt };
  }

  /**
   * 生成共享密钥
   * @returns {string} 32字节随机十六进制字符串
   */
  generateSharedSecret() {
    return crypto.randomBytes(KEY_LENGTH).toString('hex');
  }

  /**
   * 加密明文
   * @param {string} plaintext - 待加密文本
   * @param {string} key - 十六进制密钥
   * @returns {{iv: string, encrypted: string, authTag: string}} 加密结果
   */
  encrypt(plaintext, key) {
    const iv = crypto.randomBytes(this.ivLength);
    const cipher = crypto.createCipheriv(this.algorithm, Buffer.from(key, 'hex'), iv);

    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    return {
      iv: iv.toString('hex'),
      encrypted: encrypted,
      authTag: authTag.toString('hex')
    };
  }

  /**
   * 解密密文
   * @param {Object} encryptedData - 加密数据对象
   * @param {string} key - 十六进制密钥
   * @returns {string} 解密后的文本
   */
  decrypt(encryptedData, key) {
    const iv = Buffer.from(encryptedData.iv, 'hex');
    const authTag = Buffer.from(encryptedData.authTag, 'hex');
    const decipher = crypto.createDecipheriv(this.algorithm, Buffer.from(key, 'hex'), iv);

    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }

  /**
   * 加密对象
   * @param {Object} obj - 待加密对象
   * @param {string} key - 十六进制密钥
   * @returns {Object} 加密结果
   */
  encryptObject(obj, key) {
    const plaintext = JSON.stringify(obj);
    return this.encrypt(plaintext, key);
  }

  /**
   * 解密对象
   * @param {Object} encryptedObj - 加密对象
   * @param {string} key - 十六进制密钥
   * @returns {Object} 解密后的对象
   */
  decryptObject(encryptedObj, key) {
    const decrypted = this.decrypt(encryptedObj, key);
    return JSON.parse(decrypted);
  }

  /**
   * 生成RSA密钥对
   * @returns {{publicKey: string, privateKey: string}} 密钥对
   */
  generateKeyPair() {
    const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
      modulusLength: RSA_MODULUS_LENGTH,
      publicKeyEncoding: { type: 'spki', format: 'pem' },
      privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
    });
    return { publicKey, privateKey };
  }

  /**
   * 使用公钥加密
   * @param {string} plaintext - 待加密文本
   * @param {string} publicKey - PEM格式公钥
   * @returns {string} Base64编码的加密结果
   */
  encryptWithPublicKey(plaintext, publicKey) {
    const encrypted = crypto.publicEncrypt(
      {
        key: publicKey,
        padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
        oaepHash: 'sha256'
      },
      Buffer.from(plaintext)
    );
    return encrypted.toString('base64');
  }

  /**
   * 使用私钥解密
   * @param {string} encrypted - Base64编码的加密数据
   * @param {string} privateKey - PEM格式私钥
   * @returns {string} 解密后的文本
   */
  decryptWithPrivateKey(encrypted, privateKey) {
    const decrypted = crypto.privateDecrypt(
      {
        key: privateKey,
        padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
        oaepHash: 'sha256'
      },
      Buffer.from(encrypted, 'base64')
    );
    return decrypted.toString('utf8');
  }

  /**
   * 生成二维码数据
   * @returns {Object} 包含密钥和元数据
   */
  generateQRCodeData() {
    const secret = this.generateSharedSecret();
    return {
      secret: secret,
      createdAt: Date.now(),
      version: '1.0'
    };
  }

  /**
   * 哈希公钥
   * @param {string} publicKey - PEM格式公钥
   * @returns {string} 哈希值前16位
   */
  hashPublicKey(publicKey) {
    return crypto.createHash('sha256').update(publicKey).digest('hex').slice(0, HASH_TRUNCATE_LENGTH);
  }

  /**
   * 创建挑战
   * @returns {string} 随机挑战字符串
   */
  createChallenge() {
    return crypto.randomBytes(CHALLENGE_LENGTH).toString('hex');
  }

  /**
   * 验证挑战响应
   * @param {string} challenge - 挑战字符串
   * @param {Object} response - 加密响应
   * @param {string} key - 密钥
   * @returns {boolean} 验证结果
   */
  verifyChallenge(challenge, response, key) {
    const expected = this.encrypt(challenge, key);
    return response.encrypted === expected.encrypted;
  }
}

class MessageQueue {
  constructor(encryption) {
    this.encryption = encryption;
    this.queue = [];
    this.maxQueueSize = MAX_QUEUE_SIZE;
  }

  /**
   * 入队消息
   * @param {Object} message - 消息对象
   * @param {string|null} key - 加密密钥
   * @returns {string} 消息ID
   */
  enqueue(message, key = null) {
    const entry = {
      id: crypto.randomBytes(8).toString('hex'),
      timestamp: Date.now(),
      data: key ? this.encryption.encryptObject(message, key) : message,
      encrypted: !!key
    };

    this.queue.push(entry);

    if (this.queue.length > this.maxQueueSize) {
      this.queue.shift();
    }

    return entry.id;
  }

  /**
   * 出队消息
   * @param {string|null} id - 消息ID，为空则取队首
   * @returns {Object|null} 消息条目
   */
  dequeue(id = null) {
    if (id) {
      const index = this.queue.findIndex(e => e.id === id);
      if (index !== -1) {
        return this.queue.splice(index, 1)[0];
      }
      return null;
    }
    return this.queue.shift();
  }

  /**
   * 获取所有消息
   * @param {string|null} key - 解密密钥
   * @returns {Array} 消息列表
   */
  getAll(key = null) {
    return this.queue.map(entry => {
      if (entry.encrypted && key) {
        return this.encryption.decryptObject(entry.data, key);
      }
      return entry.data;
    });
  }

  /**
   * 清空队列
   */
  clear() {
    this.queue = [];
  }

  /**
   * 获取队列大小
   * @returns {number} 队列长度
   */
  getSize() {
    return this.queue.length;
  }
}

module.exports = { Encryption, MessageQueue };
