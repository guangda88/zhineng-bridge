/**
 * Web Push Notification Manager for 智桥
 * 实现推送通知功能
 */

class PushNotificationManager {
    constructor() {
        this.subscription = null;
        this.registration = null;
        this.isSupported = this.checkSupport();
    }

    /**
     * 检查浏览器是否支持推送通知
     */
    checkSupport() {
        return 'serviceWorker' in navigator &&
               'PushManager' in window &&
               'Notification' in window;
    }

    /**
     * 请求通知权限
     */
    async requestPermission() {
        if (!this.isSupported) {
            console.error('❌ 当前浏览器不支持推送通知');
            return false;
        }

        const permission = await Notification.requestPermission();
        console.log(`📋 通知权限: ${permission}`);

        return permission === 'granted';
    }

    /**
     * 初始化推送通知
     */
    async init() {
        if (!this.isSupported) {
            console.error('❌ 当前浏览器不支持推送通知');
            return false;
        }

        try {
            // 获取 Service Worker 注册
            this.registration = await navigator.serviceWorker.getRegistration();

            if (!this.subscription) {
                // 订阅推送服务
                this.subscription = await this.registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.urlBase64ToUint8Array(
                        'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEcPnq4OWfR7_o7sLAReiWbrO8pb3SvFjRKGs7OxZ_SeL2epzDVxvgi7sQBnghTzGYyV9fFo1VfzggHCc2u71xhg'
                    )
                });

                console.log('✅ 推送订阅成功:', this.subscription);

                // 将订阅信息发送到服务器
                await this.sendSubscriptionToServer(this.subscription);
            }

            return true;
        } catch (error) {
            console.error('❌ 推送初始化失败:', error);
            return false;
        }
    }

    /**
     * 发送订阅信息到服务器
     */
    async sendSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/notifications/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON(),
                    user_id: window.USER_ID || 'anonymous'
                })
            });

            if (!response.ok) {
                throw new Error('订阅发送失败');
            }

            console.log('✅ 订阅信息已发送到服务器');
        } catch (error) {
            console.error('❌ 发送订阅信息失败:', error);
        }
    }

    /**
     * 显示本地通知
     */
    showLocalNotification(title, options = {}) {
        if (!this.isSupported || Notification.permission !== 'granted') {
            console.warn('⚠️  没有通知权限');
            return;
        }

        const notification = new Notification(title, {
            icon: '/web/ui/icons/icon-192x192.png',
            badge: '/web/ui/icons/icon-72x72.png',
            vibrate: [200, 100, 200],
            ...options
        });

        notification.onclick = (event) => {
            event.preventDefault();
            window.focus();
            notification.close();

            // 如果有 URL，导航到对应页面
            if (options.url) {
                window.location.href = options.url;
            }
        };
    }

    /**
     * 会话状态变化通知
     */
    notifySessionChange(sessionId, status, toolName) {
        const titles = {
            'started': '🚀 会话已启动',
            'stopped': '⏹️ 会话已停止',
            'completed': '✅ 任务已完成',
            'error': '❌ 会话出错',
            'input_needed': '💬 需要您的输入'
        };

        const titles_zh = {
            'started': '🚀 会话已启动',
            'stopped': '⏹️ 会话已停止',
            'completed': '✅ 任务已完成',
            'error': '❌ 会话出错',
            'input_needed': '💬 需要您的输入'
        };

        this.showLocalNotification(titles[status] || titles_zh[status] || '会话状态更新', {
            body: `${toolName} 会话 ${sessionId}`,
            tag: `session-${sessionId}`,
            url: `/web/ui/index.html#sessions`
        });
    }

    /**
     * 任务完成通知
     */
    notifyTaskComplete(taskName, result) {
        this.showLocalNotification('✅ 任务完成', {
            body: `${taskName} 执行完成`,
            tag: `task-${taskName}`,
            url: `/web/ui/index.html#sessions`
        });
    }

    /**
     * 错误通知
     */
    notifyError(errorType, errorMessage) {
        this.showLocalNotification('❌ 发生错误', {
            body: `${errorType}: ${errorMessage}`,
            tag: `error-${errorType}`,
            requireInteraction: true
        });
    }

    /**
     * 测试通知
     */
    testNotification() {
        if (Notification.permission === 'granted') {
            this.showLocalNotification('🔔 测试通知', {
                body: '智桥推送通知功能正常工作！',
                icon: '/web/ui/icons/icon-192x192.png'
            });
        } else {
            this.requestPermission().then(granted => {
                if (granted) {
                    this.testNotification();
                } else {
                    alert('请允许智桥显示通知');
                }
            });
        }
    }

    /**
     * VAPID 公钥转换工具
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; i++) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        return outputArray;
    }
}

// 导出为全局变量
window.PushNotificationManager = PushNotificationManager;

// 自动初始化
if (typeof window !== 'undefined') {
    window.pushManager = new PushNotificationManager();
}
