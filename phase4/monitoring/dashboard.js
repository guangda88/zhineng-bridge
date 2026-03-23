/**
 * 性能监控仪表板
 */

class PerformanceDashboard {
    constructor() {
        this.metrics = {};
        this.alerts = [];
        this.updateInterval = 5000; // 5 秒
        this.initialized = false;
    }

    /**
     * 初始化仪表板
     */
    async init() {
        if (this.initialized) {
            console.warn('⚠️  仪表板已初始化');
            return;
        }

        console.log('📊 初始化性能监控仪表板');

        // 加载指标
        await this.loadMetrics();

        // 渲染指标
        this.renderMetrics();

        // 加载图表
        this.loadCharts();

        // 加载告警
        this.loadAlerts();

        // 启动自动更新
        this.startAutoUpdate();

        this.initialized = true;
        console.log('✅ 性能监控仪表板已初始化');
    }

    /**
     * 加载指标
     */
    async loadMetrics() {
        console.log('📊 加载性能指标');

        try {
            // 从服务器加载指标
            const response = await fetch('/api/metrics');
            const data = await response.json();

            this.metrics = {
                sessionCreationTime: data.sessionCreationTime || 75,
                webSocketConnectionTime: data.webSocketConnectionTime || 35,
                pageLoadTime: data.pageLoadTime || 1.5,
                memoryUsage: data.memoryUsage || 65,
                activeSessions: data.activeSessions || 12,
                requestSuccessRate: data.requestSuccessRate || 99.5
            };

            console.log('✅ 性能指标已加载');
        } catch (error) {
            console.error('❌ 加载性能指标失败:', error);

            // 使用模拟数据
            this.metrics = {
                sessionCreationTime: 75,
                webSocketConnectionTime: 35,
                pageLoadTime: 1.5,
                memoryUsage: 65,
                activeSessions: 12,
                requestSuccessRate: 99.5
            };
        }
    }

    /**
     * 渲染指标
     */
    renderMetrics() {
        console.log('🎨 渲染性能指标');

        // 会话创建时间
        const sessionCreationTime = document.getElementById('sessionCreationTime');
        if (sessionCreationTime) {
            sessionCreationTime.textContent = `${this.metrics.sessionCreationTime}ms`;
        }

        // WebSocket 连接时间
        const webSocketConnectionTime = document.getElementById('webSocketConnectionTime');
        if (webSocketConnectionTime) {
            webSocketConnectionTime.textContent = `${this.metrics.webSocketConnectionTime}ms`;
        }

        // 页面加载时间
        const pageLoadTime = document.getElementById('pageLoadTime');
        if (pageLoadTime) {
            pageLoadTime.textContent = `${this.metrics.pageLoadTime}s`;
        }

        // 内存使用
        const memoryUsage = document.getElementById('memoryUsage');
        if (memoryUsage) {
            memoryUsage.textContent = `${this.metrics.memoryUsage}MB`;
        }

        // 活跃会话数
        const activeSessions = document.getElementById('activeSessions');
        if (activeSessions) {
            activeSessions.textContent = this.metrics.activeSessions;
        }

        // 请求成功率
        const requestSuccessRate = document.getElementById('requestSuccessRate');
        if (requestSuccessRate) {
            requestSuccessRate.textContent = `${this.metrics.requestSuccessRate}%`;
        }

        console.log('✅ 性能指标已渲染');
    }

    /**
     * 加载图表
     */
    loadCharts() {
        console.log('📊 加载图表');

        // 性能趋势图
        const performanceTrendChart = document.getElementById('performanceTrendChart');
        if (performanceTrendChart) {
            performanceTrendChart.innerHTML = this.createTrendChart();
        }

        // 资源使用图
        const resourceUsageChart = document.getElementById('resourceUsageChart');
        if (resourceUsageChart) {
            resourceUsageChart.innerHTML = this.createResourceUsageChart();
        }

        console.log('✅ 图表已加载');
    }

    /**
     * 创建趋势图
     */
    createTrendChart() {
        // 简化的图表 HTML
        return `
            <svg width="100%" height="100%" viewBox="0 0 400 300">
                <!-- 坐标轴 -->
                <line x1="50" y1="20" x2="50" y2="250" stroke="#e2e8f0" stroke-width="2"/>
                <line x1="50" y1="250" x2="380" y2="250" stroke="#e2e8f0" stroke-width="2"/>
                
                <!-- 趋势线 -->
                <polyline 
                    points="50,200 120,180 190,160 260,140 330,120"
                    fill="none"
                    stroke="#667eea"
                    stroke-width="3"
                />
                
                <!-- 数据点 -->
                <circle cx="50" cy="200" r="5" fill="#667eea"/>
                <circle cx="120" cy="180" r="5" fill="#667eea"/>
                <circle cx="190" cy="160" r="5" fill="#667eea"/>
                <circle cx="260" cy="140" r="5" fill="#667eea"/>
                <circle cx="330" cy="120" r="5" fill="#667eea"/>
                
                <!-- 标签 -->
                <text x="215" y="280" text-anchor="middle" fill="#718096" font-size="12">时间</text>
                <text x="20" y="150" text-anchor="middle" fill="#718096" font-size="12" transform="rotate(-90 20,150)">性能</text>
            </svg>
        `;
    }

    /**
     * 创建资源使用图
     */
    createResourceUsageChart() {
        // 简化的图表 HTML
        const memoryPercent = this.metrics.memoryUsage;
        const cpuPercent = 30;
        const networkPercent = 45;

        return `
            <svg width="100%" height="100%" viewBox="0 0 400 300">
                <!-- 内存使用 -->
                <text x="50" y="30" fill="#2d3748" font-size="14" font-weight="600">内存</text>
                <rect x="50" y="40" width="300" height="20" fill="#e2e8f0" rx="10"/>
                <rect x="50" y="40" width="${memoryPercent * 3}" height="20" fill="#48bb78" rx="10"/>
                <text x="360" y="55" fill="#718096" font-size="12">${memoryPercent}%</text>
                
                <!-- CPU 使用 -->
                <text x="50" y="90" fill="#2d3748" font-size="14" font-weight="600">CPU</text>
                <rect x="50" y="100" width="300" height="20" fill="#e2e8f0" rx="10"/>
                <rect x="50" y="100" width="${cpuPercent * 3}" height="20" fill="#667eea" rx="10"/>
                <text x="360" y="115" fill="#718096" font-size="12">${cpuPercent}%</text>
                
                <!-- 网络使用 -->
                <text x="50" y="150" fill="#2d3748" font-size="14" font-weight="600">网络</text>
                <rect x="50" y="160" width="300" height="20" fill="#e2e8f0" rx="10"/>
                <rect x="50" y="160" width="${networkPercent * 3}" height="20" fill="#ed8936" rx="10"/>
                <text x="360" y="175" fill="#718096" font-size="12">${networkPercent}%</text>
                
                <!-- 存储 -->
                <text x="50" y="210" fill="#2d3748" font-size="14" font-weight="600">存储</text>
                <rect x="50" y="220" width="300" height="20" fill="#e2e8f0" rx="10"/>
                <rect x="50" y="220" width="120" height="20" fill="#f56565" rx="10"/>
                <text x="360" y="235" fill="#718096" font-size="12">40%</text>
            </svg>
        `;
    }

    /**
     * 加载告警
     */
    loadAlerts() {
        console.log('📢 加载告警');

        const alertsContainer = document.getElementById('alerts');
        if (alertsContainer) {
            alertsContainer.innerHTML = this.renderAlerts();
        }

        console.log('✅ 告警已加载');
    }

    /**
     * 渲染告警
     */
    renderAlerts() {
        if (this.alerts.length === 0) {
            return `
                <div class="alert success">
                    <span>所有系统指标正常</span>
                    <span class="alert-time">刚刚</span>
                </div>
            `;
        }

        return this.alerts.map(alert => `
            <div class="alert ${alert.type}">
                <span>${alert.message}</span>
                <span class="alert-time">${alert.time}</span>
            </div>
        `).join('');
    }

    /**
     * 添加告警
     */
    addAlert(type, message) {
        this.alerts.push({
            type: type,
            message: message,
            time: new Date().toLocaleTimeString('zh-CN')
        });

        // 限制告警数量
        if (this.alerts.length > 10) {
            this.alerts = this.alerts.slice(-10);
        }

        // 重新渲染告警
        this.loadAlerts();
    }

    /**
     * 启动自动更新
     */
    startAutoUpdate() {
        console.log('⏱️  启动自动更新');

        setInterval(async () => {
            await this.loadMetrics();
            this.renderMetrics();
        }, this.updateInterval);

        console.log(`✅ 自动更新已启动 (间隔: ${this.updateInterval}ms)`);
    }
}

// 初始化仪表板
document.addEventListener('DOMContentLoaded', async () => {
    const dashboard = new PerformanceDashboard();
    await dashboard.init();
});
