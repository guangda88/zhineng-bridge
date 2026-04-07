/**
 * 改进的 UI 功能
 */

// 显示加载状态
function showLoading(message = '加载中...') {
    const existingLoader = document.querySelector('.loading-overlay');
    if (existingLoader) {
        existingLoader.remove();
    }

    const loader = document.createElement('div');
    loader.className = 'loading-overlay';
    loader.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <span>${message}</span>
        </div>
    `;
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        backdrop-filter: blur(4px);
    `;
    document.body.appendChild(loader);
    return loader;
}

function hideLoading() {
    const loader = document.querySelector('.loading-overlay');
    if (loader) {
        loader.remove();
    }
}

// 改进的通知系统
function showNotification(message, type = 'info', duration = 5000) {
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
            <span style="font-size: 1.5rem;">${getNotificationIcon(type)}</span>
            <div style="flex: 1;">
                <div style="font-weight: 600; margin-bottom: 0.25rem;"></div>
            </div>
        </div>
        <button class="notification-close" onclick="this.parentElement.parentElement.remove()">✕</button>
    `;
    notification.querySelector('div[style*="font-weight"]')?.lastChild?.textContent || '';
    const msgDiv = notification.querySelector('div[style*="font-weight: 600"]');
    if (msgDiv) msgDiv.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }
    }, duration);

    return notification;
}

function getNotificationIcon(type) {
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        warning: '⚠️'
    };
    return icons[type] || 'ℹ️';
}

// 改进的错误处理 - Self-Healing Errors
function handleError(error, context = '') {
    console.error(`❌ 错误: ${context}`, error);

    let message = '操作失败';
    let details = '';
    let suggestion = '';

    if (typeof error === 'string') {
        message = error;
        suggestion = getSuggestion(message);
    } else if (error.message) {
        message = error.message;
        if (error.details) {
            details = error.details;
        }
        suggestion = getSuggestion(message);
    } else if (error.code) {
        message = `错误代码: ${error.code}`;
        details = error.message || '';
        suggestion = getSuggestion(message);
    }

    // 显示带建议的通知
    const fullMessage = suggestion ? `${message}\n\n💡 建议: ${suggestion}` : message;
    showNotification(fullMessage, 'error', 8000);

    if (details) {
        console.error('详细信息:', details);
    }

    // 记录错误上下文用于调试
    console.error('错误上下文:', {
        context,
        message,
        suggestion,
        timestamp: new Date().toISOString(),
        stack: error?.stack
    });

    return { message, details, suggestion, context };
}

// 错误建议映射 - Self-Healing Errors principle
function getSuggestion(errorMessage) {
    const suggestions = {
        'WebSocket 未连接': '请检查网络连接，或等待 WebSocket 自动重连',
        'WebSocket 未连接 - 请等待连接恢复': '请等待 WebSocket 自动重连（约 5 秒后），或刷新页面',
        '会话创建超时': '请检查网络连接，或稍后重试。如果问题持续，请检查服务器日志',
        '会话停止超时': '会话可能仍在运行，请尝试刷新会话列表',
        '会话删除超时': '会话可能已被删除，请刷新会话列表确认',
        '请先连接 WebSocket': '请等待 WebSocket 连接成功后再进行操作',
        '工具.* 当前不可用': '请选择其他可用工具，或稍后重试',
        '未找到工具': '请从工具列表中选择有效的工具',
        '请先选择一个工具': '请先在"工具"页面选择一个工具',
        'object of type \'coroutine\' has no len()': '服务器内部错误，请联系管理员检查日志'
    };

    for (const [pattern, suggestion] of Object.entries(suggestions)) {
        if (errorMessage.includes(pattern)) {
            return suggestion;
        }
    }

    return '';
}

// 改进的会话操作
async function createSessionWithFeedback(toolName, args = []) {
    showLoading('正在创建会话...');

    try {
        return await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('会话创建超时 - 请检查网络连接或重试'));
            }, 10000);

            // 临时消息处理器
            const originalHandleMessage = window.handleMessage;

            const customHandler = (data) => {
                if (data.type === 'session_started') {
                    clearTimeout(timeout);
                    hideLoading();
                    showNotification('会话创建成功', 'success');
                    resolve(data);
                } else if (data.type === 'error') {
                    clearTimeout(timeout);
                    hideLoading();
                    reject(new Error(`服务器错误: ${data.message}`));
                } else {
                    // 其他消息交给原始处理器
                    if (originalHandleMessage) {
                        originalHandleMessage(data);
                    }
                }
            };

            // 临时覆盖 handleMessage
            window.handleMessage = customHandler;

            // 设置待创建会话的标记
            window.APP_STATE.pendingSessionStart = {
                toolName: toolName,
                args: args
            };

            // 发送请求
            if (window.ws && window.ws.readyState === WebSocket.OPEN) {
                window.ws.send(JSON.stringify({
                    type: 'start_session',
                    tool_name: toolName,
                    args: args
                }));
            } else {
                clearTimeout(timeout);
                window.handleMessage = originalHandleMessage;
                throw new Error('WebSocket 未连接 - 请等待连接恢复');
            }

            // 恢复原始处理器（无论成功或失败）
            setTimeout(() => {
                window.handleMessage = originalHandleMessage;
            }, timeout._idleTimeout || 10000);
        });
    } catch (error) {
        hideLoading();
        throw handleError(error, '创建会话');
    }
}

async function stopSessionWithFeedback(sessionId) {
    showLoading('正在停止会话...');

    try {
        return await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('会话停止超时'));
            }, 5000);

            // 临时消息处理器
            const originalHandleMessage = window.handleMessage;

            const customHandler = (data) => {
                if (data.type === 'session_stopped') {
                    clearTimeout(timeout);
                    hideLoading();
                    showNotification('会话已停止', 'info');
                    resolve(data);
                } else if (data.type === 'error') {
                    clearTimeout(timeout);
                    hideLoading();
                    reject(new Error(`服务器错误: ${data.message}`));
                } else {
                    // 其他消息交给原始处理器
                    if (originalHandleMessage) {
                        originalHandleMessage(data);
                    }
                }
            };

            // 临时覆盖 handleMessage
            window.handleMessage = customHandler;

            // 发送请求
            if (window.ws && window.ws.readyState === WebSocket.OPEN) {
                window.ws.send(JSON.stringify({
                    type: 'stop_session',
                    session_id: sessionId
                }));
            } else {
                clearTimeout(timeout);
                window.handleMessage = originalHandleMessage;
                throw new Error('WebSocket 未连接');
            }

            // 恢复原始处理器
            setTimeout(() => {
                window.handleMessage = originalHandleMessage;
            }, timeout._idleTimeout || 5000);
        });
    } catch (error) {
        hideLoading();
        throw handleError(error, '停止会话');
    }
}

async function deleteSessionWithFeedback(sessionId) {
    if (!confirm('确定要删除这个会话吗？此操作不可恢复。')) {
        return;
    }

    showLoading('正在删除会话...');

    try {
        return await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('会话删除超时'));
            }, 5000);

            // 临时消息处理器
            const originalHandleMessage = window.handleMessage;

            const customHandler = (data) => {
                if (data.type === 'session_deleted') {
                    clearTimeout(timeout);
                    hideLoading();
                    showNotification('会话已删除', 'info');
                    // 从会话列表中移除
                    const index = window.SESSIONS.findIndex(s => s.session_id === sessionId);
                    if (index > -1) {
                        window.SESSIONS.splice(index, 1);
                        window.renderSessions();
                    }
                    resolve(data);
                } else if (data.type === 'error') {
                    clearTimeout(timeout);
                    hideLoading();
                    reject(new Error(`服务器错误: ${data.message}`));
                } else {
                    // 其他消息交给原始处理器
                    if (originalHandleMessage) {
                        originalHandleMessage(data);
                    }
                }
            };

            // 临时覆盖 handleMessage
            window.handleMessage = customHandler;

            // 发送请求
            if (window.ws && window.ws.readyState === WebSocket.OPEN) {
                window.ws.send(JSON.stringify({
                    type: 'delete_session',
                    session_id: sessionId
                }));
            } else {
                clearTimeout(timeout);
                window.handleMessage = originalHandleMessage;
                throw new Error('WebSocket 未连接');
            }

            // 恢复原始处理器
            setTimeout(() => {
                window.handleMessage = originalHandleMessage;
            }, timeout._idleTimeout || 5000);
        });
    } catch (error) {
        hideLoading();
        throw handleError(error, '删除会话');
    }
}

// 改进的终端输出
function addTerminalOutput(output, type = 'info') {
    const terminal = document.getElementById('terminal');
    if (!terminal) return;

    const line = document.createElement('div');
    line.className = `terminal-line terminal-${type}`;

    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    line.innerHTML = `
        <span style="color: rgba(255,255,255,255,0.3); margin-right: 1rem; font-size: 0.75rem;">[${timestamp}]</span>
        ${escapeHtml(output)}
    `;

    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;

    // 限制行数
    while (terminal.children.length > 1000) {
        terminal.removeChild(terminal.firstChild);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 改进的工具选择 - 已移除，使用 tools.js 中的版本

// 改进的连接状态更新
function updateConnectionStatusDetailed(connected, latency = null) {
    const statusIndicator = document.querySelector('.status-indicator');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');

    if (statusIndicator) {
        if (connected) {
            statusDot?.classList.add('connected');
            statusText.textContent = latency ? `已连接 (${latency}ms)` : '已连接';
            statusIndicator.style.borderColor = 'rgba(72, 187, 120, 0.3)';
        } else {
            statusDot?.classList.remove('connected');
            statusText.textContent = '未连接';
            statusIndicator.style.borderColor = 'rgba(245, 101, 101, 0.3)';
        }
    }
}

// 改进的工具验证
async function verifyToolAvailability(toolName) {
    if (!window.APP_STATE.isConnected) {
        throw new Error('请先连接 WebSocket');
    }

    const tool = window.TOOLS.find(t => t.id === toolName);
    if (!tool) {
        throw new Error(`未找到工具: ${toolName}`);
    }

    if (tool.status !== 'available') {
        throw new Error(`工具 ${tool.name} 当前不可用`);
    }

    return tool;
}

// 自动刷新会话列表
let autoRefreshInterval = null;

function enableAutoRefresh(enabled = true, interval = 30000) {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }

    if (enabled && window.APP_STATE.currentPage === 'sessions') {
        autoRefreshInterval = setInterval(() => {
            if (window.ws && window.ws.readyState === WebSocket.OPEN) {
                window.ws.send(JSON.stringify({ type: 'list_sessions' }));
            }
        }, interval);
        console.log(`🔄 自动刷新已启用: ${interval}ms`);
    }
}

// 导出改进函数
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showNotification = showNotification;
window.handleError = handleError;
window.createSessionWithFeedback = createSessionWithFeedback;
window.stopSessionWithFeedback = stopSessionWithFeedback;
window.deleteSessionWithFeedback = deleteSessionWithFeedback;
window.addTerminalOutput = addTerminalOutput;
window.updateConnectionStatusDetailed = updateConnectionStatusDetailed;
window.verifyToolAvailability = verifyToolAvailability;
window.enableAutoRefresh = enableAutoRefresh;
