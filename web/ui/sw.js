/**
 * 智桥 Service Worker
 * 处理 PWA 离线缓存和推送通知
 */

const CACHE_NAME = 'zhineng-bridge-v1.0.0';
const RUNTIME_CACHE = 'zhineng-bridge-runtime-v1.0.0';

// 需要缓存的静态资源
const STATIC_CACHE_URLS = [
    '/web/ui/index.html',
    '/web/ui/css/base.css',
    '/web/ui/css/components.css',
    '/web/ui/css/layout.css',
    '/web/ui/css/responsive.css',
    '/web/ui/css/mobile.css',
    '/web/ui/css/improvements.css',
    '/web/ui/js/app.js',
    '/web/ui/js/client.js',
    '/web/ui/js/tools.js',
    '/web/ui/js/sessions.js',
    '/web/ui/js/settings.js',
    '/web/ui/js/slash-commands.js',
    '/web/ui/js/push.js',
    '/web/ui/js/file-mentions.js',
    '/web/ui/js/improvements.js',
    '/web/ui/manifest.json',
    '/web/ui/icons/icon-192x192.png',
    '/web/ui/icons/icon-512x512.png'
];

/**
 * 安装 Service Worker
 */
self.addEventListener('install', (event) => {
    console.log('✅ Service Worker 安装中...');

    // 预缓存静态资源
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('📦 预缓存静态资源');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                console.log('✅ 静态资源缓存完成');
                // 强制激活新的 Service Worker
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('❌ 缓存失败:', error);
            })
    );
});

/**
 * 激活 Service Worker
 */
self.addEventListener('activate', (event) => {
    console.log('✅ Service Worker 激活中...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        // 删除旧版本的缓存
                        if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
                            console.log('🗑️  删除旧缓存:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ Service Worker 已激活');
                // 控制所有客户端
                return self.clients.claim();
            })
    );
});

/**
 * 处理 fetch 请求
 */
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // 只处理同源请求
    if (url.origin !== self.location.origin) {
        return;
    }

    // 处理 API 请求（网络优先）
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    // 成功时缓存响应
                    if (response.ok) {
                        const responseClone = response.clone();
                        caches.open(RUNTIME_CACHE).then((cache) => {
                            cache.put(event.request, responseClone);
                        });
                    }
                    return response;
                })
                .catch((error) => {
                    console.log('❌ API 请求失败，尝试从缓存读取:', error);
                    // 网络失败时尝试从缓存读取
                    return caches.match(event.request).then((cachedResponse) => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        throw error;
                    });
                })
        );
        return;
    }

    // 处理静态资源（缓存优先）
    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    // 命中缓存
                    console.log('✅ 缓存命中:', event.request.url);
                    return cachedResponse;
                }

                // 未命中缓存，从网络获取
                return fetch(event.request)
                    .then((response) => {
                        // 检查是否是有效响应
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // 克隆响应并缓存
                        const responseToCache = response.clone();
                        caches.open(RUNTIME_CACHE).then((cache) => {
                            cache.put(event.request, responseToCache);
                        });

                        return response;
                    })
                    .catch((error) => {
                        console.error('❌ 请求失败:', error);
                        throw error;
                    });
            })
    );
});

/**
 * 处理推送通知
 */
self.addEventListener('push', (event) => {
    console.log('📨 收到推送通知');

    if (!event.data) {
        console.log('❌ 推送通知没有数据');
        return;
    }

    try {
        const data = event.data.json();

        const options = {
            body: data.body || '',
            icon: data.icon || '/web/ui/icons/icon-192x192.png',
            badge: data.badge || '/web/ui/icons/icon-72x72.png',
            vibrate: [200, 100, 200],
            data: data.data || {},
            actions: data.actions || [],
            tag: data.tag || 'default-notification',
            requireInteraction: data.requireInteraction || false
        };

        // 显示通知
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );

        console.log('✅ 推送通知已显示');
    } catch (error) {
        console.error('❌ 处理推送通知失败:', error);

        // 如果 JSON 解析失败，尝试显示原始文本
        event.waitUntil(
            self.registration.showNotification('智桥通知', {
                body: event.data.text(),
                icon: '/web/ui/icons/icon-192x192.png'
            })
        );
    }
});

/**
 * 处理通知点击
 */
self.addEventListener('notificationclick', (event) => {
    console.log('👆 通知被点击');

    event.notification.close();

    // 获取通知数据
    const data = event.notification.data || {};

    // 确定要打开的 URL
    let url = '/web/ui/index.html';

    if (data.type === 'session_state') {
        url = `/web/ui/index.html#sessions?session_id=${data.session_id}`;
    } else if (data.type === 'task_completion') {
        url = `/web/ui/index.html#sessions?task_id=${data.task_id}`;
    } else if (data.url) {
        url = data.url;
    }

    // 打开或聚焦到应用
    event.waitUntil(
        self.clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        })
        .then((clientList) => {
            // 查找已打开的窗口
            for (const client of clientList) {
                if (client.url.includes(url) || 'focus' in client) {
                    return client.focus();
                }
            }

            // 如果没有找到，打开新窗口
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});

/**
 * 处理通知关闭
 */
self.addEventListener('notificationclose', (event) => {
    console.log('❌ 通知被关闭');

    // 可以在这里记录用户关闭通知的统计信息
    const data = event.notification.data || {};
    console.log('关闭的通知数据:', data);
});

/**
 * 处理消息（从主线程接收消息）
 */
self.addEventListener('message', (event) => {
    console.log('📩 收到主线程消息:', event.data);

    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        console.log('🗑️  清除缓存:', cacheName);
                        return caches.delete(cacheName);
                    })
                );
            })
        );
    }
});

/**
 * 处理后台同步（可选功能）
 */
self.addEventListener('sync', (event) => {
    console.log('🔄 后台同步:', event.tag);

    if (event.tag === 'sync-data') {
        event.waitUntil(
            // 这里可以实现后台数据同步逻辑
            Promise.resolve()
        );
    }
});

console.log('🚀 智桥 Service Worker 已加载');
