/**
 * 智桥 - Service Worker
 */

const CACHE_NAME = 'zhineng-bridge-v1';
const urlsToCache = [
    '/',
    '/web/ui/index.html',
    '/web/ui/css/base.css',
    '/web/ui/css/layout.css',
    '/web/ui/css/components.css',
    '/web/ui/css/responsive.css',
    '/web/ui/css/mobile.css',
    '/web/ui/js/app.js',
    '/web/ui/js/tools.js',
    '/web/ui/js/sessions.js',
    '/web/ui/js/settings.js',
    '/web/ui/js/client.js'
];

self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker 安装');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('✅ 已打开缓存');
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // 缓存命中，返回缓存的响应
                if (response) {
                    return response;
                }
                
                // 缓存未命中，发送网络请求
                return fetch(event.request).then(
                    (response) => {
                        // 检查是否是有效的响应
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // 克隆响应
                        const responseToCache = response.clone();
                        
                        // 添加到缓存
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });
                        
                        return response;
                    }
                );
            })
    );
});

self.addEventListener('activate', (event) => {
    console.log('🔧 Service Worker 激活');
    
    const cacheWhitelist = [CACHE_NAME];
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        console.log('🗑️  删除缓存:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
