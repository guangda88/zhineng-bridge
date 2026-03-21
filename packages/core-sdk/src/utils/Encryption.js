const crypto = require('crypto');

class Encryption {
  constructor() {
    this.algorithm = 'aes-256-gcm';
    this.keyLength = 32;
    this.ivLength = 16;
    this.authTagLength = 16;
    this.saltLength = 32;
  }

  generateKey(password, salt = null) {
    salt = salt || crypto.randomBytes(this.saltLength);
    const key = crypto.pbkdf2Sync(password, salt, 100000, this.keyLength, 'sha256');
    return { key, salt };
  }

  generateSharedSecret() {
    return crypto.randomBytes(32).toString('hex');
  }

  encrypt(plaintext, key) {
    const iv = crypto.randomBytes(this.ivLength);
    const cipher = crypto.createCipheriv(this.algorithm, Buffer.from(key, 'hex'), iv);
    
    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    return {
      iv: iv.toString('hex'),
      encrypted,
      authTag: authTag.toString('hex')
    };
  }

  decrypt(encryptedData, key) {
    const iv = Buffer.from(encryptedData.iv, 'hex');
    const authTag = Buffer.from(encryptedData.authTag, 'hex');
    const decipher = crypto.createDecipheriv(this.algorithm, Buffer.from(key, 'hex'), iv);
    
    decipher.setAuthTag(authTag);
    
    let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return decrypted;
  }

  encryptObject(obj, key) {
    const plaintext = JSON.stringify(obj);
    return this.encrypt(plaintext, key);
  }

  decryptObject(encryptedObj, key) {
    const decrypted = this.decrypt(encryptedObj, key);
    return JSON.parse(decrypted);
  }

  generateKeyPair() {
    const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
      modulusLength: 2048,
      publicKeyEncoding: { type: 'spki', format: 'pem' },
      privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
    });
    return { publicKey, privateKey };
  }

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

  generateQRCodeData() {
    const secret = this.generateSharedSecret();
    return {
      secret,
      createdAt: Date.now(),
      version: '1.0'
    };
  }

  hashPublicKey(publicKey) {
    return crypto.createHash('sha256').update(publicKey).digest('hex').slice(0, 16);
  }

  createChallenge() {
    return crypto.randomBytes(16).toString('hex');
  }

  verifyChallenge(challenge, response, key) {
    const expected = this.encrypt(challenge, key);
    return response.encrypted === expected.encrypted;
  }
}

class MessageQueue {
  constructor(encryption) {
    this.encryption = encryption;
    this.queue = [];
    this.maxQueueSize = 1000;
  }

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

  getAll(key = null) {
    return this.queue.map(entry => {
      if (entry.encrypted && key) {
        return this.encryption.decryptObject(entry.data, key);
      }
      return entry.data;
    });
  }

  clear() {
    this.queue = [];
  }

  getSize() {
    return this.queue.length;
  }
}

module.exports = { Encryption, MessageQueue };
