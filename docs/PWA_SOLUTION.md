# 智桥 Web UI PWA 化方案

## 概述

本文档说明如何将智桥的 Web UI 转换为 PWA（Progressive Web App），实现接近原生应用的用户体验。

## 📋 功能对比：PWA vs 原生应用

### ✅ Web UI 完全可以实现的功能

| 功能 | 技术方案 | 实现状态 |
|------|---------|---------|
| **实时双向同步** | WebSocket | ✅ 已实现 |
| **多会话管理** | 前端状态管理 | ✅ 已实现 |
| **端到端加密** | Web Crypto API | ✅ 已实现 |
| **离线缓存** | Service Worker + IndexedDB | ✅ 已实现 |
| **文件提及** | 文件 API + 前端解析 | ✅ 新增 |
| **斜杠命令** | 前端命令解析器 | ✅ 新增 |
| **自定义代理库** | 文件同步 API | 🔲 待实现 |
| **权限提示 UI** | 前端对话框 + 后端拦截 | 🔲 待实现 |
| **响应式设计** | CSS Media Queries | ✅ 已实现 |

### 🟡 Web UI 可以实现但有差异的功能

| 功能 | Web 实现 | 原生实现 | 差异说明 |
|------|---------|---------|---------|
| **推送通知** | Web Push API | FCM/APNs | ✅ 已实现（push.js） |
| **文件访问** | File System Access API | 原生文件系统 | 需要用户授权 |
| **后台运行** | Service Worker | 原生后台服务 | 受限较多，但够用 |
| **系统集成** | Web Share API 等 | 原生 API | 分享、快捷方式可接入 |
| **离线使用** | Service Worker | 原生缓存 | 效果相似 |
| **安装到主屏幕** | PWA Manifest | App Store | ✅ 已实现（manifest.json） |

### 🔴 Web UI 无法实现的功能

| 功能 | 限制 | 替代方案 |
|------|------|---------|
| **完全后台运行** | 浏览器限制 | 推送通知可部分解决 |
| **原生通知栏完全控制** | 浏览器沙盒 | Web Push API 足够 |
| **系统级权限** | 安全限制 | 文件、相机等可通过 API 请求 |
| **App Store 分发** | 浏览器生态 | PWA 可安装到主屏幕 |

## 🚀 已实现的 PWA 功能

### 1. PWA Manifest (web/ui/manifest.json)

**功能：**
- 定义应用元数据（名称、图标、主题色）
- 设置为 standalone 模式（全屏应用体验）
- 添加快捷方式（新建会话、会话列表、工具选择）
- 支持移动端横屏锁定

**使用方式：**
1. 用户访问 Web UI
2. 浏览器提示"添加到主屏幕"
3. 点击安装后，应用以全屏模式运行
4. 从主屏幕启动，体验接近原生应用

### 2. 推送通知 (web/ui/js/push.js)

**功能：**
- Web Push API 集成
- 通知权限管理
- 会话状态变化通知（启动、停止、完成、错误、需要输入）
- 任务完成通知
- 错误通知
- 测试通知功能

**使用示例：**
```javascript
// 测试通知
window.pushManager.testNotification();

// 会话状态变化通知
window.pushManager.notifySessionChange(sessionId, 'completed', 'Crush');

// 任务完成通知
window.pushManager.notifyTaskComplete('代码生成', '成功');

// 错误通知
window.pushManager.notifyError('连接失败', '无法连接到服务器');
```

**需要配置：**
- VAPID 公钥/私钥对（用于 Web Push）
- 后端推送服务（发送通知到浏览器）

### 3. 文件提及系统 (web/ui/js/file-mentions.js)

**功能：**
- 解析 `@file` 语法
- 文件路径验证和安全检查
- 文件内容读取和缓存
- 自动补全 UI（输入 @ 后显示文件列表）
- 注入文件上下文到提示词

**使用示例：**
```javascript
// 处理用户输入
const result = await window.fileMentionsManager.processInput(
    '帮我查看 @src/main.js 的代码'
);

// result.prompt: 增强后的提示词（包含文件内容）
// result.mentions: 提及的文件列表
// result.cleanPrompt: 清理后的提示词

// 搜索文件
const files = await window.fileMentionsManager.searchFiles('main');

// 创建文件提及 UI
const wrapper = window.fileMentionsManager.createMentionUI(textarea);
```

**需要配置：**
- 后端文件读取 API (`/api/files/read`)
- 后端文件搜索 API (`/api/files/search`)
- 后端文件统计 API (`/api/files/stats`)

### 4. 斜杠命令系统 (web/ui/js/slash-commands.js)

**功能：**
- 内置命令：`/help`, `/model`, `/clear`, `/sessions`, `/tools`, `/settings`, `/exit`, `/export`
- 自定义命令注册
- 命令自动补全（输入 / 后显示命令列表）
- 命令历史记录
- 模糊搜索

**内置命令示例：**
```
/help                    # 显示帮助
/help model             # 显示 /model 命令的帮助
/model                   # 查看当前模型
/model zai/glm-4.6       # 切换到指定模型
/clear                   # 清除会话输出
/sessions                # 列出所有会话
/tools                   # 列出所有工具
/settings                # 打开设置
/exit                    # 退出当前会话
/export                  # 导出会话为 Markdown
/export json            # 导出会话为 JSON
```

**注册自定义命令：**
```javascript
window.slashCommandsManager.registerCommand({
    name: 'mycommand',
    description: '我的自定义命令',
    usage: '/mycommand [args]',
    handler: async (args) => {
        return '命令执行结果';
    }
});
```

**使用示例：**
```javascript
// 检查是否为命令
if (window.slashCommandsManager.isCommand(input)) {
    const output = await window.slashCommandsManager.executeCommand(input);
    console.log(output);
}

// 创建命令自动补全 UI
const wrapper = window.slashCommandsManager.createAutoCompleteUI(textarea);
```

### 5. Service Worker (phase4/optimization/sw.js)

**功能：**
- 离线缓存（静态资源）
- 网络请求拦截
- 缓存管理
- 自动更新

**缓存内容：**
- HTML 文件
- CSS 样式表
- JavaScript 模块
- 图标资源

## 📱 移动端优化

### 已实现

1. **响应式设计**
   - `mobile.css` - 移动端特定样式
   - `responsive.css` - 响应式布局
   - 触摸友好的交互

2. **PWA 安装**
   - 添加到主屏幕
   - 全屏运行
   - 启动画面（可选）

3. **移动端快捷方式**
   - 新建会话
   - 会话列表
   - 工具选择

### 待实现

1. **触摸手势**
   - 滑动切换会话
   - 长按上下文菜单
   - 双指缩放

2. **移动端优化 UI**
   - 底部导航栏
   - 侧边抽屉菜单
   - 浮动操作按钮（FAB）

3. **原生功能集成**
   - 相机/相册（用于截图）
   - 麦克风（用于语音输入）
   - 分享（用于导出会话）

## 🔧 配置步骤

### 1. VAPID 密钥生成（推送通知）

```bash
# 使用 web-push 库生成
npm install -g web-push
web-push generate-vapid-keys
```

将生成的公钥填入 `web/ui/js/push.js`:
```javascript
applicationServerKey: this.urlBase64ToUint8Array(
    'YOUR_VAPID_PUBLIC_KEY_HERE'
)
```

### 2. 后端推送服务

需要实现以下 API 端点：
- `POST /api/notifications/subscribe` - 订阅推送通知
- `POST /api/notifications/unsubscribe` - 取消订阅
- `POST /api/notifications/send` - 发送推送通知

### 3. 文件 API 端点

需要实现以下 API 端点：
- `GET /api/files/read?path=...` - 读取文件内容
- `GET /api/files/search?q=...` - 搜索文件
- `GET /api/files/stats?path=...` - 获取文件统计信息
- `GET /api/files/list?path=...` - 列出目录内容

### 4. 图标资源

创建以下尺寸的图标：
- 16x16, 32x32, 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512

放置在 `web/ui/icons/` 目录。

## 📊 性能对比

| 指标 | Web PWA | 原生应用 | 说明 |
|------|---------|---------|------|
| **首次加载** | ~2s | ~1s | PWA 需要加载资源，但可缓存 |
| **后续加载** | ~0.5s | ~0.3s | PWA 使用缓存，接近原生 |
| **内存使用** | ~50MB | ~30MB | PWA 稍高，但可接受 |
| **启动时间** | ~1s | ~0.5s | PWA 接近原生 |
| **网络依赖** | 低（离线缓存） | 无 | PWA 可离线使用 |
| **更新机制** | 自动（后台） | App Store | PWA 更新更灵活 |

## 🎯 用户体验对比

### Web PWA 优势

1. **无需下载安装**：通过浏览器直接访问
2. **跨平台**：一套代码支持 iOS、Android、桌面
3. **自动更新**：无需用户手动更新
4. **体积小**：相比原生应用节省存储空间
5. **安全**：HTTPS 强制加密，沙盒隔离

### 原生应用优势

1. **完全后台运行**：不受浏览器限制
2. **更多系统权限**：通知、文件、传感器等
3. **更流畅的动画**：GPU 加速更充分
4. **应用商店分发**：更高的可见度和信任度

## 📝 开发建议

### 1. 优先使用 PWA

**理由：**
- 开发成本低（一次开发，多平台）
- 维护成本低（代码统一）
- 发布流程简单（无需审核）
- 用户体验接近原生

**适用场景：**
- 工具类应用（如智桥）
- 生产力应用
- 内容消费应用
- 内部应用

### 2. 考虑原生应用的场景

**需要原生应用当：**
- 需要完全后台运行
- 需要大量系统权限
- 需要高性能 3D/动画
- 需要复杂的离线处理
- 需要在应用商店分发

### 3. 混合方案

**建议：**
1. 先开发 PWA 版本
2. 收集用户反馈
3. 根据需求决定是否开发原生应用
4. 核心功能保持统一（通过 WebSocket + API）

## 🚀 部署

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name zhineng-bridge.example.com;

    root /var/www/zhineng-bridge;
    index index.html;

    # HTTPS 重定向
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name zhineng-bridge.example.com;

    root /var/www/zhineng-bridge;
    index index.html;

    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/zhineng-bridge.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/zhineng-bridge.example.com/privkey.pem;

    # Service Worker 支持
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # PWA Manifest
    location /manifest.json {
        add_header Content-Type application/json;
    }

    # API 端点
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 📚 参考资料

- [PWA 规范](https://www.w3.org/TR/appmanifest/)
- [Web Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Web Crypto API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API)
- [File System Access API](https://developer.mozilla.org/en-US/docs/Web/API/File_System_Access_API)
- [IndexedDB](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)

## 🎉 总结

通过 PWA 技术，智桥的 Web UI 可以实现 90%+ 的原生应用功能，包括：

✅ **已实现：**
- 实时双向同步
- 多会话管理
- 端到端加密
- 离线缓存
- 推送通知
- 文件提及
- 斜杠命令
- 响应式设计
- 安装到主屏幕

🔲 **待实现：**
- 自定义代理库同步
- MCP 工具权限提示
- 触摸手势
- 移动端优化 UI

**建议：** 优先使用 PWA 方案，根据用户反馈决定是否开发原生应用。PWA 可以快速验证产品价值，降低开发和维护成本。
