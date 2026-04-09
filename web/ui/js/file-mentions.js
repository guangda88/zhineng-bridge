/**
 * File Mentions System for 智桥
 * 实现文件提及功能 (@file)
 */

class FileMentionsManager {
    constructor() {
        this.fileCache = new Map();
        this.currentDirectory = '';
    }

    /**
     * 解析输入中的文件提及
     * @param {string} input - 用户输入
     * @returns {Array} - 提及的文件路径数组
     */
    parseFileMentions(input) {
        const regex = /@([^\s@]+)/g;
        const mentions = [];
        let match;

        while ((match = regex.exec(input)) !== null) {
            mentions.push(match[1]);
        }

        return mentions;
    }

    /**
     * 验证文件路径是否有效
     * @param {string} filePath - 文件路径
     * @returns {boolean}
     */
    async validateFilePath(filePath) {
        // 检查路径是否包含非法字符
        const invalidChars = /[<>:"|?*]/;
        if (invalidChars.test(filePath)) {
            return false;
        }

        // 检查路径是否试图访问父目录（安全考虑）
        if (filePath.includes('..')) {
            return false;
        }

        return true;
    }

    /**
     * 获取文件内容
     * @param {string} filePath - 文件路径
     * @returns {Promise<string>} - 文件内容
     */
    async getFileContent(filePath) {
        // 先检查缓存
        if (this.fileCache.has(filePath)) {
            return this.fileCache.get(filePath);
        }

        try {
            const response = await fetch(`/api/files/read?path=${encodeURIComponent(filePath)}`);
            if (!response.ok) {
                throw new Error(`无法读取文件: ${filePath}`);
            }

            const data = await response.json();
            const content = data.content;

            // 缓存文件内容
            this.fileCache.set(filePath, content);

            return content;
        } catch (error) {
            console.error('❌ 获取文件内容失败:', error);
            return `[无法读取文件 ${filePath}: ${error.message}]`;
        }
    }

    /**
     * 注入文件上下文到提示词
     * @param {string} prompt - 原始提示词
     * @param {Array} filePaths - 文件路径数组
     * @returns {Promise<string>} - 增强后的提示词
     */
    async injectFileContext(prompt, filePaths) {
        if (filePaths.length === 0) {
            return prompt;
        }

        const contextParts = [];

        for (const filePath of filePaths) {
            const isValid = await this.validateFilePath(filePath);
            if (!isValid) {
                contextParts.push(`### 文件: ${filePath}\n(路径无效或包含非法字符)`);
                continue;
            }

            const content = await this.getFileContent(filePath);
            contextParts.push(`### 文件: ${filePath}\n\`\`\`\n${content}\n\`\`\``);
        }

        const context = contextParts.join('\n\n');
        const enhancedPrompt = `${prompt}\n\n---\n\n# 相关文件内容\n\n${context}`;

        return enhancedPrompt;
    }

    /**
     * 处理用户输入中的文件提及
     * @param {string} input - 用户输入
     * @returns {Promise<{prompt: string, mentions: Array}>} - 处理结果
     */
    async processInput(input) {
        const mentions = this.parseFileMentions(input);

        if (mentions.length === 0) {
            return { prompt: input, mentions: [] };
        }

        // 移除文件提及符号，保持原始路径
        let cleanPrompt = input;
        mentions.forEach(mention => {
            cleanPrompt = cleanPrompt.replace(`@${mention}`, mention);
        });

        // 注入文件上下文
        const enhancedPrompt = await this.injectFileContext(cleanPrompt, mentions);

        return {
            prompt: enhancedPrompt,
            mentions: mentions,
            cleanPrompt: cleanPrompt
        };
    }

    /**
     * 搜索文件（自动补全）
     * @param {string} query - 搜索查询
     * @returns {Promise<Array>} - 匹配的文件列表
     */
    async searchFiles(query) {
        try {
            const response = await fetch(`/api/files/search?q=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error('搜索失败');
            }

            const data = await response.json();
            return data.files || [];
        } catch (error) {
            console.error('❌ 搜索文件失败:', error);
            return [];
        }
    }

    /**
     * 清除文件缓存
     */
    clearCache() {
        this.fileCache.clear();
    }

    /**
     * 获取文件统计信息
     * @param {string} filePath - 文件路径
     * @returns {Promise<Object>} - 文件统计信息
     */
    async getFileStats(filePath) {
        try {
            const response = await fetch(`/api/files/stats?path=${encodeURIComponent(filePath)}`);
            if (!response.ok) {
                throw new Error('获取统计信息失败');
            }

            return await response.json();
        } catch (error) {
            console.error('❌ 获取文件统计失败:', error);
            return null;
        }
    }

    /**
     * 创建文件提及提示 UI
     * @param {HTMLElement} textarea - 输入框元素
     */
    createMentionUI(textarea) {
        const wrapper = document.createElement('div');
        wrapper.className = 'file-mention-wrapper';
        wrapper.style.position = 'relative';

        const mentionList = document.createElement('div');
        mentionList.className = 'file-mention-list';
        mentionList.style.display = 'none';
        mentionList.style.position = 'absolute';
        mentionList.style.bottom = '100%';
        mentionList.style.left = '0';
        mentionList.style.width = '100%';
        mentionList.style.maxHeight = '200px';
        mentionList.style.overflow = 'auto';
        mentionList.style.background = 'white';
        mentionList.style.border = '1px solid #ccc';
        mentionList.style.borderRadius = '4px';
        mentionList.style.zIndex = '1000';

        // 监听输入
        textarea.addEventListener('input', async (e) => {
            const value = e.target.value;
            const cursorPosition = e.target.selectionStart;

            // 查找 @ 符号后面的文本
            const beforeCursor = value.substring(0, cursorPosition);
            const atIndex = beforeCursor.lastIndexOf('@');

            if (atIndex === -1) {
                mentionList.style.display = 'none';
                return;
            }

            const query = beforeCursor.substring(atIndex + 1);

            // 如果查询为空或包含空格，隐藏提示
            if (query === '' || query.includes(' ')) {
                mentionList.style.display = 'none';
                return;
            }

            // 搜索文件
            const files = await this.searchFiles(query);

            if (files.length === 0) {
                mentionList.style.display = 'none';
                return;
            }

            // 显示文件列表
            mentionList.innerHTML = '';
            files.forEach(file => {
                const item = document.createElement('div');
                item.className = 'file-mention-item';
                item.style.padding = '8px 12px';
                item.style.cursor = 'pointer';
                item.textContent = file.path;

                item.addEventListener('click', () => {
                    const afterCursor = value.substring(cursorPosition);
                    e.target.value = beforeCursor.substring(0, atIndex) + file.path + afterCursor;
                    mentionList.style.display = 'none';
                });

                item.addEventListener('mouseover', () => {
                    item.style.background = '#f0f0f0';
                });

                item.addEventListener('mouseout', () => {
                    item.style.background = 'white';
                });

                mentionList.appendChild(item);
            });

            mentionList.style.display = 'block';
        });

        // 点击其他地方隐藏提示
        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) {
                mentionList.style.display = 'none';
            }
        });

        wrapper.appendChild(textarea);
        wrapper.appendChild(mentionList);

        return wrapper;
    }
}

// 导出为全局变量
window.FileMentionsManager = FileMentionsManager;

// 自动初始化
if (typeof window !== 'undefined') {
    window.fileMentionsManager = new FileMentionsManager();
}
