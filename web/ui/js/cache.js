/**
 * 缓存管理器
 */

class CacheManager {
  constructor() {
    this.cache = new Map();
    this.initialized = false;
    this.ttl = 3600000; // 1 小时
  }

  /**
   * 初始化缓存管理器
   */
  async init() {
    if (this.initialized) {
      console.warn('⚠️  缓存管理器已初始化');
      return;
    }

    console.log('💾 初始化缓存管理器');

    // 检查是否支持 Service Worker
    if ('serviceWorker' in navigator) {
      try {
        // 注册 Service Worker
        const registration = await navigator.serviceWorker.register('/web/ui/sw.js');
        console.log('✅ Service Worker 已注册:', registration);
      } catch (error) {
        console.error('❌ Service Worker 注册失败:', error);
      }
    } else {
      console.warn('⚠️  Service Worker 不支持');
    }

    this.initialized = true;
    console.log('✅ 缓存管理器已初始化');
  }

  /**
   * 设置缓存
   */
  set(key, value, ttl = this.ttl) {
    const expiry = Date.now() + ttl;
    this.cache.set(key, { value, expiry });
    console.log(`💾 缓存已设置: ${key}`);
  }

  /**
   * 获取缓存
   */
  get(key) {
    const cached = this.cache.get(key);
    
    if (!cached) {
      return null;
    }
    
    // 检查是否过期
    if (Date.now() > cached.expiry) {
      this.cache.delete(key);
      console.log(`⏰ 缓存已过期: ${key}`);
      return null;
    }
    
    console.log(`💾 缓存命中: ${key}`);
    return cached.value;
  }

  /**
   * 删除缓存
   */
  delete(key) {
    this.cache.delete(key);
    console.log(`🗑️  缓存已删除: ${key}`);
  }

  /**
   * 清空缓存
   */
  clear() {
    this.cache.clear();
    console.log('🗑️  所有缓存已清空');
  }

  /**
   * 获取缓存统计
   */
  getStats() {
    const now = Date.now();
    let valid = 0;
    let expired = 0;

    for (const [key, cached] of this.cache.entries()) {
      if (now > cached.expiry) {
        expired++;
      } else {
        valid++;
      }
    }

    return {
      total: this.cache.size,
      valid,
      expired
    };
  }

  /**
   * 清理过期缓存
   */
  cleanup() {
    const now = Date.now();
    const keysToDelete = [];

    for (const [key, cached] of this.cache.entries()) {
      if (now > cached.expiry) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => this.cache.delete(key));
    console.log(`🧹 已清理 ${keysToDelete.length} 个过期缓存`);
  }
}

// 导出缓存管理器
window.CacheManager = CacheManager;
