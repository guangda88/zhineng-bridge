/**
 * Slash Commands System for 智桥
 * 实现斜杠命令 (/command) 功能
 */

class SlashCommandsManager {
    constructor() {
        this.commands = new Map();
        this.commandHistory = [];
        this.fuzzySearchIndex = [];

        // 初始化内置命令
        this.initBuiltinCommands();
    }

    /**
     * 初始化内置命令
     */
    initBuiltinCommands() {
        // /help - 显示帮助
        this.registerCommand({
            name: 'help',
            description: '显示帮助信息',
            usage: '/help [command]',
            handler: async (args) => {
                if (args.length > 0) {
                    const cmd = this.getCommand(args[0]);
                    if (cmd) {
                        return `## ${cmd.name}\n\n${cmd.description}\n\n用法: ${cmd.usage}`;
                    } else {
                        return `未找到命令: ${args[0]}`;
                    }
                }

                let help = '## 可用命令\n\n';
                this.commands.forEach((cmd, name) => {
                    help += `- \`/${name}\`: ${cmd.description}\n`;
                });
                help += '\n输入 \`/help <command>\` 查看详细帮助';

                return help;
            }
        });

        // /model - 切换模型
        this.registerCommand({
            name: 'model',
            description: '切换或查看当前模型',
            usage: '/model [model_name]',
            handler: async (args) => {
                if (args.length === 0) {
                    const currentModel = window.APP_STATE?.selectedModel || 'zai/glm-4.5';
                    const models = ['zai/glm-4.5', 'zai/glm-4.5-air', 'zai/glm-4.6', 'zai/glm-4.7', 'zai/glm-5'];
                    return `当前模型: ${currentModel}\n\n可用模型:\n${models.map(m => `- ${m}`).join('\n')}`;
                }

                const newModel = args[0];
                const availableModels = ['zai/glm-4.5', 'zai/glm-4.5-air', 'zai/glm-4.6', 'zai/glm-4.7', 'zai/glm-5'];

                if (!availableModels.includes(newModel)) {
                    return `无效的模型: ${newModel}\n\n可用模型: ${availableModels.join(', ')}`;
                }

                window.APP_STATE.selectedModel = newModel;
                return `✅ 已切换到模型: ${newModel}`;
            }
        });

        // /clear - 清除会话
        this.registerCommand({
            name: 'clear',
            description: '清除当前会话输出',
            usage: '/clear',
            handler: async () => {
                const terminal = document.getElementById('terminal');
                if (terminal) {
                    terminal.innerHTML = '';
                    return '✅ 会话输出已清除';
                }
                return '❌ 未找到终端';
            }
        });

        // /sessions - 列出所有会话
        this.registerCommand({
            name: 'sessions',
            description: '列出所有会话',
            usage: '/sessions',
            handler: async () => {
                const sessions = window.SESSIONS || [];
                if (sessions.length === 0) {
                    return '当前没有活动会话';
                }

                let output = '## 活动会话\n\n';
                sessions.forEach(session => {
                    const statusIcon = session.status === 'running' ? '🟢' : '⏹️';
                    output += `${statusIcon} ${session.session_id}: ${session.tool_name}\n`;
                });

                return output;
            }
        });

        // /tools - 列出可用工具
        this.registerCommand({
            name: 'tools',
            description: '列出所有可用工具',
            usage: '/tools',
            handler: async () => {
                const tools = window.TOOLS || [];
                let output = '## 可用工具\n\n';
                tools.forEach(tool => {
                    const statusIcon = tool.status === 'available' ? '✅' : '❌';
                    output += `${statusIcon} ${tool.icon} ${tool.name}: ${tool.description}\n`;
                });

                return output;
            }
        });

        // /settings - 打开设置
        this.registerCommand({
            name: 'settings',
            description: '打开设置页面',
            usage: '/settings',
            handler: async () => {
                if (window.navigateToPage) {
                    window.navigateToPage('settings');
                    return '✅ 正在打开设置...';
                }
                return '❌ 无法打开设置';
            }
        });

        // /exit - 退出当前会话
        this.registerCommand({
            name: 'exit',
            description: '退出当前会话',
            usage: '/exit',
            handler: async () => {
                if (window.APP_STATE?.selectedSession) {
                    if (window.sendMessage) {
                        window.sendMessage({
                            type: 'stop_session',
                            session_id: window.APP_STATE.selectedSession.session_id
                        });
                    }
                    window.APP_STATE.selectedSession = null;
                    if (window.navigateToPage) {
                        window.navigateToPage('sessions');
                    }
                    return '✅ 已退出会话';
                }
                return '❌ 当前没有活动会话';
            }
        });

        // /export - 导出会话
        this.registerCommand({
            name: 'export',
            description: '导出当前会话',
            usage: '/export [format]',
            handler: async (args) => {
                const format = args[0] || 'md';
                const terminal = document.getElementById('terminal');

                if (!terminal) {
                    return '❌ 未找到终端内容';
                }

                let content = '';
                terminal.querySelectorAll('.terminal-line').forEach(line => {
                    content += line.textContent + '\n';
                });

                const blob = new Blob([content], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `session-${Date.now()}.${format}`;
                a.click();
                URL.revokeObjectURL(url);

                return `✅ 会话已导出为 ${format}`;
            }
        });
    }

    /**
     * 注册自定义命令
     * @param {Object} command - 命令配置
     */
    registerCommand(command) {
        this.commands.set(command.name, command);
        this.updateFuzzySearchIndex();
        console.log(`✅ 已注册命令: /${command.name}`);
    }

    /**
     * 注销命令
     * @param {string} name - 命令名称
     */
    unregisterCommand(name) {
        this.commands.delete(name);
        this.updateFuzzySearchIndex();
        console.log(`✅ 已注销命令: /${name}`);
    }

    /**
     * 获取命令
     * @param {string} name - 命令名称
     * @returns {Object|null}
     */
    getCommand(name) {
        return this.commands.get(name) || null;
    }

    /**
     * 获取所有命令
     * @returns {Array}
     */
    getAllCommands() {
        return Array.from(this.commands.values());
    }

    /**
     * 检查输入是否为命令
     * @param {string} input - 用户输入
     * @returns {boolean}
     */
    isCommand(input) {
        return input.trim().startsWith('/');
    }

    /**
     * 解析命令
     * @param {string} input - 用户输入
     * @returns {Object} - {name, args}
     */
    parseCommand(input) {
        const parts = input.trim().split(/\s+/);
        const name = parts[0].substring(1); // 移除 /
        const args = parts.slice(1);

        return { name, args };
    }

    /**
     * 执行命令
     * @param {string} input - 用户输入
     * @returns {Promise<string>} - 命令输出
     */
    async executeCommand(input) {
        const { name, args } = this.parseCommand(input);
        const command = this.getCommand(name);

        if (!command) {
            return `❌ 未找到命令: /${name}\n\n输入 \`/help\` 查看可用命令`;
        }

        // 添加到历史记录
        this.addToHistory(input);

        // 执行命令
        try {
            const result = await command.handler(args);
            return result;
        } catch (error) {
            console.error(`❌ 命令执行失败: /${name}`, error);
            return `❌ 命令执行失败: ${error.message}`;
        }
    }

    /**
     * 模糊搜索命令
     * @param {string} query - 搜索查询
     * @returns {Array} - 匹配的命令
     */
    fuzzySearch(query) {
        if (!query) {
            return this.getAllCommands();
        }

        const lowerQuery = query.toLowerCase();
        return this.getAllCommands().filter(cmd =>
            cmd.name.toLowerCase().includes(lowerQuery) ||
            cmd.description.toLowerCase().includes(lowerQuery)
        );
    }

    /**
     * 更新模糊搜索索引
     */
    updateFuzzySearchIndex() {
        this.fuzzySearchIndex = this.getAllCommands();
    }

    /**
     * 添加到历史记录
     * @param {string} input - 用户输入
     */
    addToHistory(input) {
        // 避免重复
        if (this.commandHistory.length > 0 && this.commandHistory[0] === input) {
            return;
        }

        this.commandHistory.unshift(input);

        // 限制历史记录大小
        if (this.commandHistory.length > 100) {
            this.commandHistory.pop();
        }
    }

    /**
     * 获取历史记录
     * @returns {Array}
     */
    getHistory() {
        return [...this.commandHistory];
    }

    /**
     * 清除历史记录
     */
    clearHistory() {
        this.commandHistory = [];
    }

    /**
     * 创建命令自动补全 UI
     * @param {HTMLElement} textarea - 输入框元素
     */
    createAutoCompleteUI(textarea) {
        const wrapper = document.createElement('div');
        wrapper.className = 'slash-command-wrapper';
        wrapper.style.position = 'relative';

        const commandList = document.createElement('div');
        commandList.className = 'slash-command-list';
        commandList.style.display = 'none';
        commandList.style.position = 'absolute';
        commandList.style.bottom = '100%';
        commandList.style.left = '0';
        commandList.style.width = '100%';
        commandList.style.maxHeight = '200px';
        commandList.style.overflow = 'auto';
        commandList.style.background = 'white';
        commandList.style.border = '1px solid #ccc';
        commandList.style.borderRadius = '4px';
        commandList.style.zIndex = '1000';

        let selectedIndex = 0;
        let filteredCommands = [];

        // 监听输入
        textarea.addEventListener('input', (e) => {
            const value = e.target.value;
            const cursorPosition = e.target.selectionStart;

            // 查找 / 符号后面的文本
            const beforeCursor = value.substring(0, cursorPosition);
            const slashIndex = beforeCursor.lastIndexOf('/');

            if (slashIndex === -1) {
                commandList.style.display = 'none';
                return;
            }

            const query = beforeCursor.substring(slashIndex + 1);

            // 如果查询包含空格，隐藏提示
            if (query.includes(' ')) {
                commandList.style.display = 'none';
                return;
            }

            // 搜索命令
            filteredCommands = this.fuzzySearch(query);

            if (filteredCommands.length === 0) {
                commandList.style.display = 'none';
                return;
            }

            // 显示命令列表
            selectedIndex = 0;
            this.renderCommandList(commandList, filteredCommands, selectedIndex, e.target, slashIndex);
            commandList.style.display = 'block';
        });

        // 监听键盘事件
        textarea.addEventListener('keydown', (e) => {
            if (commandList.style.display === 'none') {
                return;
            }

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, filteredCommands.length - 1);
                this.renderCommandList(commandList, filteredCommands, selectedIndex, textarea, 0);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, 0);
                this.renderCommandList(commandList, filteredCommands, selectedIndex, textarea, 0);
            } else if (e.key === 'Tab' || e.key === 'Enter') {
                e.preventDefault();
                if (filteredCommands[selectedIndex]) {
                    const afterCursor = textarea.value.substring(textarea.selectionStart);
                    textarea.value = textarea.value.substring(0, textarea.value.lastIndexOf('/')) + '/' + filteredCommands[selectedIndex].name + ' ' + afterCursor;
                    commandList.style.display = 'none';
                }
            } else if (e.key === 'Escape') {
                commandList.style.display = 'none';
            }
        });

        // 点击其他地方隐藏提示
        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) {
                commandList.style.display = 'none';
            }
        });

        wrapper.appendChild(textarea);
        wrapper.appendChild(commandList);

        return wrapper;
    }

    /**
     * 渲染命令列表
     */
    renderCommandList(listElement, commands, selectedIndex, textarea, slashIndex) {
        listElement.innerHTML = '';
        commands.forEach((cmd, index) => {
            const item = document.createElement('div');
            item.className = 'slash-command-item';
            item.style.padding = '8px 12px';
            item.style.cursor = 'pointer';
            item.style.background = index === selectedIndex ? '#f0f0f0' : 'white';

            item.innerHTML = `
                <strong>/${cmd.name}</strong>
                <small style="color: #666; margin-left: 8px;">${cmd.description}</small>
            `;

            item.addEventListener('click', () => {
                const afterCursor = textarea.value.substring(textarea.selectionStart);
                textarea.value = textarea.value.substring(0, slashIndex + 1) + cmd.name + ' ' + afterCursor;
                listElement.style.display = 'none';
                textarea.focus();
            });

            listElement.appendChild(item);
        });
    }
}

// 导出为全局变量
window.SlashCommandsManager = SlashCommandsManager;

// 自动初始化
if (typeof window !== 'undefined') {
    window.slashCommandsManager = new SlashCommandsManager();
}
