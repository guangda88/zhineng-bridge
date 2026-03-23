/**
 * 设置页面逻辑
 */

// 设置列表
const SETTINGS = [
    {
        id: 'ws_host',
        name: 'WebSocket 主机',
        description: '中继服务器地址',
        type: 'text',
        default: 'localhost',
        value: 'localhost'
    },
    {
        id: 'ws_port',
        name: 'WebSocket 端口',
        description: '中继服务器端口',
        type: 'number',
        default: 8765,
        value: 8765
    },
    {
        id: 'auto_reconnect',
        name: '自动重连',
        description: '断开后自动重新连接',
        type: 'switch',
        default: true,
        value: true
    },
    {
        id: 'reconnect_interval',
        name: '重连间隔',
        description: '重连尝试间隔（秒）',
        type: 'number',
        default: 5,
        value: 5
    },
    {
        id: 'ping_interval',
        name: '心跳间隔',
        description: 'WebSocket 心跳间隔（秒）',
        type: 'number',
        default: 10,
        value: 10
    },
    {
        id: 'output_scroll',
        name: '自动滚动',
        description: '新输出时自动滚动到底部',
        type: 'switch',
        default: true,
        value: true
    },
    {
        id: 'output_max_lines',
        name: '最大输出行数',
        description: '终端最大显示行数',
        type: 'number',
        default: 1000,
        value: 1000
    },
    {
        id: 'command_history',
        name: '命令历史',
        description: '保存命令历史记录',
        type: 'switch',
        default: true,
        value: true
    },
    {
        id: 'theme',
        name: '主题',
        description: '应用主题',
        type: 'select',
        options: ['light', 'dark'],
        default: 'light',
        value: 'light'
    },
    {
        id: 'language',
        name: '语言',
        description: '应用界面语言',
        type: 'select',
        options: ['zh-CN', 'en-US'],
        default: 'zh-CN',
        value: 'zh-CN'
    }
];

// 渲染设置列表
function renderSettings() {
    const settingsList = document.getElementById('settingsList');
    
    if (!settingsList) {
        console.warn('⚠️  settingsList 元素不存在');
        return;
    }
    
    // 清空设置列表
    settingsList.innerHTML = '';
    
    // 生成设置项
    SETTINGS.forEach(setting => {
        const item = createSettingItem(setting);
        settingsList.appendChild(item);
    });
    
    console.log(`✅ 已渲染 ${SETTINGS.length} 个设置项`);
}

// 创建设置项
function createSettingItem(setting) {
    const item = document.createElement('div');
    item.className = 'setting-item';
    item.dataset.settingId = setting.id;
    
    let inputHtml = '';
    
    switch (setting.type) {
        case 'text':
            inputHtml = `
                <input 
                    type="text" 
                    id="setting-${setting.id}" 
                    value="${setting.value}" 
                    onchange="updateSetting('${setting.id}', this.value)"
                />
            `;
            break;
        case 'number':
            inputHtml = `
                <input 
                    type="number" 
                    id="setting-${setting.id}" 
                    value="${setting.value}" 
                    onchange="updateSetting('${setting.id}', this.value)"
                />
            `;
            break;
        case 'switch':
            inputHtml = `
                <label class="switch">
                    <input 
                        type="checkbox" 
                        id="setting-${setting.id}" 
                        ${setting.value ? 'checked' : ''} 
                        onchange="updateSetting('${setting.id}', this.checked)"
                    />
                    <span class="switch-slider"></span>
                </label>
            `;
            break;
        case 'select':
            const options = setting.options.map(opt => 
                `<option value="${opt}" ${setting.value === opt ? 'selected' : ''}>${opt}</option>`
            ).join('');
            inputHtml = `
                <select 
                    id="setting-${setting.id}" 
                    onchange="updateSetting('${setting.id}', this.value)"
                >
                    ${options}
                </select>
            `;
            break;
        default:
            inputHtml = `<span class="setting-type">未知类型: ${setting.type}</span>`;
    }
    
    item.innerHTML = `
        <div class="setting-info">
            <h3 class="setting-name">${setting.name}</h3>
            <p class="setting-description">${setting.description}</p>
        </div>
        <div class="setting-control">
            ${inputHtml}
        </div>
    `;
    
    return item;
}

// 更新设置
function updateSetting(settingId, value) {
    const setting = SETTINGS.find(s => s.id === settingId);
    if (setting) {
        setting.value = value;
        console.log(`⚙️  更新设置: ${setting.name} = ${value}`);
        
        // 保存到本地存储
        saveSettings();
        
        // 显示通知
        showNotification(`已更新: ${setting.name}`, 'success');
    }
}

// 保存设置到本地存储
function saveSettings() {
    const settings = {};
    SETTINGS.forEach(setting => {
        settings[setting.id] = setting.value;
    });
    
    localStorage.setItem('zhineng-bridge-settings', JSON.stringify(settings));
    console.log('💾 设置已保存到本地存储');
}

// 从本地存储加载设置
function loadSettings() {
    const saved = localStorage.getItem('zhineng-bridge-settings');
    if (saved) {
        try {
            const settings = JSON.parse(saved);
            SETTINGS.forEach(setting => {
                if (settings[setting.id] !== undefined) {
                    setting.value = settings[setting.id];
                }
            });
            console.log('📂 已从本地存储加载设置');
        } catch (error) {
            console.error('❌ 加载设置失败:', error);
        }
    }
}

// 重置设置
function resetSettings() {
    if (confirm('确定要重置所有设置吗？')) {
        SETTINGS.forEach(setting => {
            setting.value = setting.default;
        });
        
        saveSettings();
        renderSettings();
        
        showNotification('设置已重置', 'info');
    }
}

// 应用主题
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    console.log(`🎨 应用主题: ${theme}`);
}

// 导出函数
window.SETTINGS = SETTINGS;
window.renderSettings = renderSettings;
window.updateSetting = updateSetting;
window.saveSettings = saveSettings;
window.loadSettings = loadSettings;
window.resetSettings = resetSettings;
window.applyTheme = applyTheme;
