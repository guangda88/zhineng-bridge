/**
 * AI 工具集成示例 - Crush AI Assistant
 *
 * 本示例展示如何将 Crush AI Assistant 集成到 zhineng-bridge 系统
 * 使其能够向移动端发送问询，并接收用户的响应和指令
 */

const WebSocket = require('ws');

class CrushAIIntegrator {
    constructor(serverUrl, channel) {
        this.serverUrl = serverUrl || 'ws://localhost:8001';
        this.channel = channel || 'ai-assistant';
        this.ws = null;
        this.sessionId = null;
        this.isProcessing = false;
    }

    /**
     * 连接到 Relay Server
     */
    connect() {
        // console.log(`正在连接到 ${this.serverUrl}...`);

        this.ws = new WebSocket(this.serverUrl);

        this.ws.on('open', () => {
            // console.log('✅ 已连接到 Relay Server');
            this.joinChannel();
        });

        this.ws.on('message', (data) => {
            this.handleMessage(JSON.parse(data.toString()));
        });

        this.ws.on('error', (error) => {
            // console.error('❌ 连接错误:', error.message);
        });

        this.ws.on('close', () => {
            // console.log('🔌 已断开连接');
        });
    }

    /**
     * 加入频道
     */
    joinChannel() {
        this.send({
            type: 'join',
            channel: this.channel
        });
        // console.log(`📢 已加入频道: ${this.channel}`);
    }

    /**
     * 发送消息到 Relay Server
     */
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    /**
     * 处理从 Relay Server 接收到的消息
     */
    handleMessage(message) {
        // console.log('📨 收到消息:', message.type);

        switch (message.type) {
            case 'joined':
                // console.log(`✅ 成功加入频道: ${message.channel}`);
                break;

            case 'message':
                this.handleUserResponse(message);
                break;

            case 'command':
                this.handleUserCommand(message);
                break;

            case 'client_joined':
                // console.log(`👤 新客户端加入: ${message.clientId.substring(0, 8)}`);
                break;

            default:
                // console.log('未知消息类型:', message.type);
        }
    }

    /**
     * 处理用户响应
     */
    handleUserResponse(message) {
        const { payload } = message;

        if (payload.responseType === 'option') {
            // console.log(`✅ 用户选择了选项 [${payload.selectedOption}]: ${payload.content}`);
            this.processUserOption(payload.content);
        } else {
            // console.log(`✅ 用户输入: ${payload.content}`);
            this.processUserInput(payload.content);
        }
    }

    /**
     * 处理用户指令
     */
    handleUserCommand(message) {
        const { payload } = message;
        const command = payload.command;

        // console.log(`🎯 用户指令: ${command}`);

        switch (command) {
            case 'continue':
                this.continueProcessing();
                break;
            case 'pause':
                this.pauseProcessing();
                break;
            case 'stop':
                this.stopProcessing();
                break;
            case 'retry':
                this.retryOperation();
                break;
            case 'confirm':
                this.confirmAction();
                break;
            case 'cancel':
                this.cancelAction();
                break;
            case 'details':
                this.showDetails();
                break;
            case 'help':
                this.showHelp();
                break;
            default:
                // console.log(`未知指令: ${command}`);
        }
    }

    /**
     * 发送问询到移动端
     */
    askQuestion(question, options = [], context = {}) {
        const message = {
            type: 'command',
            channel: this.channel,
            payload: {
                question,
                options,
                context,
                sessionId: this.sessionId,
                timestamp: Date.now()
            }
        };

        this.send(message);
        // console.log(`❓ 发送问询: ${question}`);
        if (options.length > 0) {
            // console.log(`   选项: ${options.join(', ')}`);
        }
    }

    /**
     * 发送状态更新
     */
    sendStatus(status, progress = null) {
        const message = {
            type: 'message',
            channel: this.channel,
            payload: {
                from: 'ai',
                content: status,
                progress,
                sessionId: this.sessionId,
                timestamp: Date.now()
            }
        };

        this.send(message);
        // console.log(`📊 状态更新: ${status}${progress !=== null ? ` (${progress}%)` : ''}`);
    }

    // ============================================
    // Crush AI 特定功能示例
    // ============================================

    /**
     * 开始代码重构任务
     */
    startRefactoring(file, functionName) {
        this.sessionId = `refactor_${Date.now()}`;
        this.isProcessing = true;

        this.askQuestion(
            `是否开始重构 ${functionName} 函数？`,
            ['开始重构', '查看代码', '取消'],
            {
                function: functionName,
                file: file,
                operation: 'refactor'
            }
        );
    }

    /**
     * 处理用户选择的选项
     */
    processUserOption(option) {
        if (option === '开始重构') {
            this.sendStatus('开始重构...', 0);
            this.performRefactoring();
        } else if (option === '查看代码') {
            this.sendStatus('正在分析代码...', 0);
            this.showCodeAnalysis();
        } else if (option === '取消') {
            this.sendStatus('任务已取消');
            this.isProcessing = false;
        }
    }

    /**
     * 处理用户输入
     */
    processUserInput(input) {
        // console.log(`处理用户自定义输入: ${input}`);
        // 根据用户输入执行相应操作
    }

    /**
     * 执行重构操作（模拟）
     */
    async performRefactoring() {
        this.sendStatus('正在分析代码...', 10);
        await this.delay(1000);

        this.sendStatus('识别重构点...', 30);
        await this.delay(1000);

        this.askQuestion(
            '发现以下重构点：\n1. 函数过长，建议拆分\n2. 缺少错误处理\n\n是否继续？',
            ['全部重构', '选择性重构', '跳过'],
            { operation: 'refactor_points' }
        );

        await this.waitForResponse();

        this.sendStatus('正在重构...', 50);
        await this.delay(1000);

        this.sendStatus('重构完成', 100);
        this.isProcessing = false;
    }

    /**
     * 显示代码分析（模拟）
     */
    async showCodeAnalysis() {
        this.askQuestion(
            '代码分析结果：\n\n函数 userAuth 包含 45 行代码\n复杂度: 8\n建议: 拆分为 3 个子函数\n\n是否执行重构？',
            ['执行重构', '查看详情', '返回'],
            { operation: 'show_analysis' }
        );

        await this.waitForResponse();
    }

    // ============================================
    // 指令处理函数
    // ============================================

    continueProcessing() {
        if (!this.isProcessing) {
            this.sendStatus('没有正在进行的任务');
            return;
        }
        this.sendStatus('继续执行...');
        // 继续当前任务
    }

    pauseProcessing() {
        if (!this.isProcessing) {
            this.sendStatus('没有正在进行的任务');
            return;
        }
        this.sendStatus('任务已暂停');
        // 暂停当前任务
    }

    stopProcessing() {
        if (!this.isProcessing) {
            this.sendStatus('没有正在进行的任务');
            return;
        }
        this.sendStatus('任务已停止');
        this.isProcessing = false;
        // 停止当前任务
    }

    retryOperation() {
        this.sendStatus('正在重试...');
        // 重试上一个操作
    }

    confirmAction() {
        this.sendStatus('已确认');
        // 确认当前操作
    }

    cancelAction() {
        this.sendStatus('已取消');
        // 取消当前操作
    }

    showDetails() {
        this.sendStatus('详细信息：\n会话ID: ' + this.sessionId);
        // 显示详细信息
    }

    showHelp() {
        this.askQuestion(
            '可用指令：\n\n▶️ 继续 - 继续执行当前任务\n⏸️ 暂停 - 暂停当前任务\n⏹️ 停止 - 停止当前任务\n🔄 重试 - 重试上一个操作\n✅ 确认 - 确认当前操作\n❌ 取消 - 取消当前操作\nℹ️ 详情 - 查看详细信息\n❓ 帮助 - 显示此帮助信息',
            [],
            { operation: 'help' }
        );
    }

    // ============================================
    // 工具函数
    // ============================================

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    waitForResponse() {
        return new Promise(resolve => {
            // 这里应该等待用户响应
            // 实际实现需要更复杂的逻辑
            setTimeout(resolve, 1000);
        });
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// ============================================
// 使用示例
// ============================================

async function main() {
    const integrator = new CrushAIIntegrator(
        'ws://localhost:8001',
        'ai-assistant'
    );

    integrator.connect();

    // 等待连接建立
    await integrator.delay(2000);

    // 示例 1: 开始重构任务
    // console.log('\n=== 示例 1: 开始重构任务 ===');
    integrator.startRefactoring('src/auth.js', 'userAuth');

    // 示例 2: 发送状态更新
    await integrator.delay(3000);
    // console.log('\n=== 示例 2: 发送状态更新 ===');
    integrator.sendStatus('正在编译...', 75);

    // 示例 3: 询问用户
    await integrator.delay(2000);
    // console.log('\n=== 示例 3: 询问用户 ===');
    integrator.askQuestion(
        '是否要添加测试用例？',
        ['是', '否', '稍后'],
        {
            file: 'src/auth.js',
            function: 'userAuth',
            operation: 'add_tests'
        }
    );

    // 保持连接
    // console.log('\n✅ 集成器正在运行，按 Ctrl+C 退出\n');
}

// 如果直接运行此文件，执行示例
if (require.main === module) {
    main().catch(console.error);
}

module.exports = CrushAIIntegrator;
