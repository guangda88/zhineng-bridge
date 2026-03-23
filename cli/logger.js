/**
 * 简单的日志工具
 * 用于替换console语句，提供更好的日志管理
 */

class Logger {
    constructor(name) {
        this.name = name;
    }

    /**
     * 信息级别日志
     * @param {string} message - 日志消息
     * @param {...any} args - 额外参数
     */
    info(message, ...args) {
        // console.log(`[INFO] ${this.name}:`, message, ...args);
    }

    /**
     * 警告级别日志
     * @param {string} message - 日志消息
     * @param {...any} args - 额外参数
     */
    warn(message, ...args) {
        // console.warn(`[WARN] ${this.name}:`, message, ...args);
    }

    /**
     * 错误级别日志
     * @param {string} message - 日志消息
     * @param {...any} args - 额外参数
     */
    error(message, ...args) {
        // console.error(`[ERROR] ${this.name}:`, message, ...args);
    }

    /**
     * 调试级别日志
     * @param {string} message - 日志消息
     * @param {...any} args - 额外参数
     */
    debug(message, ...args) {
        if (process.env.DEBUG === 'true') {
            // console.log(`[DEBUG] ${this.name}:`, message, ...args);
        }
    }
}

/**
 * 创建logger实例
 * @param {string} name - Logger名称
 * @returns {Logger} Logger实例
 */
function createLogger(name) {
    return new Logger(name);
}

module.exports = { Logger, createLogger };
