/**
 * Jest Setup File for Frontend Tests
 * Mocks browser APIs for testing in Node.js environment
 */

// Mock console methods to reduce noise
global.console.log = jest.fn();
global.console.warn = jest.fn();
global.console.error = jest.fn();

// Global database storage for sharing state across test instances
const globalDatabases = new Map();

class MockIndexedDB {
  constructor() {
    this.databases = globalDatabases;
  }

  open(name, version) {
    const request = {
      onsuccess: null,
      onerror: null,
      onupgradeneeded: null,
      result: null
    };

    // Get existing database or create new one
    let db = this.databases.get(name);
    const isNew = !db;

    if (isNew) {
      db = new MockDatabase(name, version);
      this.databases.set(name, db);
    }

    // Simulate async behavior
    setTimeout(() => {
      // Trigger onupgradeneeded for new databases
      if (isNew && request.onupgradeneeded) {
        request.onupgradeneeded({
          target: { result: db },
          oldVersion: 0,
          newVersion: version
        });
      }

      if (request.onsuccess) {
        request.result = db;
        request.onsuccess({ target: request });
      }
    }, 0);

    return request;
  }
}

class MockDatabase {
  constructor(name, version) {
    this.name = name;
    this.version = version;
    this.stores = {};
    this.objectStoreNames = {
      contains: (name) => name in this.stores
    };
  }

  transaction(storeNames, mode = 'readonly') {
    const storeArray = Array.isArray(storeNames) ? storeNames : [storeNames];
    return new MockTransaction(storeArray.map(name => this.stores[name]), mode);
  }

  createObjectStore(name, options = {}) {
    const store = new MockObjectStore(name, options);
    this.stores[name] = store;
    return store;
  }
}

class MockTransaction {
  constructor(stores, mode) {
    this.stores = stores;
    this.mode = mode;
  }

  objectStore(name) {
    const store = this.stores.find(s => s.name === name);
    return store || new MockObjectStore(name);
  }
}

class MockObjectStore {
  constructor(name, options = {}) {
    this.name = name;
    this.keyPath = options.keyPath;
    this.autoIncrement = options.autoIncrement;
    this.data = new Map();
    this.indexes = new Map();
  }

  get(key) {
    const request = {
      onsuccess: null,
      onerror: null,
      result: null
    };

    setTimeout(() => {
      request.result = this.data.get(key);
      if (request.onsuccess) {
        request.onsuccess({ target: request });
      }
    }, 0);

    return request;
  }

  getAll(key) {
    const request = {
      onsuccess: null,
      onerror: null,
      result: []
    };

    setTimeout(() => {
      request.result = Array.from(this.data.values());
      if (request.onsuccess) {
        request.onsuccess({ target: request });
      }
    }, 0);

    return request;
  }

  put(value) {
    const request = {
      onsuccess: null,
      onerror: null
    };

    setTimeout(() => {
      const key = this.keyPath ? value[this.keyPath] : Math.random().toString(36).substr(2, 9);
      this.data.set(key, value);

      if (request.onsuccess) {
        request.onsuccess({ target: request });
      }
    }, 0);

    return request;
  }

  add(value) {
    const request = {
      onsuccess: null,
      onerror: null
    };

    setTimeout(() => {
      const key = this.autoIncrement
        ? Math.floor(Math.random() * 1000000)
        : Math.random().toString(36).substr(2, 9);

      value.output_id = value.output_id || key;
      value.command_id = value.command_id || key;
      this.data.set(key, value);

      if (request.onsuccess) {
        request.onsuccess({ target: request });
      }
    }, 0);

    return request;
  }

  delete(key) {
    const request = {
      onsuccess: null,
      onerror: null
    };

    setTimeout(() => {
      this.data.delete(key);
      if (request.onsuccess) {
        request.onsuccess({ target: request });
      }
    }, 0);

    return request;
  }

  clear() {
    const request = {
      onsuccess: null,
      onerror: null
    };

    setTimeout(() => {
      this.data.clear();
      if (request.onsuccess) {
        request.onsuccess({ target: request });
      }
    }, 0);

    return request;
  }

  createIndex(name, keyPath, options = {}) {
    this.indexes.set(name, { name, keyPath, options });
    return this;
  }

  index(name) {
    // Return a mock index that filters data
    return {
      getAll: (value) => {
        const request = {
          onsuccess: null,
          onerror: null,
          result: []
        };

        setTimeout(() => {
          const index = this.indexes.get(name);
          if (index) {
            request.result = Array.from(this.data.values()).filter(item =>
              item[index.keyPath] === value
            );
          }
          if (request.onsuccess) {
            request.onsuccess({ target: request });
          }
        }, 0);

        return request;
      }
    };
  }
}

// Mock Web Crypto API
class MockCryptoSubtle {
  constructor() {
    this.keyPairs = new Map();
    this.sessionKeys = new Map();
  }

  async generateKey(algorithm, extractable, keyUsages) {
    const keyId = Math.random().toString(36).substr(2, 9);

    const keyPair = {
      algorithm,
      extractable,
      type: 'public',
      usages: keyUsages,
      id: keyId
    };

    this.keyPairs.set(keyId, keyPair);

    return {
      publicKey: { ...keyPair, type: 'public' },
      privateKey: { ...keyPair, type: 'private' }
    };
  }

  async exportKey(format, key) {
    // Return a mock buffer
    const buffer = new ArrayBuffer(256);
    const view = new Uint8Array(buffer);
    for (let i = 0; i < view.length; i++) {
      view[i] = Math.floor(Math.random() * 256);
    }
    return buffer;
  }

  async importKey(format, keyData, algorithm, extractable, keyUsages) {
    return {
      algorithm,
      extractable,
      type: 'public',
      usages: keyUsages,
      id: Math.random().toString(36).substr(2, 9)
    };
  }

  async encrypt(algorithm, key, data) {
    // Simple mock: return modified data as "encrypted"
    const encoder = new TextEncoder();
    const encoderResult = encoder.encode('encrypted-');
    const result = new Uint8Array(encoderResult.byteLength + data.byteLength);
    result.set(encoderResult, 0);
    result.set(new Uint8Array(data), encoderResult.byteLength);
    return result.buffer;
  }

  async decrypt(algorithm, key, data) {
    // Simple mock: remove 'encrypted-' prefix
    const uint8Array = new Uint8Array(data);
    const prefix = new TextEncoder().encode('encrypted-');
    if (uint8Array.length > prefix.byteLength) {
      const result = uint8Array.slice(prefix.byteLength);
      return result.buffer;
    }
    return data;
  }
}

class MockCrypto {
  constructor() {
    this.subtle = new MockCryptoSubtle();
  }

  getRandomValues(array) {
    for (let i = 0; i < array.length; i++) {
      array[i] = Math.floor(Math.random() * 256);
    }
    return array;
  }
}

// Reset global state before each test
beforeEach(() => {
  jest.clearAllMocks();
  globalDatabases.clear();
});

// Install mocks in global scope
global.indexedDB = new MockIndexedDB();
global.crypto = new MockCrypto();
global.window = {
  crypto: global.crypto,
  btoa: (str) => Buffer.from(str).toString('base64'),
  atob: (str) => Buffer.from(str, 'base64').toString('binary')
};

// Add TextEncoder and TextDecoder for Node.js compatibility
if (typeof TextEncoder === 'undefined') {
  global.TextEncoder = require('util').TextEncoder;
}
if (typeof TextDecoder === 'undefined') {
  global.TextDecoder = require('util').TextDecoder;
}
