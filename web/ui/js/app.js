/**
 * 智桥 - 主应用逻辑
 */

// 工具列表
const TOOLS = [
    {
        id: 'crush',
        name: 'Crush',
        icon: '💎',
        description: 'Charmbracelet Crush - AI 编码助手',
        status: 'available',
        color: '#FFE66D'
    },
    {
        id: 'claude',
        name: 'Claude Code',
        icon: '🤖',
        description: 'Anthropic Claude Code - AI 编码助手',
        status: 'available',
        color: '#FF6B6B'
    },
    {
        id: 'iflow',
        name: 'iFlow CLI',
        icon: '🌊',
        description: '阿里巴巴心流 iFlow CLI - AI 编码助手',
        status: 'available',
        color: '#4ECDC4'
    },
    {
        id: 'cursor',
        name: 'Cursor',
        icon: '👆',
        description: 'Anysphere Cursor - AI IDE',
        status: 'available',
        color: '#45B7D1'
    },
    {
        id: 'trae',
        name: 'Trae',
        icon: '🌊',
        description: '字节跳动 Trae - AI IDE（国产）',
        status: 'available',
        color: '#96CEB4'
    },
    {
        id: 'factroydroid',
        name: 'Droid',
        icon: '🤖',
        description: 'Factory Droid - AI Agent',
        status: 'available',
        color: '#FFEEAD'
    },
    {
        id: 'openclaw',
        name: 'OpenClaw',
        icon: '🦞',
        description: 'OpenClaw - AI 助手',
        status: 'available',
        color: '#D4A5A5'
    },
    {
        id: 'copilot',
        name: 'GitHub Copilot',
        icon: '🤖',
        description: 'GitHub Copilot - AI 助手',
        status: 'available',
        color: '#F0F0F0'
    }
];

// 会话列表
let SESSIONS = [];

// 应用状态
const APP_STATE = {
    currentPage: 'tools',
    selectedTool: null,
    selectedSession: null,
    isConnected: false
};

// 初始化应用
function initApp() {
    console.log('🚀 智桥应用初始化');
    
    // 渲染工具列表
    renderTools();
    
    // 渲染会话列表
    renderSessions();
    
    // 设置导航
    setupNavigation();
    
    // 连接 WebSocket
    connectWebSocket();
}

// 导航功能
function setupNavigation() {
    // 桌面导航
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('href').substring(1);
            navigateToPage(page);
        });
    });
    
    // 底部导航
    document.querySelectorAll('.footer-nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('data-page');
            navigateToPage(page);
        });
    });
}

function navigateToPage(page) {
    // 隐藏所有页面
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    
    // 显示目标页面
    document.getElementById(page).classList.add('active');
    
    // 更新导航状态
    document.querySelectorAll('.nav-item, .footer-nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('href') === `#${page}` ||
            item.getAttribute('data-page') === page) {
            item.classList.add('active');
        }
    });
    
    // 更新应用状态
    APP_STATE.currentPage = page;
    
    console.log(`📄 导航到页面: ${page}`);
}

// WebSocket 连接
function connectWebSocket() {
    const ws = new WebSocket('ws://localhost:8765');
    
    ws.onopen = () => {
        console.log('✅ WebSocket 已连接');
        APP_STATE.isConnected = true;
        updateConnectionStatus(true);
    };
    
    ws.onclose = () => {
        console.log('❌ WebSocket 已断开');
        APP_STATE.isConnected = false;
        updateConnectionStatus(false);
        
        // 5 秒后重连
        setTimeout(connectWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
        console.error('❌ WebSocket 错误:', error);
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
    
    return ws;
}

// 更新连接状态
function updateConnectionStatus(connected) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    if (connected) {
        statusDot.classList.add('connected');
        statusText.textContent = '已连接';
    } else {
        statusDot.classList.remove('connected');
        statusText.textContent = '未连接';
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
        default:
            console.warn('⚠️  未知消息类型:', data.type);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initApp);
