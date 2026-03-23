/**
 * 网络优化器
 */

class NetworkOptimizer {
  constructor() {
    this.metrics = {
      'requestCount': 0,
      'responseTime': 0,
      'errorCount': 0,
      'cacheHits': 0,
      'cacheMisses': 0
    };
    this.requestCache = new Map();
    this.requestQueue = [];
    this.maxConcurrentRequests = 5;
    this.concurrencySemaphore = {
      value: 5
    };
    this.initialized = false;
  }

  /**
   * 初始化网络优化器
   */
  async init() {
    if (this.initialized) {
      console.warn('⚠️  网络优化器已初始化');
      return;
    }

    console.log('🌐 初始化网络优化器');

    // 初始化 Service Worker
    await this.initServiceWorker();

    // 初始化缓存
    await this.initCache();

    this.initialized = true;
    console.log('✅ 网络优化器已初始化');
  }

  /**
   * 初始化 Service Worker
   */
  async initServiceWorker() {
    console.log('🔧 初始化 Service Worker');

    if ('serviceWorker' in navigator) {
      try {
        await navigator.serviceWorker.register('/web/ui/sw.js');
        console.log('✅ Service Worker 已注册');
      } catch (error) {
        console.error('❌ Service Worker 注册失败:', error);
      }
    }
  }

  /**
   * 初始化缓存
   */
  async initCache() {
    console.log('💾 初始化缓存');

    if ('caches' in window) {
      try {
        this.cache = await caches.open('zhineng-bridge-network-v1');
        console.log('✅ 缓存已打开');
      } catch (error) {
        console.error('❌ 打开缓存失败:', error);
      }
    }
  }

  /**
   * 发送请求（优化版）
   */
  async fetch(url, options = {}, useCache = true) {
    const cacheKey = this.getCacheKey(url, options);

    // 检查缓存
    if (useCache && this.requestCache.has(cacheKey)) {
      console.log('💾 缓存命中:', cacheKey);
      this.metrics['cacheHits']++;
      return this.requestCache.get(cacheKey);
    }

    if (useCache) {
      this.metrics['cacheMisses']++;
    }

    // 等待并发限制
    await this.waitForConcurrency();

    try {
      const startTime = performance.now();

      // 发送请求
      const response = await this.optimizedFetch(url, options);

      const endTime = performance.now();
      const responseTime = endTime - startTime;

      // 更新指标
      this.metrics['requestCount']++;
      this.metrics['responseTime'] += responseTime;

      if (!response.ok) {
        this.metrics['errorCount']++;
        console.error('❌ 请求失败:', url, response.status);
      }

      // 缓存响应
      if (useCache && response.ok) {
        this.requestCache.set(cacheKey, response);
        console.log('💾 响应已缓存:', cacheKey);
      }

      // 释放并发限制
      this.releaseConcurrency();

      return response;
    } catch (error) {
      console.error('❌ 请求异常:', url, error);
      this.metrics['errorCount']++;
      this.releaseConcurrency();
      throw error;
    }
  }

  /**
   * 优化的 fetch
   */
  async optimizedFetch(url, options) {
    // 尝试从缓存获取
    if (this.cache && options.method === 'GET') {
      try {
        const cachedResponse = await this.cache.match(url);
        if (cachedResponse) {
          console.log('💾 Service Worker 缓存命中:', url);
          return cachedResponse;
        }
      } catch (error) {
        console.warn('⚠️  Service Worker 缓存查找失败:', error);
      }
    }

    // 发送网络请求
    const response = await fetch(url, options);

    // 缓存响应
    if (this.cache && options.method === 'GET' && response.ok) {
      try {
        const responseClone = response.clone();
        await this.cache.put(url, responseClone);
        console.log('💾 响应已缓存到 Service Worker:', url);
      } catch (error) {
        console.warn('⚠️  缓存响应失败:', error);
      }
    }

    return response;
  }

  /**
   * 等待并发限制
   */
  async waitForConcurrency() {
    while (this.concurrencySemaphore.value <= 0) {
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    this.concurrencySemaphore.value--;
  }

  /**
   * 释放并发限制
   */
  releaseConcurrency() {
    this.concurrencySemaphore.value++;
  }

  /**
   * 获取缓存键
   */
  getCacheKey(url, options) {
    const method = options.method || 'GET';
    const body = options.body || '';
    return `${method}:${url}:${body}`;
  }

  /**
   * 批量请求
   */
  async fetchAll(requests, options = {}) {
    console.log('📦 批量请求:', requests.length);

    const results = await Promise.all(
      requests.map(request => this.fetch(request.url, request.options))
    );

    return results;
  }

  /**
   * 预加载资源
   */
  async prefetch(urls) {
    console.log('⚡ 预加载资源:', urls.length);

    const promises = urls.map(url => {
      return this.fetch(url, { method: 'HEAD' }, false);
    });

    await Promise.all(promises);
    console.log('✅ 预加载完成');
  }

  /**
   * 清理缓存
   */
  async clearCache() {
    console.log('🧹 清理缓存');

    // 清理内存缓存
    this.requestCache.clear();

    // 清理 Service Worker 缓存
    if (this.cache) {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map(name => caches.delete(name))
      );
    }

    console.log('✅ 缓存已清理');
  }

  /**
   * 获取性能指标
   */
  getMetrics() {
    const avgResponseTime = this.metrics['requestCount'] > 0
      ? this.metrics['responseTime'] / this.metrics['requestCount']
      : 0;

    const cacheHitRate = (this.metrics['cacheHits'] + this.metrics['cacheMisses']) > 0
      ? this.metrics['cacheHits'] / (this.metrics['cacheHits'] + this.metrics['cacheMisses'])
      : 0;

    const errorRate = this.metrics['requestCount'] > 0
      ? this.metrics['errorCount'] / this.metrics['requestCount']
      : 0;

    return {
      'requestCount': this.metrics['requestCount'],
      'avgResponseTime': avgResponseTime,
      'errorCount': this.metrics['errorCount'],
      'errorRate': errorRate,
      'cacheHitRate': cacheHitRate,
      'cacheHits': this.metrics['cacheHits'],
      'cacheMisses': this.metrics['cacheMisses']
    };
  }
}

// 导出网络优化器
window.NetworkOptimizer = NetworkOptimizer;
