/**
 * 智桥 - 性能优化模块
 */

class PerformanceOptimizer {
    constructor() {
        this.metrics = {
            pageLoadTime: 0,
            renderTime: 0,
            apiResponseTime: 0,
            memoryUsage: 0,
            fps: 0
        };
        this.observers = [];
    }

    /**
     * 初始化性能优化器
     */
    init() {
        console.log('⚡ 初始化性能优化器');
        
        // 监听页面加载时间
        this.trackPageLoadTime();
        
        // 监听渲染时间
        this.trackRenderTime();
        
        // 监听内存使用
        this.trackMemoryUsage();
        
        // 监听 FPS
        this.trackFPS();
        
        // 优化图片加载
        this.optimizeImageLoading();
        
        // 优化 CSS
        this.optimizeCSS();
        
        // 优化 JavaScript
        this.optimizeJavaScript();
        
        // 使用 Web Workers
        this.useWebWorkers();
        
        // 使用 Service Workers
        this.useServiceWorkers();
        
        console.log('✅ 性能优化器已初始化');
    }

    /**
     * 监听页面加载时间
     */
    trackPageLoadTime() {
        window.addEventListener('load', () => {
            const loadTime = window.performance.timing.loadEventEnd - 
                            window.performance.timing.navigationStart;
            this.metrics.pageLoadTime = loadTime;
            console.log(`⏱️  页面加载时间: ${loadTime}ms`);
        });
    }

    /**
     * 监听渲染时间
     */
    trackRenderTime() {
        window.addEventListener('DOMContentLoaded', () => {
            const renderTime = window.performance.timing.domComplete - 
                              window.performance.timing.domLoading;
            this.metrics.renderTime = renderTime;
            console.log(`⏱️  渲染时间: ${renderTime}ms`);
        });
    }

    /**
     * 监听内存使用
     */
    trackMemoryUsage() {
        if (performance.memory) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.entryType === 'measure') {
                        this.metrics.memoryUsage = performance.memory.usedJSHeapSize;
                        console.log(`💾 内存使用: ${(this.metrics.memoryUsage / 1024 / 1024).toFixed(2)}MB`);
                    }
                }
            });
            observer.observe({ entryTypes: ['measure'] });
            this.observers.push(observer);
        }
    }

    /**
     * 监听 FPS
     */
    trackFPS() {
        let lastTime = performance.now();
        let frames = 0;

        const updateFPS = () => {
            frames++;
            const currentTime = performance.now();
            const delta = currentTime - lastTime;

            if (delta >= 1000) {
                this.metrics.fps = frames;
                console.log(`🎬 FPS: ${frames}`);
                frames = 0;
                lastTime = currentTime;
            }

            requestAnimationFrame(updateFPS);
        };

        requestAnimationFrame(updateFPS);
    }

    /**
     * 优化图片加载
     */
    optimizeImageLoading() {
        console.log('🖼️  优化图片加载');
        
        // 懒加载图片
        const images = document.querySelectorAll('img[data-src]');
        images.forEach(img => {
            img.addEventListener('load', () => {
                img.classList.add('loaded');
            });
            img.src = img.dataset.src;
        });

        // 使用 WebP 格式
        if (this.supportsWebP()) {
            const webpImages = document.querySelectorAll('img[data-webp]');
            webpImages.forEach(img => {
                img.src = img.dataset.webp;
            });
        }
    }

    /**
     * 检查是否支持 WebP
     */
    supportsWebP() {
        return document.createElement('canvas').toDataURL('image/webp')
            .indexOf('data:image/webp') === 0;
    }

    /**
     * 优化 CSS
     */
    optimizeCSS() {
        console.log('🎨 优化 CSS');
        
        // 使用 CSS 变量
        document.documentElement.style.setProperty('--primary-color', '#667eea');
        document.documentElement.style.setProperty('--secondary-color', '#764ba2');
        
        // 使用 CSS 硬件加速
        const acceleratedElements = document.querySelectorAll('.accelerated');
        acceleratedElements.forEach(el => {
            el.style.transform = 'translateZ(0)';
            el.style.willChange = 'transform';
        });

        // 减少重绘和重排
        const elements = document.querySelectorAll('.no-reflow');
        elements.forEach(el => {
            el.style.position = 'absolute';
        });
    }

    /**
     * 优化 JavaScript
     */
    optimizeJavaScript() {
        console.log('⚡ 优化 JavaScript');
        
        // 防抖函数
        this.debounce = (func, wait) => {
            let timeout;
            return (...args) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        };

        // 节流函数
        this.throttle = (func, limit) => {
            let inThrottle;
            return (...args) => {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        };

        // 优化事件监听器
        const scrollElements = document.querySelectorAll('.scroll-optimized');
        scrollElements.forEach(el => {
            el.addEventListener('scroll', this.throttle((e) => {
                // 处理滚动事件
            }, 100));
        });

        // 优化输入事件
        const inputElements = document.querySelectorAll('.input-optimized');
        inputElements.forEach(el => {
            el.addEventListener('input', this.debounce((e) => {
                // 处理输入事件
            }, 300));
        });
    }

    /**
     * 使用 Web Workers
     */
    useWebWorkers() {
        console.log('👷 使用 Web Workers');
        
        // 创建 Web Worker
        if (window.Worker) {
            const worker = new Worker('/web/ui/js/worker.js');
            
            worker.onmessage = (event) => {
                console.log('📨 Worker 消息:', event.data);
            };

            // 发送任务给 Worker
            worker.postMessage({
                type: 'optimize',
                data: {}
            });
        }
    }

    /**
     * 使用 Service Workers
     */
    useServiceWorkers() {
        console.log('🔧 使用 Service Workers');
        
        // 注册 Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/web/ui/sw.js')
                .then(registration => {
                    console.log('✅ Service Worker 已注册:', registration);
                })
                .catch(error => {
                    console.error('❌ Service Worker 注册失败:', error);
                });
        }
    }

    /**
     * 获取性能指标
     */
    getMetrics() {
        return this.metrics;
    }

    /**
     * 生成性能报告
     */
    generateReport() {
        const report = {
            metrics: this.metrics,
            recommendations: []
        };

        // 生成建议
        if (this.metrics.pageLoadTime > 3000) {
            report.recommendations.push('页面加载时间过长，建议优化资源加载');
        }

        if (this.metrics.renderTime > 1000) {
            report.recommendations.push('渲染时间过长，建议优化 DOM 操作');
        }

        if (this.metrics.fps < 30) {
            report.recommendations.push('FPS 过低，建议优化动画和渲染');
        }

        if (this.metrics.memoryUsage > 100 * 1024 * 1024) {
            report.recommendations.push('内存使用过高，建议优化内存管理');
        }

        return report;
    }
}

// 导出性能优化器
window.PerformanceOptimizer = PerformanceOptimizer;
