/**
 * 预加载资源
 */

class PreloadManager {
  constructor() {
    this.preloadedResources = new Map();
    this.initialized = false;
  }

  /**
   * 初始化预加载管理器
   */
  async init() {
    if (this.initialized) {
      console.warn('⚠️  预加载管理器已初始化');
      return;
    }

    console.log('⚡ 初始化预加载管理器');

    // 预加载 JavaScript 文件
    await this.preloadScripts();

    // 预加载 CSS 文件
    await this.preloadStyles();

    // 预加载图片
    await this.preloadImages();

    // 预加载字体
    await this.preloadFonts();

    this.initialized = true;
    console.log('✅ 预加载管理器已初始化');
  }

  /**
   * 预加载 JavaScript 文件
   */
  async preloadScripts() {
    console.log('📜 预加载 JavaScript 文件');

    const scripts = [
      'js/app.js',
      'js/tools.js',
      'js/sessions.js',
      'js/settings.js',
      'js/client.js',
      'js/dynamic_imports.js'
    ];

    for (const script of scripts) {
      try {
        await this.preloadResource(script, 'script');
        this.preloadedResources.set(script, true);
      } catch (error) {
        console.warn(`⚠️  预加载失败: ${script}`, error);
      }
    }
  }

  /**
   * 预加载 CSS 文件
   */
  async preloadStyles() {
    console.log('🎨 预加载 CSS 文件');

    const styles = [
      'css/base.css',
      'css/layout.css',
      'css/components.css',
      'css/responsive.css',
      'css/mobile.css'
    ];

    for (const style of styles) {
      try {
        await this.preloadResource(style, 'style');
        this.preloadedResources.set(style, true);
      } catch (error) {
        console.warn(`⚠️  预加载失败: ${style}`, error);
      }
    }
  }

  /**
   * 预加载图片
   */
  async preloadImages() {
    console.log('🖼️  预加载图片');

    const images = document.querySelectorAll('img[data-src]');
    
    for (const img of images) {
      const src = img.dataset.src;
      if (src) {
        try {
          await this.preloadResource(src, 'image');
          this.preloadedResources.set(src, true);
        } catch (error) {
          console.warn(`⚠️  预加载失败: ${src}`, error);
        }
      }
    }
  }

  /**
   * 预加载字体
   */
  async preloadFonts() {
    console.log('🔤 预加载字体');

    const fonts = [
      'Arial',
      'Helvetica',
      'sans-serif',
      'Courier New',
      'monospace'
    ];

    // 使用 document.fonts 预加载字体
    for (const font of fonts) {
      try {
        await document.fonts.load(`12px ${font}`);
        console.log(`✅ 字体已预加载: ${font}`);
      } catch (error) {
        console.warn(`⚠️  预加载字体失败: ${font}`, error);
      }
    }
  }

  /**
   * 预加载资源
   */
  async preloadResource(url, type) {
    return new Promise((resolve, reject) => {
      if (type === 'script') {
        const script = document.createElement('link');
        script.rel = 'preload';
        script.as = 'script';
        script.href = url;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      } else if (type === 'style') {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'style';
        link.href = url;
        link.onload = resolve;
        link.onerror = reject;
        document.head.appendChild(link);
      } else if (type === 'image') {
        const img = new Image();
        img.onload = resolve;
        img.onerror = reject;
        img.src = url;
      } else {
        reject(new Error(`未知资源类型: ${type}`));
      }
    });
  }

  /**
   * 检查资源是否已预加载
   */
  isPreloaded(url) {
    return this.preloadedResources.has(url);
  }

  /**
   * 获取预加载统计
   */
  getStats() {
    return {
      total: this.preloadedResources.size,
      preloaded: Array.from(this.preloadedResources.keys())
    };
  }
}

// 导出预加载管理器
window.PreloadManager = PreloadManager;
