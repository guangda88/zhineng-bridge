/**
 * WebSocket 客户端逻辑
 */

let ws = null;

// 连接 WebSocket
function connectWebSocket() {
    const settings = SETTINGS || [];
    const wsHost = settings.find(s => s.id === 'ws_host')?.value || 'localhost';
    const wsPort = settings.find(s => s.id === 'ws_port')?.value || 8765;
    const autoReconnect = settings.find(s => s.id === 'auto_reconnect')?.value !== false;
    const reconnectInterval = settings.find(s => s.id === 'reconnect_interval')?.value || 5;
    
    const url = `ws://${wsHost}:${wsPort}`;
    
    console.log(`🔌 连接 WebSocket: ${url}`);
    
    try {
        ws = new WebSocket(url);
        
        ws.onopen = () => {
            console.log('✅ WebSocket 已连接');
            APP_STATE.isConnected = true;
            updateConnectionStatus(true);
            
            // 发送心跳
            startHeartbeat();
        };
        
        ws.onclose = (event) => {
            console.log(`❌ WebSocket 已断开: code=${event.code}, reason=${event.reason}`);
            APP_STATE.isConnected = false;
            updateConnectionStatus(false);
            
            // 停止心跳
            stopHeartbeat();
            
            // 自动重连
            if (autoReconnect) {
                console.log(`🔄 ${reconnectInterval} 秒后自动重连...`);
                setTimeout(connectWebSocket, reconnectInterval * 1000);
            }
        };
        
        ws.onerror = (error) => {
            console.error('❌ WebSocket 错误:', error);
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleMessage(data);
            } catch (error) {
                console.error('❌ 消息解析失败:', error);
            }
        };
        
        // 保存到全局
        window.ws = ws;
        
        return ws;
    } catch (error) {
        console.error('❌ WebSocket 连接失败:', error);
        return null;
    }
}

// 断开 WebSocket
function disconnectWebSocket() {
    if (ws) {
        console.log('🔌 断开 WebSocket');
        ws.close();
        ws = null;
        window.ws = null;
    }
}

// 更新连接状态
function updateConnectionStatus(connected) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    if (statusDot) {
        if (connected) {
            statusDot.classList.add('connected');
        } else {
            statusDot.classList.remove('connected');
        }
    }
    
    if (statusText) {
        statusText.textContent = connected ? '已连接' : '未连接';
    }
}

// 心跳
let heartbeatInterval = null;

function startHeartbeat() {
    const pingInterval = SETTINGS?.find(s => s.id === 'ping_interval')?.value || 10;
    
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
    }
    
    heartbeatInterval = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
            console.log('💓 心跳发送');
        }
    }, pingInterval * 1000);
    
    console.log(`💓 心跳已启动: ${pingInterval} 秒`);
}

function stopHeartbeat() {
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
        console.log('💓 心跳已停止');
    }
}

// 发送消息
function sendMessage(message) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
        console.log('📤 消息已发送:', message);
    } else {
        console.error('❌ WebSocket 未连接，无法发送消息');
        showNotification('WebSocket 未连接', 'error');
    }
}

// 消息处理
function handleMessage(data) {
    console.log('📨 收到消息:', data);
    
    switch (data.type) {
        case 'session_started':
            handleSessionStarted(data);
            break;
        case 'session_stopped':
            handleSessionStopped(data);
            break;
        case 'command_sent':
            handleCommandSent(data);
            break;
        case 'output':
            handleOutput(data);
            break;
        case 'sessions_list':
            handleSessionsList(data);
            break;
        case 'pong':
            console.log('💓 心跳响应');
            break;
        default:
            console.warn('⚠️  未知消息类型:', data.type);
    }
}

// 处理会话启动
function handleSessionStarted(data) {
    console.log('✅ 会话已启动:', data);
    
    // 更新会话列表
    SESSIONS.push({
        session_id: data.session_id,
        tool_name: data.tool_name,
        status: 'running',
        created_at: new Date().toISOString()
    });
    
    // 重新渲染会话列表
    renderSessions();
    
    // 显示通知
    showNotification('会话已启动', 'success');
    
    // 如果在会话详情页面，更新详情
    if (APP_STATE.currentPage === 'session-detail' && APP_STATE.selectedSession) {
        renderSessionDetail(APP_STATE.selectedSession);
    }
}

// 处理会话停止
function handleSessionStopped(data) {
    console.log('⏹️  会话已停止:', data);
    
    // 更新会话状态
    const session = SESSIONS.find(s => s.session_id === data.session_id);
    if (session) {
        session.status = 'stopped';
    }
    
    // 重新渲染会话列表
    renderSessions();
    
    // 显示通知
    showNotification('会话已停止', 'info');
    
    // 如果在会话详情页面，更新详情
    if (APP_STATE.currentPage === 'session-detail' && APP_STATE.selectedSession) {
        renderSessionDetail(APP_STATE.selectedSession);
    }
}

// 处理命令发送
function handleCommandSent(data) {
    console.log('📤 命令已发送:', data);
    showNotification('命令已发送', 'success');
}

// 处理输出
function handleOutput(data) {
    console.log('📤 输出:', data);
    
    // 添加到终端
    const terminal = document.getElementById('terminal');
    if (terminal) {
        const outputLine = document.createElement('div');
        outputLine.className = 'terminal-line';
        outputLine.textContent = data.output || '';
        terminal.appendChild(outputLine);
        
        // 自动滚动
        const autoScroll = SETTINGS?.find(s => s.id === 'output_scroll')?.value !== false;
        if (autoScroll) {
            terminal.scrollTop = terminal.scrollHeight;
        }
        
        // 限制最大行数
        const maxLines = SETTINGS?.find(s => s.id === 'output_max_lines')?.value || 1000;
        while (terminal.children.length > maxLines) {
            terminal.removeChild(terminal.firstChild);
        }
    }
}

// 处理会话列表
function handleSessionsList(data) {
    console.log('📋 会话列表:', data);
    
    // 更新会话列表
    SESSIONS = data.sessions || [];
    
    // 重新渲染会话列表
    renderSessions();
}

// 导出函数
window.connectWebSocket = connectWebSocket;
window.disconnectWebSocket = disconnectWebSocket;
window.sendMessage = sendMessage;
window.ws = ws;
