/**
 * 增强型性能监控仪表板
 * Version: 2.0.0
 */

class EnhancedPerformanceDashboard {
    constructor() {
        this.metrics = {};
        this.history = [];
        this.alerts = [];
        this.charts = {};
        this.updateInterval = 5000; // 5 秒
        this.initialized = false;
        this.maxHistoryLength = 100; // 保留最近 100 个数据点
    }

    /**
     * 初始化仪表板
     */
    async init() {
        if (this.initialized) {
            console.warn('⚠️  仪表板已初始化');
            return;
        }

        console.log('📊 初始化增强型性能监控仪表板');

        try {
            // 加载指标
            await this.loadMetrics();

            // 初始化图表
            this.initializeCharts();

            // 渲染指标
            this.renderMetrics();

            // 渲染历史图表
            this.renderHistoryCharts();

            // 加载告警
            this.loadAlerts();

            // 加载系统状态
            this.loadSystemStatus();

            // 启动自动更新
            this.startAutoUpdate();

            // 监听窗口大小变化
            this.setupEventListeners();

            this.initialized = true;
            console.log('✅ 性能监控仪表板已初始化');
        } catch (error) {
            console.error('❌ 初始化失败:', error);
        }
    }

    /**
     * 加载指标
     */
    async loadMetrics() {
        console.log('📊 加载性能指标');

        try {
            const response = await fetch('/api/metrics');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            this.metrics = {
                // 时间指标
                sessionCreationTime: data.sessionCreationTime || 75,
                webSocketConnectionTime: data.webSocketConnectionTime || 35,
                pageLoadTime: data.pageLoadTime || 1.5,
                responseTime: data.responseTime || 150,

                // 资源指标
                memoryUsage: data.memoryUsage || 65,
                cpuUsage: data.cpuUsage || 25,
                diskUsage: data.diskUsage || 40,

                // 会话指标
                activeSessions: data.activeSessions || 12,
                totalSessions: data.totalSessions || 1250,
                sessionsPerMinute: data.sessionsPerMinute || 8.5,

                // 网络指标
                requestSuccessRate: data.requestSuccessRate || 99.5,
                requestsPerSecond: data.requestsPerSecond || 45,
                bandwidthUsage: data.bandwidthUsage || 1.2,

                // 错误指标
                errorRate: data.errorRate || 0.5,
                warningCount: data.warningCount || 3,
                criticalErrors: data.criticalErrors || 0
            };

            // 添加到历史记录
            this.addToHistory(this.metrics);

            console.log('✅ 性能指标已加载');
        } catch (error) {
            console.error('❌ 加载性能指标失败:', error);
            this.useMockData();
        }
    }

    /**
     * 使用模拟数据
     */
    useMockData() {
        console.log('📊 使用模拟数据');

        this.metrics = {
            sessionCreationTime: 75 + Math.random() * 25,
            webSocketConnectionTime: 35 + Math.random() * 15,
            pageLoadTime: 1.5 + Math.random() * 0.5,
            responseTime: 150 + Math.random() * 50,
            memoryUsage: 65 + Math.random() * 10,
            cpuUsage: 25 + Math.random() * 15,
            diskUsage: 40 + Math.random() * 5,
            activeSessions: 12 + Math.floor(Math.random() * 5),
            totalSessions: 1250 + Math.floor(Math.random() * 100),
            sessionsPerMinute: 8.5 + Math.random() * 2,
            requestSuccessRate: 99.5 - Math.random() * 0.5,
            requestsPerSecond: 45 + Math.random() * 10,
            bandwidthUsage: 1.2 + Math.random() * 0.3,
            errorRate: 0.5 + Math.random() * 0.5,
            warningCount: Math.floor(Math.random() * 5),
            criticalErrors: 0
        };

        this.addToHistory(this.metrics);
    }

    /**
     * 添加到历史记录
     */
    addToHistory(metrics) {
        const timestamp = new Date().toISOString();
        this.history.push({ ...metrics, timestamp });

        // 限制历史记录长度
        if (this.history.length > this.maxHistoryLength) {
            this.history.shift();
        }
    }

    /**
     * 初始化图表
     */
    initializeCharts() {
        console.log('📈 初始化图表');

        // 会话历史图表
        this.charts.sessionHistory = {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '活跃会话数',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true
                }]
            }
        };

        // 响应时间图表
        this.charts.responseTime = {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '响应时间 (ms)',
                    data: [],
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    fill: true
                }]
            }
        };

        // 内存使用图表
        this.charts.memoryUsage = {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '内存使用率 (%)',
                    data: [],
                    borderColor: '#48bb78',
                    backgroundColor: 'rgba(72, 187, 120, 0.1)',
                    fill: true
                }]
            }
        };

        console.log('✅ 图表已初始化');
    }

    /**
     * 渲染指标
     */
    renderMetrics() {
        console.log('🎨 渲染性能指标');

        const metricIds = [
            'sessionCreationTime',
            'webSocketConnectionTime',
            'pageLoadTime',
            'responseTime',
            'memoryUsage',
            'cpuUsage',
            'diskUsage',
            'activeSessions',
            'totalSessions',
            'sessionsPerMinute',
            'requestSuccessRate',
            'requestsPerSecond',
            'bandwidthUsage',
            'errorRate',
            'warningCount',
            'criticalErrors'
        ];

        metricIds.forEach(id => {
            const element = document.getElementById(id);
            if (element && this.metrics[id] !== undefined) {
                const value = this.metrics[id];
                const formattedValue = this.formatMetricValue(id, value);

                // 如果是趋势指示器
                const trendElement = document.getElementById(`${id}Trend`);
                if (trendElement) {
                    const trend = this.calculateTrend(id);
                    trendElement.innerHTML = this.getTrendIcon(trend);
                    trendElement.className = `metric-trend ${trend > 0 ? 'positive' : trend < 0 ? 'negative' : 'neutral'}`;
                }

                // 更新数值
                element.textContent = formattedValue;

                // 更新颜色（基于阈值）
                this.updateMetricColor(element, id, value);
            }
        });

        console.log('✅ 性能指标已渲染');
    }

    /**
     * 格式化指标值
     */
    formatMetricValue(id, value) {
        if (id.includes('Time') && !id.includes('Load')) {
            return `${value.toFixed(1)}ms`;
        }
        if (id.includes('Rate') || id.includes('Usage')) {
            return `${value.toFixed(1)}%`;
        }
        if (id === 'pageLoadTime') {
            return `${value.toFixed(2)}s`;
        }
        if (id === 'bandwidthUsage') {
            return `${value.toFixed(2)}MB/s`;
        }
        if (id === 'sessionsPerMinute') {
            return value.toFixed(1);
        }
        if (id === 'requestsPerSecond') {
            return value.toFixed(0);
        }
        if (Number.isInteger(value)) {
            return value.toString();
        }
        return value.toFixed(2);
    }

    /**
     * 计算趋势
     */
    calculateTrend(id) {
        if (this.history.length < 2) return 0;

        const current = this.metrics[id];
        const previous = this.history[this.history.length - 2][id];

        if (previous === undefined || previous === 0) return 0;

        const change = ((current - previous) / previous) * 100;
        return change;
    }

    /**
     * 获取趋势图标
     */
    getTrendIcon(trend) {
        if (trend > 5) return '📈';
        if (trend < -5) return '📉';
        return '➡️';
    }

    /**
     * 更新指标颜色
     */
    updateMetricColor(element, id, value) {
        // 移除旧的颜色类
        element.classList.remove('good', 'warning', 'danger');

        // 根据阈值添加新颜色
        const threshold = this.getThreshold(id);
        if (threshold) {
            if (value >= threshold.danger) {
                element.classList.add('danger');
            } else if (value >= threshold.warning) {
                element.classList.add('warning');
            } else {
                element.classList.add('good');
            }
        }
    }

    /**
     * 获取指标阈值
     */
    getThreshold(id) {
        const thresholds = {
            sessionCreationTime: { warning: 100, danger: 150 },
            webSocketConnectionTime: { warning: 50, danger: 100 },
            pageLoadTime: { warning: 2, danger: 3 },
            responseTime: { warning: 200, danger: 500 },
            memoryUsage: { warning: 80, danger: 90 },
            cpuUsage: { warning: 70, danger: 90 },
            diskUsage: { warning: 80, danger: 90 },
            requestSuccessRate: { warning: 99, danger: 98 },
            errorRate: { warning: 1, danger: 5 }
        };

        return thresholds[id];
    }

    /**
     * 渲染历史图表
     */
    renderHistoryCharts() {
        console.log('📈 渲染历史图表');

        // 准备数据
        const labels = this.history.map((_, i) => i);
        const activeSessions = this.history.map(h => h.activeSessions);
        const responseTime = this.history.map(h => h.responseTime);
        const memoryUsage = this.history.map(h => h.memoryUsage);

        // 更新图表数据
        if (this.charts.sessionHistory) {
            this.charts.sessionHistory.data.labels = labels;
            this.charts.sessionHistory.data.datasets[0].data = activeSessions;
        }

        if (this.charts.responseTime) {
            this.charts.responseTime.data.labels = labels;
            this.charts.responseTime.data.datasets[0].data = responseTime;
        }

        if (this.charts.memoryUsage) {
            this.charts.memoryUsage.data.labels = labels;
            this.charts.memoryUsage.data.datasets[0].data = memoryUsage;
        }

        // 这里可以集成实际的图表库（如 Chart.js）
        console.log('✅ 历史图表已渲染');
    }

    /**
     * 加载告警
     */
    loadAlerts() {
        console.log('🚨 加载告警');

        // 模拟告警
        this.alerts = [
            {
                level: 'warning',
                message: '内存使用率接近阈值',
                time: new Date(Date.now() - 300000)
            },
            {
                level: 'info',
                message: '系统运行正常',
                time: new Date(Date.now() - 600000)
            }
        ];

        this.renderAlerts();
    }

    /**
     * 渲染告警
     */
    renderAlerts() {
        const alertsContainer = document.getElementById('alerts');
        if (!alertsContainer) return;

        alertsContainer.innerHTML = '';

        this.alerts.forEach(alert => {
            const alertElement = document.createElement('div');
            alertElement.className = `alert alert-${alert.level}`;
            alertElement.innerHTML = `
                <span class="alert-icon">${this.getAlertIcon(alert.level)}</span>
                <span class="alert-message">${alert.message}</span>
                <span class="alert-time">${this.formatTime(alert.time)}</span>
            `;
            alertsContainer.appendChild(alertElement);
        });
    }

    /**
     * 获取告警图标
     */
    getAlertIcon(level) {
        const icons = {
            danger: '🔴',
            warning: '🟡',
            info: '🔵',
            success: '🟢'
        };
        return icons[level] || '⚪';
    }

    /**
     * 格式化时间
     */
    formatTime(date) {
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return '刚刚';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
        return date.toLocaleDateString();
    }

    /**
     * 加载系统状态
     */
    loadSystemStatus() {
        console.log('🖥️  加载系统状态');

        const statusElement = document.getElementById('systemStatus');
        if (statusElement) {
            // 检查是否有严重问题
            const hasCriticalErrors = this.metrics.criticalErrors > 0;
            const highErrorRate = this.metrics.errorRate > 5;
            const highMemoryUsage = this.metrics.memoryUsage > 90;

            if (hasCriticalErrors || highErrorRate || highMemoryUsage) {
                statusElement.innerHTML = '<span class="status-dot danger"></span>系统异常';
                statusElement.className = 'status status-danger';
            } else {
                statusElement.innerHTML = '<span class="status-dot"></span>运行正常';
                statusElement.className = 'status status-normal';
            }
        }
    }

    /**
     * 启动自动更新
     */
    startAutoUpdate() {
        console.log('🔄 启动自动更新');

        setInterval(async () => {
            try {
                await this.loadMetrics();
                this.renderMetrics();
                this.renderHistoryCharts();
                this.loadSystemStatus();
            } catch (error) {
                console.error('❌ 自动更新失败:', error);
            }
        }, this.updateInterval);
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        window.addEventListener('resize', () => {
            // 重新渲染图表以适应新尺寸
            this.renderHistoryCharts();
        });
    }

    /**
     * 导出报告
     */
    exportReport() {
        const report = {
            timestamp: new Date().toISOString(),
            metrics: this.metrics,
            history: this.history,
            alerts: this.alerts
        };

        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `performance-report-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * 清除历史数据
     */
    clearHistory() {
        this.history = [];
        this.charts = {};
        this.initializeCharts();
        this.renderHistoryCharts();
        console.log('✅ 历史数据已清除');
    }
}

// 导出到全局
window.EnhancedPerformanceDashboard = EnhancedPerformanceDashboard;

// 自动初始化
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new EnhancedPerformanceDashboard();
    window.dashboard.init();
});
