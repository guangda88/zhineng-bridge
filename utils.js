/**
 * @fileoverview 通用工具函数库
 * @module utils
 */

/**
 * 转义HTML特殊字符以防止XSS攻击
 * @param {string} text - 需要转义的文本
 * @returns {string} 转义后的HTML安全字符串
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 格式化时间戳为本地时间字符串
 * @param {number} timestamp - 时间戳（毫秒）
 * @returns {string} 格式化的时间字符串
 */
function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleTimeString();
}

/**
 * 生成随机ID
 * @param {number} [length=16] - ID长度
 * @returns {string} 随机ID字符串
 */
function generateRandomId(length = 16) {
    const chars = '0123456789abcdef';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 深度克隆对象
 * @param {Object} obj - 要克隆的对象
 * @returns {Object} 克隆后的对象
 */
function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}
