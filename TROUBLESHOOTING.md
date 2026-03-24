# 智桥故障排查指南

## 📖 目录

1. [快速诊断](#快速诊断)
2. [连接问题](#连接问题)
3. [会话问题](#会话问题)
4. [性能问题](#性能问题)
5. [错误代码](#错误代码)
6. [调试技巧](#调试技巧)
7. [日志分析](#日志分析)
8. [常见问题](#常见问题)

---

## 🔍 快速诊断

### 诊断检查清单

遇到问题时，按以下顺序检查：

- [ ] 服务是否正在运行？
- [ ] 端口是否被占用？
- [ ] 防火墙是否阻止连接？
- [ ] 浏览器控制台是否有错误？
- [ ] 服务器日志是否有错误？
- [ ] 网络连接是否正常？
- [ ] 配置文件是否正确？

### 快速诊断脚本

```bash
#!/bin/bash
# 快速诊断脚本

echo "=== 智桥诊断 ==="
echo ""

# 检查服务
echo "1. 检查服务运行状态..."
ps aux | grep -E "start_server.py|start_manager.py" | grep -v grep
echo ""

# 检查端口
echo "2. 检查端口占用..."
lsof -i :8765 2>/dev/null || echo "端口 8765 未被占用"
echo ""

# 检查防火墙
echo "3. 检查防火墙..."
sudo ufw status 2>/dev/null || echo "无法检查防火墙状态"
echo ""

# 检查网络
echo "4. 检查网络连接..."
ping -c 1 localhost > /dev/null 2>&1 && echo "本地网络正常" || echo "本地网络异常"
echo ""

# 检查 Python 环境
echo "5. 检查 Python 环境..."
python3 --version
pip list | grep websockets
echo ""

# 检查 Node.js 环境
echo "6. 检查 Node.js 环境..."
node --version 2>/dev/null || echo "Node.js 未安装"
npm list 2>/dev/null | head -5
echo ""

echo "=== 诊断完成 ==="
```

---

## 🔌 连接问题

### 问题 1: WebSocket 连接失败

**症状**:
- 浏览器控制台显示 "WebSocket connection failed"
- Web UI 显示连接错误
- 无法连接到服务器

**可能原因**:
1. 中继服务器未启动
2. 端口被占用
3. 防火墙阻止连接
4. 端口号配置错误

**诊断步骤**:

```bash
# 1. 检查服务器是否运行
ps aux | grep start_server.py

# 2. 检查端口是否被监听
lsof -i :8765

# 3. 检查端口是否被占用
netstat -tuln | grep 8765

# 4. 检查防火墙
sudo ufw status
```

**解决方案**:

```bash
# 解决方案 1: 启动服务器
cd relay-server
python3 start_server.py

# 解决方案 2: 修改端口
# 编辑 relay-server/server.py
server = CrushRelayServer(port=8766)  # 使用其他端口

# 解决方案 3: 允许防火墙
sudo ufw allow 8765

# 解决方案 4: 停止占用端口的程序
lsof -ti :8765 | xargs kill -9
```

### 问题 2: 连接超时

**症状**:
- WebSocket 连接建立后立即超时
- 消息发送后无响应
- 长时间无活动后断开

**可能原因**:
1. 网络延迟
2. 服务器负载过高
3. 心跳配置不正确

**解决方案**:

```bash
# 1. 调整心跳间隔
# 编辑 web/ui/js/client.js
const config = {
    ping_interval: 30,  # 增加到 30 秒
    reconnect_interval: 10  # 增加重连间隔
};

# 2. 检查网络延迟
ping -c 10 localhost

# 3. 优化服务器性能
# 查看服务器资源使用
top
htop
```

### 问题 3: 自动重连失败

**症状**:
- 连接断开后无法自动重连
- 重连尝试不断失败
- 需要手动刷新页面才能重新连接

**解决方案**:

```javascript
// 在 web/ui/js/client.js 中检查自动重连配置
const config = {
    auto_reconnect: true,  // 确保启用
    max_reconnect_attempts: 10,  // 增加重连尝试次数
    reconnect_interval: 5
};

// 添加重连失败后的处理
function handleReconnectFailure() {
    console.error('重连失败，请检查服务器状态');
    // 显示错误提示给用户
}
```

---

## 🎯 会话问题

### 问题 4: 会话创建失败

**症状**:
- 点击"创建会话"后无响应
- 显示错误消息
- 会话列表为空

**可能原因**:
1. Session Manager 未启动
2. 工具可执行文件不存在
3. 参数错误

**诊断步骤**:

```bash
# 1. 检查 Session Manager 是否运行
ps aux | grep start_manager.py

# 2. 检查工具是否存在
which crush
which claude

# 3. 检查工具权限
ls -l /usr/local/bin/crush

# 4. 查看服务器日志
tail -f /tmp/relay-server.log
```

**解决方案**:

```bash
# 解决方案 1: 启动 Session Manager
cd phase1/session_manager
python3 start_manager.py

# 解决方案 2: 安装工具
# 根据官方文档安装相应的 AI 工具

# 解决方案 3: 添加执行权限
chmod +x /usr/local/bin/crush

# 解决方案 4: 验证工具
crush --help
```

### 问题 5: 会话状态异常

**症状**:
- 会话状态显示不正确
- 会话无法停止
- 会话显示为"卡死"状态

**解决方案**:

```bash
# 1. 查看会话详细信息
# 通过 API 查询
ws.send(JSON.stringify({
    "type": "list_sessions"
}));

# 2. 重启 Session Manager
ps aux | grep start_manager.py | grep -v grep | awk '{print $2}' | xargs kill -9
cd phase1/session_manager
python3 start_manager.py

# 3. 清理僵尸会话
# 编辑 phase1/session_manager/session_manager.py
# 添加会话超时清理逻辑
```

### 问题 6: 多个会话冲突

**症状**:
- 不同会话间命令冲突
- 会话切换后状态混乱
- 输出显示到错误的会话

**解决方案**:

```bash
# 1. 确保每个会话独立运行
# Session Manager 已经实现会话隔离

# 2. 检查会话配置
# 确保每个会话有独立的工作目录

# 3. 清理旧会话
# 在 Web UI 中删除不需要的会话
```

---

## ⚡ 性能问题

### 问题 7: 页面加载缓慢

**症状**:
- 首次加载时间超过 5 秒
- 资源加载缓慢
- 交互响应延迟

**诊断步骤**:

```bash
# 1. 检查资源大小
du -sh web/ui/

# 2. 检查网络速度
speedtest-cli

# 3. 检查浏览器缓存
# 在浏览器开发者工具中查看 Network 标签
```

**解决方案**:

```bash
# 1. 优化资源文件
# 压缩图片
optipng web/ui/images/*.png

# 压缩 CSS
cssnano web/ui/css/*.css -o optimized/

# 压缩 JavaScript
uglifyjs web/ui/js/*.js -o optimized.js

# 2. 启用 Gzip 压缩
# 在 Nginx 配置中添加
gzip on;
gzip_types text/css application/javascript application/json;

# 3. 使用 CDN
# 将静态资源部署到 CDN

# 4. 实现懒加载
# 修改 web/ui/js/app.js
function lazyLoad() {
    // 按需加载模块
}
```

### 问题 8: 内存使用过高

**症状**:
- 内存占用持续增长
- 系统变慢
- 最终崩溃

**诊断步骤**:

```bash
# 1. 检查内存使用
top
htop

# 2. 检查 Python 进程内存
ps aux | grep python

# 3. 使用内存分析工具
python3 -m memory_profiler your_script.py
```

**解决方案**:

```bash
# 1. 清理不需要的会话
# 在 Web UI 中删除旧会话

# 2. 重启服务
kill -9 <PID>
python3 start_server.py

# 3. 调整会话限制
# 编辑 phase1/session_manager/session_manager.py
self.max_sessions = 50  # 减少最大会话数

# 4. 实现内存监控
# 定期检查内存使用，超过阈值时自动清理
```

### 问题 9: CPU 使用率过高

**症状**:
- CPU 使用率持续 > 80%
- 系统响应缓慢
- 风扇噪音增大

**解决方案**:

```bash
# 1. 检查 CPU 使用
top -p <PID>

# 2. 查看瓶颈
python3 -m cProfile -o profile.stats your_script.py
python3 -m pstats profile.stats

# 3. 优化代码
# 使用异步操作
# 避免阻塞调用
# 使用缓存
```

---

## 🔢 错误代码

### WebSocket 错误

| 错误代码 | 错误消息 | 可能原因 | 解决方案 |
|----------|----------|----------|----------|
| 1000 | 正常关闭 | 连接正常结束 | 无需处理 |
| 1001 | 端点离开 | 客户端关闭 | 正常行为 |
| 1002 | 协议错误 | 协议不匹配 | 检查 WebSocket 版本 |
| 1003 | 不支持的数据类型 | 数据格式错误 | 检查消息格式 |
| 1006 | 连接异常关闭 | 网络问题 | 检查网络连接 |
| 1007 | 数据不一致 | 数据类型错误 | 检查数据格式 |
| 1008 | 策略违规 | 违反安全策略 | 检查消息内容 |
| 1009 | 消息过大 | 超过大小限制 | 减小消息大小 |
| 1010 | 缺少扩展 | 扩展未支持 | 检查 WebSocket 扩展 |
| 1011 | 内部错误 | 服务器错误 | 查看服务器日志 |
| 1015 | TLS 握手失败 | 证书问题 | 检查 TLS 配置 |

### 服务器错误

| 错误代码 | 错误消息 | 可能原因 | 解决方案 |
|----------|----------|----------|----------|
| 500 | 服务器内部错误 | 代码错误 | 查看服务器日志 |
| 503 | 服务不可用 | 服务未启动 | 启动相关服务 |
| 504 | 网关超时 | 响应超时 | 增加超时时间 |

### 应用错误

| 错误代码 | 错误消息 | 可能原因 | 解决方案 |
|----------|----------|----------|----------|
| E001 | 工具不存在 | 工具未注册 | 检查工具配置 |
| E002 | 工具不可用 | 工具未安装 | 安装相应工具 |
| E003 | 参数错误 | 参数格式错误 | 检查参数格式 |
| E004 | 会话不存在 | 会话 ID 错误 | 检查会话 ID |
| E005 | 会话已满 | 达到会话上限 | 删除旧会话 |

---

## 🐛 调试技巧

### 启用调试日志

**服务器端**:

```python
# 编辑 relay-server/server.py
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 设置为 DEBUG 级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**客户端**:

```javascript
// 编辑 web/ui/js/client.js
const DEBUG = true;  // 启用调试

function logDebug(message, data) {
    if (DEBUG) {
        console.log('[DEBUG]', message, data);
    }
}
```

### 使用浏览器开发者工具

1. **Console 标签**: 查看 JavaScript 错误和日志
2. **Network 标签**: 查看 WebSocket 消息和网络请求
3. **Sources 标签**: 设置断点调试 JavaScript
4. **Performance 标签**: 分析性能瓶颈

### 使用 Python 调试器

```bash
# 使用 pdb 调试
python3 -m pdb relay-server/server.py

# 常用命令
# n (next): 执行下一行
# s (step): 进入函数
# c (continue): 继续执行
# p (print): 打印变量
# l (list): 查看代码
```

### 使用 IPython 调试

```bash
# 安装 IPython
pip install ipython

# 使用 IPython 调试
from IPython import embed
embed()
```

---

## 📋 日志分析

### 日志位置

- **中继服务器**: `/tmp/relay-server.log`
- **Session Manager**: `/tmp/session-manager.log`
- **浏览器**: 浏览器开发者工具 Console

### 日志格式

```
2026-03-25 12:00:00 - server - INFO - 🚀 启动中继服务器
2026-03-25 12:00:00 - server - INFO -    地址: 0.0.0.0:8765
2026-03-25 12:00:01 - server - INFO - 📡 客户端已连接: xxx-xxx-xxx
2026-03-25 12:00:02 - server - INFO - 📨 收到消息: xxx-xxx-xxx - ping
2026-03-25 12:00:02 - server - INFO - 💓 心跳
```

### 日志分析命令

```bash
# 查看最近的错误
grep ERROR /tmp/relay-server.log | tail -20

# 统计错误类型
grep ERROR /tmp/relay-server.log | awk '{print $NF}' | sort | uniq -c

# 查看特定时间的日志
grep "12:00:0[0-9]" /tmp/relay-server.log

# 查看特定客户端的日志
grep "xxx-xxx-xxx" /tmp/relay-server.log

# 实时监控日志
tail -f /tmp/relay-server.log

# 导出日志
grep ERROR /tmp/relay-server.log > errors.log
```

---

## ❓ 常见问题

### 安装问题

**Q1: pip install 失败？**

A: 使用虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate
pip install websockets asyncio
```

**Q2: npm install 失败？**

A: 清除缓存后重试：
```bash
npm cache clean --force
npm install
```

### 配置问题

**Q3: 如何修改端口？**

A: 编辑 `relay-server/server.py`：
```python
server = CrushRelayServer(port=8766)  # 修改端口
```

**Q4: 如何配置 HTTPS？**

A: 使用 Nginx 反向代理：
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 使用问题

**Q5: 如何查看所有会话？**

A: 发送 `list_sessions` 消息：
```javascript
ws.send(JSON.stringify({
    "type": "list_sessions"
}));
```

**Q6: 如何删除会话？**

A: 发送 `delete_session` 消息：
```javascript
ws.send(JSON.stringify({
    "type": "delete_session",
    "session_id": "xxx-xxx-xxx"
}));
```

**Q7: 如何切换会话？**

A: 在 Web UI 中点击会话卡片，或通过 SessionManager 设置活动会话。

### 性能问题

**Q8: 如何提高性能？**

A: 参考以下优化建议：
1. 使用 Web Workers
2. 实现缓存策略
3. 代码分割
4. 懒加载
5. 使用 Service Workers

**Q9: 如何减少内存使用？**

A: 参考以下建议：
1. 定期清理会话
2. 使用对象池
3. 避免内存泄漏
4. 使用 Profiler 工具

### 安全问题

**Q10: 如何保护 WebSocket 连接？**

A: 使用 WSS（WebSocket Secure）：
```javascript
const ws = new WebSocket('wss://your-domain.com');
```

**Q11: 如何实现用户认证？**

A: 参考 Phase 3 的加密模块：
```python
# 使用端到端加密
from phase3.encryption.encryption import EncryptionManager
```

---

## 📞 获取帮助

### 自助资源

- 📖 [快速入门](QUICKSTART.md)
- 📘 [使用指南](USAGE_GUIDE.md)
- 📗 [API 文档](docs/API.md)
- 📙 [开发指南](AGENTS.md)

### 社区支持

- 💬 **GitHub Discussions**: https://github.com/guangda88/zhineng-bridge/discussions
- 🐛 **Issue 跟踪**: https://github.com/guangda88/zhineng-bridge/issues
- 📧 **邮件支持**: support@example.com（示例）

### 报告问题

提交 Issue 时，请提供以下信息：

1. **问题描述**: 详细描述问题
2. **复现步骤**: 如何重现问题
3. **预期行为**: 期望的正确行为
4. **实际行为**: 实际发生的行为
5. **环境信息**:
   - 操作系统
   - Python 版本
   - Node.js 版本
   - 浏览器版本
6. **日志**: 相关的日志输出
7. **截图**: 错误截图（如果适用）

---

## 🔧 高级故障排查

### 使用 strace 追踪系统调用

```bash
# 追踪 Python 进程
strace -p <PID> -o trace.log

# 追踪文件访问
strace -p <PID> -e trace=file

# 追踪网络访问
strace -p <PID> -e trace=network
```

### 使用 tcpdump 抓包

```bash
# 抓取 WebSocket 数据包
tcpdump -i lo port 8765 -w websocket.pcap

# 分析数据包
tcpdump -r websocket.pcap -A
```

### 使用 wireshark 分析

```bash
# 安装 wireshark
sudo apt install wireshark

# 打开抓包文件
wireshark websocket.pcap
```

---

**智桥（Zhineng-bridge） - 连接多个 AI 编码工具的桥梁** 🚀

希望这个故障排查指南能帮助你解决问题！
