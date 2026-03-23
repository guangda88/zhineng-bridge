/**
 * 会话管理逻辑
 */

// 渲染会话列表
function renderSessions() {
    const sessionsList = document.getElementById('sessionsList');
    
    if (!sessionsList) {
        console.warn('⚠️  sessionsList 元素不存在');
        return;
    }
    
    // 清空会话列表
    sessionsList.innerHTML = '';
    
    // 生成会话卡片
    if (SESSIONS.length === 0) {
        sessionsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <div class="empty-text">暂无会话</div>
                <div class="empty-description">点击"新建会话"创建第一个会话</div>
            </div>
        `;
    } else {
        SESSIONS.forEach(session => {
            const card = createSessionCard(session);
            sessionsList.appendChild(card);
        });
    }
    
    console.log(`✅ 已渲染 ${SESSIONS.length} 个会话`);
}

// 创建会话卡片
function createSessionCard(session) {
    const card = document.createElement('div');
    card.className = 'session-card';
    card.dataset.sessionId = session.session_id;
    
    const statusClass = session.status === 'running' ? 'running' : 'stopped';
    const statusText = session.status === 'running' ? '运行中' : '已停止';
    const statusIcon = session.status === 'running' ? '🟢' : '🔴';
    
    const tool = TOOLS.find(t => t.id === session.tool_name);
    const toolIcon = tool ? tool.icon : '❓';
    const toolColor = tool ? tool.color : '#666';
    
    const createdAt = new Date(session.created_at).toLocaleString('zh-CN');
    
    card.innerHTML = `
        <div class="session-info-header">
            <div class="session-tool" style="color: ${toolColor}">${toolIcon}</div>
            <div class="session-details">
                <div class="session-id">ID: ${session.session_id.substring(0, 8)}...</div>
                <div class="session-status ${statusClass}">
                    <span class="status-icon">${statusIcon}</span>
                    <span class="status-text">${statusText}</span>
                </div>
                <div class="session-tool-name">${tool ? tool.name : session.tool_name}</div>
                <div class="session-created-at">创建于: ${createdAt}</div>
            </div>
        </div>
        <div class="session-actions">
            <button class="btn btn-primary" onclick="openSession('${session.session_id}')">打开</button>
            ${session.status === 'running' ? 
                `<button class="btn btn-secondary" onclick="stopSession('${session.session_id}')">停止</button>` :
                `<button class="btn btn-secondary" onclick="startSession('${session.session_id}')">运行</button>`
            }
            <button class="btn btn-danger" onclick="deleteSession('${session.session_id}')">删除</button>
        </div>
    `;
    
    return card;
}

// 新建会话
async function newSession() {
    console.log('➕ 新建会话');
    
    if (!APP_STATE.selectedTool) {
        showNotification('请先选择一个工具', 'error');
        navigateToPage('tools');
        return;
    }
    
    // 发送新建会话请求
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        window.ws.send(JSON.stringify({
            type: 'start_session',
            tool_name: APP_STATE.selectedTool.id,
            args: []
        }));
    } else {
        showNotification('WebSocket 未连接', 'error');
    }
}

// 刷新会话列表
function refreshSessions() {
    console.log('🔄 刷新会话列表');
    
    // 发送刷新请求
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        window.ws.send(JSON.stringify({
            type: 'list_sessions'
        }));
    }
}

// 打开会话
function openSession(sessionId) {
    console.log(`📂 打开会话: ${sessionId}`);
    
    APP_STATE.selectedSession = sessionId;
    navigateToPage('session-detail');
    renderSessionDetail(sessionId);
}

// 开始会话
function startSession(sessionId) {
    console.log(`▶️ 开始会话: ${sessionId}`);
    
    // 发送启动请求
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        window.ws.send(JSON.stringify({
            type: 'start_session',
            session_id: sessionId
        }));
    }
}

// 停止会话
function stopSession(sessionId) {
    console.log(`⏹️  停止会话: ${sessionId}`);
    
    // 发送停止请求
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        window.ws.send(JSON.stringify({
            type: 'stop_session',
            session_id: sessionId
        }));
    }
}

// 删除会话
function deleteSession(sessionId) {
    console.log(`🗑️  删除会话: ${sessionId}`);
    
    if (confirm('确定要删除这个会话吗？')) {
        // 发送删除请求
        if (window.ws && window.ws.readyState === WebSocket.OPEN) {
            window.ws.send(JSON.stringify({
                type: 'delete_session',
                session_id: sessionId
            }));
        }
    }
}

// 渲染会话详情
function renderSessionDetail(sessionId) {
    const session = SESSIONS.find(s => s.session_id === sessionId);
    
    if (!session) {
        console.warn('⚠️  会话不存在:', sessionId);
        return;
    }
    
    const sessionInfo = document.getElementById('sessionInfo');
    const tool = TOOLS.find(t => t.id === session.tool_name);
    
    sessionInfo.innerHTML = `
        <div class="session-detail-card">
            <div class="session-detail-header">
                <div class="session-detail-icon" style="color: ${tool ? tool.color : '#666'}">
                    ${tool ? tool.icon : '❓'}
                </div>
                <div class="session-detail-info">
                    <h3 class="session-detail-title">${tool ? tool.name : session.tool_name}</h3>
                    <div class="session-detail-id">ID: ${session.session_id}</div>
                    <div class="session-detail-status">
                        <span class="status-dot ${session.status === 'running' ? 'connected' : ''}"></span>
                        <span class="status-text">${session.status === 'running' ? '运行中' : '已停止'}</span>
                    </div>
                </div>
            </div>
            <div class="session-detail-actions">
                ${session.status === 'running' ? 
                    `<button class="btn btn-secondary" onclick="stopSession('${session.session_id}')">停止</button>` :
                    `<button class="btn btn-primary" onclick="startSession('${session.session_id}')">运行</button>`
                }
                <button class="btn btn-secondary" onclick="navigateToPage('sessions')">返回</button>
            </div>
        </div>
    `;
}

// 消息处理
function handleSessionStarted(data) {
    console.log('✅ 会话已启动:', data);
    
    // 添加到会话列表
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
}

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
}

// 导出函数
window.SESSIONS = SESSIONS;
window.renderSessions = renderSessions;
window.newSession = newSession;
window.refreshSessions = refreshSessions;
window.openSession = openSession;
window.startSession = startSession;
window.stopSession = stopSession;
window.deleteSession = deleteSession;
window.renderSessionDetail = renderSessionDetail;
window.handleSessionStarted = handleSessionStarted;
window.handleSessionStopped = handleSessionStopped;
