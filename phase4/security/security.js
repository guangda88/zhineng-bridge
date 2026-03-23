/**
 * 智桥 - 安全加固模块
 */

class SecurityManager {
    constructor() {
        this.initialized = false;
        this.securityHeaders = {
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
        };
        this.encryptionManager = null;
    }

    /**
     * 初始化安全管理器
     */
    async init() {
        if (this.initialized) {
            console.warn('⚠️  安全管理器已初始化');
            return;
        }

        console.log('🔒 初始化安全管理器');

        // 设置安全头
        this.setSecurityHeaders();

        // 初始化加密
        await this.initEncryption();

        // 设置 CSRF 保护
        this.setupCSRFProtection();

        // 设置 XSS 保护
        this.setupXSSProtection();

        // 设置输入验证
        this.setupInputValidation();

        // 设置速率限制
        this.setupRateLimiting();

        // 设置日志记录
        this.setupLogging();

        this.initialized = true;
        console.log('✅ 安全管理器已初始化');
    }

    /**
     * 设置安全头
     */
    setSecurityHeaders() {
        console.log('📝 设置安全头');

        // Content-Security-Policy
        const csp = this.securityHeaders['Content-Security-Policy'];
        const metaCSP = document.createElement('meta');
        metaCSP.httpEquiv = 'Content-Security-Policy';
        metaCSP.content = csp;
        document.head.appendChild(metaCSP);

        // X-Content-Type-Options
        const metaXCTO = document.createElement('meta');
        metaXCTO.httpEquiv = 'X-Content-Type-Options';
        metaXCTO.content = this.securityHeaders['X-Content-Type-Options'];
        document.head.appendChild(metaXCTO);

        // X-Frame-Options
        const metaXFO = document.createElement('meta');
        metaXFO.httpEquiv = 'X-Frame-Options';
        metaXFO.content = this.securityHeaders['X-Frame-Options'];
        document.head.appendChild(metaXFO);

        // X-XSS-Protection
        const metaXXSSP = document.createElement('meta');
        metaXXSSP.httpEquiv = 'X-XSS-Protection';
        metaXXSSP.content = this.securityHeaders['X-XSS-Protection'];
        document.head.appendChild(metaXXSSP);

        console.log('✅ 安全头已设置');
    }

    /**
     * 初始化加密
     */
    async initEncryption() {
        console.log('🔐 初始化加密');

        if (window.EncryptionManager) {
            this.encryptionManager = new EncryptionManager();
            await this.encryptionManager.init();
            console.log('✅ 加密管理器已初始化');
        }
    }

    /**
     * 设置 CSRF 保护
     */
    setupCSRFProtection() {
        console.log('🛡️  设置 CSRF 保护');

        // 生成 CSRF Token
        const csrfToken = this.generateCSRFToken();

        // 保存到 localStorage
        localStorage.setItem('csrf-token', csrfToken);

        // 添加到所有请求头
        const originalFetch = window.fetch;
        window.fetch = async (url, options = {}) => {
            options.headers = options.headers || {};
            options.headers['X-CSRF-Token'] = csrfToken;

            return originalFetch(url, options);
        };

        console.log('✅ CSRF 保护已设置');
    }

    /**
     * 生成 CSRF Token
     */
    generateCSRFToken() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    /**
     * 设置 XSS 保护
     */
    setupXSSProtection() {
        console.log('🛡️  设置 XSS 保护');

        // 过滤 HTML
        this.filterHTML();

        // 过滤 URL
        this.filterURL();

        // 使用 DOMPurify（如果可用）
        if (typeof DOMPurify !== 'undefined') {
            window.sanitizeHTML = (html) => DOMPurify.sanitize(html);
        } else {
            window.sanitizeHTML = (html) => html;
        }

        console.log('✅ XSS 保护已设置');
    }

    /**
     * 过滤 HTML
     */
    filterHTML() {
        console.log('🔍 过滤 HTML');

        const dangerousTags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'textarea'];
        
        dangerousTags.forEach(tag => {
            const elements = document.getElementsByTagName(tag);
            for (let i = elements.length - 1; i >= 0; i--) {
                const element = elements[i];
                if (element.getAttribute('data-safe') !== 'true') {
                    element.parentNode.removeChild(element);
                }
            }
        });

        console.log('✅ HTML 已过滤');
    }

    /**
     * 过滤 URL
     */
    filterURL(url) {
        console.log('🔍 过滤 URL');

        // 检查 URL 协议
        const dangerousProtocols = ['javascript:', 'vbscript:', 'data:', 'file:'];
        
        for (const protocol of dangerousProtocols) {
            if (url.toLowerCase().startsWith(protocol)) {
                console.warn('⚠️  检测到危险 URL:', url);
                return '#';
            }
        }

        return url;
    }

    /**
     * 设置输入验证
     */
    setupInputValidation() {
        console.log('✅ 设置输入验证');

        // 验证所有输入
        const inputs = document.querySelectorAll('input[type="text"], input[type="email"], textarea');
        
        inputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const value = e.target.value;
                
                // 过滤危险字符
                const dangerousChars = ['<', '>', '"', "'", '&'];
                let filteredValue = value;
                
                dangerousChars.forEach(char => {
                    filteredValue = filteredValue.replace(char, '');
                });
                
                if (value !== filteredValue) {
                    e.target.value = filteredValue;
                    console.warn('⚠️  检测到危险输入:', value);
                }
            });
        });

        console.log('✅ 输入验证已设置');
    }

    /**
     * 设置速率限制
     */
    setupRateLimiting() {
        console.log('⏱️  设置速率限制');

        // 记录请求次数
        this.requestCount = {};
        this.requestLimit = 10;
        this.requestWindow = 60000; // 1 分钟

        // 拦截 fetch 请求
        const originalFetch = window.fetch;
        window.fetch = async (url, options = {}) => {
            const now = Date.now();
            const key = url;

            // 检查请求次数
            if (this.requestCount[key]) {
                const requests = this.requestCount[key].filter(timestamp => now - timestamp < this.requestWindow);
                
                if (requests.length >= this.requestLimit) {
                    console.warn('⚠️  速率限制触发:', key);
                    throw new Error('Too many requests');
                }
                
                this.requestCount[key] = [...requests, now];
            } else {
                this.requestCount[key] = [now];
            }

            return originalFetch(url, options);
        };

        console.log('✅ 速率限制已设置');
    }

    /**
     * 设置日志记录
     */
    setupLogging() {
        console.log('📝 设置日志记录');

        // 拦截 console.log
        const originalLog = console.log;
        console.log = (...args) => {
            // 记录日志到服务器
            this.logToServer('info', args);
            
            // 调用原始 log
            originalLog.apply(console, args);
        };

        // 拦截 console.error
        const originalError = console.error;
        console.error = (...args) => {
            // 记录错误到服务器
            this.logToServer('error', args);
            
            // 调用原始 error
            originalError.apply(console, args);
        };

        // 拦截 console.warn
        const originalWarn = console.warn;
        console.warn = (...args) => {
            // 记录警告到服务器
            this.logToServer('warning', args);
            
            // 调用原始 warn
            originalWarn.apply(console, args);
        };

        console.log('✅ 日志记录已设置');
    }

    /**
     * 记录日志到服务器
     */
    logToServer(level, args) {
        const logData = {
            level: level,
            message: args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(' '),
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        // 发送到服务器
        fetch('/api/logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(logData)
        }).catch(error => {
            // 静默失败
        });
    }

    /**
     * 安全检查
     */
    async performSecurityCheck() {
        console.log('🔍 执行安全检查');

        const results = {
            csp: false,
            xss: false,
            csrf: false,
            encryption: false
        };

        // 检查 CSP
        const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
        results.csp = cspMeta !== null;

        // 检查 XSS
        const scripts = document.querySelectorAll('script:not([data-safe])');
        results.xss = scripts.length === 0;

        // 检查 CSRF
        const csrfToken = localStorage.getItem('csrf-token');
        results.csrf = csrfToken !== null;

        // 检查加密
        results.encryption = this.encryptionManager !== null;

        console.log('✅ 安全检查完成:', results);

        return results;
    }
}

// 导出安全管理器
window.SecurityManager = SecurityManager;
