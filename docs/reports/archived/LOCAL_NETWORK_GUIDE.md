# 本地网络使用指南

**日期：** 2026-03-29
**环境：** 本地网络（同一WiFi/局域网）
**状态：** ✅ 完全可用

---

## 📱 当前能力

### ✅ 已实现功能

在**同一WiFi/局域网**内，你可以：

1. **手机访问** 📱
   - 访问Web界面管理AI会话
   - 实时查看AI输出
   - 发送命令给AI工具

2. **平板访问** 📲
   - 大屏幕查看会话输出
   - 触摸优化界面
   - PWA全屏体验

3. **HTTPS安全连接** 🔒
   - 使用自签名证书
   - 加密通信
   - WebSocket Secure (WSS)

4. **PWA离线功能** 📴
   - 首次加载后可离线访问
   - 添加到主屏幕
   - 推送通知

---

## 🚀 快速开始

### 方式1：HTTP访问（最简单）

**1. 确保服务运行：**

```bash
# 检查服务状态
ps aux | grep python3 | grep -E "(relay|session_manager)"

# 如果未运行，启动服务
cd /home/ai/zhibridge/relay-server
python3 start_server.py &

cd /home/ai/zhibridge/phase1/session_manager
python3 start_manager.py &
```

**2. 手机访问：**

```
打开浏览器，输入：
http://10.113.22.99:8080/web/ui/index.html

或：
http://100.66.1.8:8080/web/ui/index.html

或：
http://192.168.2.1:8080/web/ui/index.html
```

**3. 测试功能：**
- ✅ 选择工具（Crush/Claude等）
- ✅ 创建新会话
- ✅ 发送命令
- ✅ 查看实时输出

---

### 方式2：HTTPS访问（推荐）

**1. 启动Nginx：**

```bash
# 使用Docker启动Nginx
docker run -d \
  --name zhineng-nginx \
  --restart unless-stopped \
  -p 80:80 \
  -p 443:443 \
  -v /home/ai/zhibridge/nginx/nginx-local.conf:/etc/nginx/nginx.conf:ro \
  -v /home/ai/zhibridge/nginx/ssl:/etc/nginx/ssl:ro \
  -v /home/ai/zhibridge/web/ui:/app/web:ro \
  nginx:latest

# 检查Nginx状态
docker ps | grep zhineng-nginx
```

**2. 手机访问：**

```
打开浏览器，输入：
https://10.113.22.99/web/ui/index.html
```

**3. 浏览器会提示证书不安全，选择：**
- Chrome: "高级" → "继续访问"
- Safari: "详细信息" → "访问此网站"

**4. 测试功能：**
- ✅ HTTPS加密连接
- ✅ WebSocket Secure (WSS)
- ✅ PWA推送通知
- ✅ 所有HTTP功能

---

## 📲 手机端使用指南

### iOS Safari

#### 1. 访问Web界面
```
Safari浏览器打开：
http://10.113.22.99:8080/web/ui/index.html
```

#### 2. 添加到主屏幕（PWA）
```
1. 点击底部分享按钮
2. 滑动并选择"添加到主屏幕"
3. 点击"添加"
```

#### 3. 使用PWA
```
- 像原生APP一样使用
- 全屏显示，无浏览器栏
- 支持离线访问（首次加载后）
```

#### 4. 启用推送通知
```
1. 系统设置 → Safari
2. 关闭"阻止所有弹窗"
3. 访问网站时允许通知
```

### Android Chrome

#### 1. 访问Web界面
```
Chrome浏览器打开：
http://10.113.22.99:8080/web/ui/index.html
```

#### 2. 安装PWA
```
1. 点击菜单按钮（三个点）
2. 选择"安装应用"或"添加到主屏幕"
3. 点击"安装"
```

#### 3. 使用PWA
```
- 桌面会有APP图标
- 点击打开使用
- 支持后台运行
```

---

## 🛠️ 管理命令

### 启动所有服务

```bash
# 启动relay server
cd /home/ai/zhibridge/relay-server
python3 start_server.py > /tmp/relay_server.log 2>&1 &

# 启动session manager
cd /home/ai/zhibridge/phase1/session_manager
python3 start_manager.py > /tmp/session_manager.log 2>&1 &

# 启动nginx（可选，用于HTTPS）
docker run -d \
  --name zhineng-nginx \
  -p 80:80 \
  -p 443:443 \
  -v /home/ai/zhibridge/nginx/nginx-local.conf:/etc/nginx/nginx.conf:ro \
  -v /home/ai/zhibridge/nginx/ssl:/etc/nginx/ssl:ro \
  -v /home/ai/zhibridge/web/ui:/app/web:ro \
  nginx:latest
```

### 查看服务状态

```bash
# 检查进程
ps aux | grep python3 | grep -E "(relay|session_manager)"

# 检查端口
netstat -tlnp | grep -E "(8080|8765|80|443)"

# 检查docker
docker ps | grep zhineng-nginx
```

### 查看日志

```bash
# Relay server日志
tail -f /tmp/relay_server.log

# Session manager日志
tail -f /tmp/session_manager.log

# Nginx日志
docker logs -f zhineng-nginx
```

### 停止所有服务

```bash
# 停止nginx
docker stop zhineng-nginx
docker rm zhineng-nginx

# 停止session manager
pkill -f "start_manager.py"

# 停止relay server
pkill -f "start_server.py"
```

---

## 🔍 网络调试

### 查看本机IP地址

```bash
# 查看所有网络接口
ip addr show

# 查看IPv4地址
ip addr show | grep "inet " | grep -v "127.0.0.1"

# 或使用
hostname -I
```

### 测试手机能否访问

**在电脑上测试：**
```bash
# 测试HTTP
curl http://10.113.22.99:8080/health

# 测试HTTPS（如果nginx运行）
curl -k https://10.113.22.99/health

# 测试WebSocket
python3 -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://10.113.22.99:8765') as ws:
        await ws.send('{\"type\": \"ping\"}')
        response = await ws.recv()
        print(f'Response: {response}')

asyncio.run(test())
"
```

**在手机浏览器测试：**
```
1. 打开浏览器
2. 输入: http://10.113.22.99:8080/health
3. 应该看到: {"status": "healthy", ...}
```

### 防火墙检查

```bash
# 查看防火墙状态
sudo ufw status

# 如果需要开放端口
sudo ufw allow 8080/tcp   # HTTP服务
sudo ufw allow 8765/tcp   # WebSocket
sudo ufw allow 443/tcp    # HTTPS（如果使用）
```

---

## ⚠️ 常见问题

### 问题1：手机无法访问

**检查清单：**
- [ ] 手机和电脑在同一WiFi网络
- [ ] 服务正在运行（`ps aux | grep python3`）
- [ ] 防火墙允许端口（`sudo ufw status`）
- [ ] IP地址正确（`hostname -I`）

**解决方法：**
```bash
# 1. 确认IP地址
hostname -I

# 2. 测试本地访问
curl http://localhost:8080/health

# 3. 测试局域网访问（在电脑上）
curl http://10.113.22.99:8080/health

# 4. 检查防火墙
sudo ufw allow 8080/tcp
```

### 问题2：WebSocket连接失败

**检查清单：**
- [ ] Relay server运行在8765端口
- [ ] 防火墙允许8765端口
- [ ] 使用HTTPS时，浏览器显示证书警告

**解决方法：**
```bash
# 检查WebSocket服务
netstat -tlnp | grep 8765

# 测试WebSocket连接
python3 -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://10.113.22.99:8765') as ws:
        await ws.send('{\"type\": \"ping\"}')
        print('✅ WebSocket连接成功')

asyncio.run(test())
"
```

### 问题3：HTTPS证书警告

**原因：** 使用自签名证书

**解决方法：**
- 选择"继续访问"或"接受风险"
- 这是正常的，证书用于加密通信
- 生产环境使用Let's Encrypt证书

### 问题4：PWA无法添加到主屏幕

**iOS Safari：**
- 确保使用HTTPS（或本地HTTP）
- 网站必须支持Service Worker
- 点击分享按钮 → "添加到主屏幕"

**Android Chrome：**
- 网站必须使用HTTPS
- 点击菜单 → "安装应用"
- 如果没有"安装"选项，清除浏览器缓存重试

---

## 📊 功能对比

| 功能 | HTTP | HTTPS |
|-----|------|-------|
| 基础访问 | ✅ | ✅ |
| 会话管理 | ✅ | ✅ |
| 实时通信 | ✅ | ✅ |
| 文件提及 | ✅ | ✅ |
| 离线缓存 | ✅ | ✅ |
| 推送通知 | ⚠️ 有限 | ✅ 完整 |
| 加密传输 | ❌ | ✅ |
| PWA安装 | ⚠️ 有限 | ✅ 完整 |

**推荐：** 使用HTTPS，支持所有功能

---

## 🎯 使用场景

### 场景1：在家办公

```
电脑运行服务 → 手机WiFi连接 → 访问http://10.113.22.99:8080
```

### 场景2：会议室演示

```
电脑运行服务 → 手机/平板WiFi连接 → 大屏幕展示AI会话
```

### 场景3：床上编程

```
电脑运行服务 → 手机WiFi连接 → 躺床上发送命令
```

### 场景4：离线工作

```
1. 首次访问加载数据
2. 断开WiFi
3. 使用PWA离线查看会话
4. 重新连接同步最新数据
```

---

## 📝 快速参考

### 访问地址

```
HTTP（简单）:
http://10.113.22.99:8080/web/ui/index.html
http://100.66.1.8:8080/web/ui/index.html
http://192.168.2.1:8080/web/ui/index.html

HTTPS（推荐）:
https://10.113.22.99/web/ui/index.html
https://100.66.1.8/web/ui/index.html
https://192.168.2.1/web/ui/index.html
```

### 常用命令

```bash
# 启动服务
cd /home/ai/zhibridge/relay-server && python3 start_server.py &
cd /home/ai/zhibridge/phase1/session_manager && python3 start_manager.py &

# 查看日志
tail -f /tmp/relay_server.log

# 查看会话列表
curl http://10.113.22.99:8080/sessions

# 停止服务
pkill -f "start_server.py"
```

### 文档位置

```
使用指南: docs/OFFLINE_ACCESS_ANALYSIS.md
部署指南: docs/PUBLIC_ACCESS_DEPLOYMENT.md
开发报告: docs/PUBLIC_ACCESS_DEVELOPMENT_REPORT.md
```

---

## 🎉 总结

### 当前状态

**✅ 完全可用：**
- 同一WiFi/局域网内使用
- 手机/平板访问
- HTTPS加密连接
- PWA离线功能
- 实时WebSocket通信

**⚠️ 不支持：**
- 离开本地网络访问
- 公网直接访问
- （需要云服务器或内网穿透）

### 适用场景

✅ **适合：**
- 在家办公
- 局域网内多设备协作
- 演示和展示
- 离线查看（需先加载）

❌ **不适合：**
- 离开办公室使用
- 远程办公
- 公网发布

### 下一步（可选）

如果需要公网访问，可以选择：
1. 部署到云服务器
2. 使用内网穿透（已有配置）
3. 使用VPN

---

**最后更新：** 2026-03-29
**维护者：** Crush AI Assistant
