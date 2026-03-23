/**
 * Zhineng Bridge 常量配置
 * @module config/constants
 */

// 服务器配置
const SERVER_CONFIG = {
    DEFAULT_PORT: 8001,
    HTTP_STATUS_OK: 200,
    HTTP_STATUS_NOT_FOUND: 404,
    RECONNECT_DELAY_MS: 3000,
    MESSAGE_TIMEOUT: 5000
};

// WebSocket配置
const WS_CONFIG = {
    PING_INTERVAL: 30000,
    MAX_MESSAGE_SIZE: 1024 * 1024 // 1MB
};

// UI配置
const UI_CONFIG = {
    MAX_MESSAGE_LENGTH: 5000,
    AUTO_SCROLL_DELAY: 100,
    DEBOUNCE_DELAY: 300,
    CHAT_HISTORY_LIMIT: 100
};

// 加密配置
const ENCRYPTION_CONFIG = {
    ALGORITHM: 'aes-256-gcm',
    KEY_LENGTH: 32,
    IV_LENGTH: 16,
    SALT_LENGTH: 64
};

// 会话配置
const SESSION_CONFIG = {
    DEFAULT_TIMEOUT: 24 * 60 * 60 * 1000, // 24小时
    MAX_SESSIONS: 100
};

// 日志配置
const LOG_CONFIG = {
    MAX_LOG_SIZE: 10 * 1024 * 1024, // 10MB
    LOG_RETENTION_DAYS: 7
};

module.exports = {
    SERVER_CONFIG,
    WS_CONFIG,
    UI_CONFIG,
    ENCRYPTION_CONFIG,
    SESSION_CONFIG,
    LOG_CONFIG
};
