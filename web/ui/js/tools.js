/**
 * 工具选择逻辑
 */

// 渲染工具列表
function renderTools() {
    const toolsGrid = document.getElementById('toolsGrid');
    
    if (!toolsGrid) {
        console.warn('⚠️  toolsGrid 元素不存在');
        return;
    }
    
    // 清空工具列表
    toolsGrid.innerHTML = '';
    
    // 生成工具卡片
    TOOLS.forEach(tool => {
        const card = createToolCard(tool);
        toolsGrid.appendChild(card);
    });
    
    console.log(`✅ 已渲染 ${TOOLS.length} 个工具`);
}

// 创建工具卡片
function createToolCard(tool) {
    const card = document.createElement('div');
    card.className = 'tool-card';
    card.dataset.toolId = tool.id;
    
    const statusClass = tool.status === 'available' ? 'available' : 'unavailable';
    const statusText = tool.status === 'available' ? '可用' : '不可用';
    
    card.innerHTML = `
        <div class="tool-icon" style="color: ${tool.color}">${tool.icon}</div>
        <div class="tool-name">${tool.name}</div>
        <div class="tool-description">${tool.description}</div>
        <div class="tool-status ${statusClass}">
            <span class="status-dot"></span>
            <span class="status-text">${statusText}</span>
        </div>
    `;
    
    // 点击事件
    card.addEventListener('click', () => selectTool(tool));
    
    return card;
}

// 选择工具
function selectTool(tool) {
    console.log(`🎯 选择工具: ${tool.name}`);
    
    // 更新应用状态
    APP_STATE.selectedTool = tool;
    
    // 导航到会话页面
    navigateToPage('sessions');
    
    // 显示通知
    showNotification(`已选择 ${tool.name}`, 'success');
}

// 显示通知
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 3 秒后移除
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 导出函数
window.TOOLS = TOOLS;
window.renderTools = renderTools;
window.selectTool = selectTool;
