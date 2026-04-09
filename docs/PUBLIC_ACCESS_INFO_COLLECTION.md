# 公网访问配置信息收集

**日期：** 2026-03-29
**任务：** 配置智桥的公网访问

---

## 📋 需要的信息

### 方式A：直接公网IP访问

如果服务器有公网IP，请提供：

```
1. 公网IP地址：
   示例：123.45.67.89

2. 端口映射情况：
   - 8080端口（HTTP服务）→ 公网端口：？
   - 8765端口（WebSocket）→ 公网端口：？
   - 443端口（HTTPS）→ 公网端口：？

3. 防火墙状态：
   - 端口是否已开放？
   - 是否需要配置防火墙？
```

### 方式B：域名访问

如果有域名，请提供：

```
1. 域名：
   示例：zhineng.example.com

2. DNS解析情况：
   - 是否已解析到公网IP？
   - 是否支持HTTPS（需要SSL证书）？

3. 证书情况：
   - 是否有SSL证书？
   - 证书文件位置？
```

### 方式C：内网穿透（FRP）

如果有FRP服务，请提供：

```
1. FRP服务器地址：
   示例：frp.example.com

2. FRP端口：
   默认：7000

3. FRP认证令牌：
   token: xxxxxx

4. 远程端口映射：
   - HTTP端口：？
   - HTTPS端口：？
   - WebSocket端口：？
```

### 方式D：VPN访问

如果通过VPN访问，请提供：

```
1. VPN类型：
   - WireGuard？
   - OpenVPN？
   - 其他？

2. VPN服务器信息：
   - 服务器地址
   - 配置文件

3. VPN内网地址：
   - 连接后的IP范围
```

---

## 🔍 快速检查命令

### 检查本机网络

```bash
# 查看所有网络接口
ip addr show

# 查看路由表
ip route show

# 查看公网IP
curl ifconfig.me
curl ipinfo.io/ip
```

### 检查端口监听

```bash
# 查看当前监听的端口
netstat -tlnp | grep -E "(8080|8765|80|443)"

# 或使用ss
ss -tlnp | grep -E "(8080|8765|80|443)"
```

### 检查防火墙

```bash
# UFW防火墙
sudo ufw status

# iptables规则
sudo iptables -L -n

# firewalld
sudo firewall-cmd --list-all
```

### 测试外网访问

```bash
# 从外部测试（需要另一台设备）
# 替换为你的公网IP或域名

curl http://你的公网IP:8080/health
curl https://你的公网IP/health
curl http://你的域名:8080/health
```

---

## 📝 配置模板

### 模板1：直接公网IP访问

```ini
# 如果使用公网IP访问，更新前端配置

# 公网IP
PUBLIC_IP=你的公网IP

# 端口映射
HTTP_PORT=8080
WS_PORT=8765
HTTPS_PORT=443

# 访问地址
HTTP_URL=http://你的公网IP:8080/web/ui/index.html
WS_URL=ws://你的公网IP:8765
HTTPS_URL=https://你的公网IP/web/ui/index.html
WSS_URL=wss://你的公网IP
```

### 模板2：域名访问

```ini
# 如果使用域名访问

# 域名
DOMAIN=你的域名.com

# SSL证书
CERT_PATH=/etc/letsencrypt/live/你的域名.com/fullchain.pem
KEY_PATH=/etc/letsencrypt/live/你的域名.com/privkey.pem

# 访问地址
HTTP_URL=http://你的域名.com:8080/web/ui/index.html
HTTPS_URL=https://你的域名.com/web/ui/index.html
WSS_URL=wss://你的域名.com
```

### 模板3：FRP内网穿透

```ini
# FRP配置

[common]
server_addr = frp服务器地址
server_port = 7000
token = 你的token

[zhineng_bridge_http]
type = tcp
local_ip = 127.0.0.1
local_port = 8080
remote_port = 8080

[zhineng_bridge_https]
type = tcp
local_ip = 127.0.0.1
local_port = 443
remote_port = 443

[zhineng_bridge_websocket]
type = tcp
local_ip = 127.0.0.1
local_port = 8765
remote_port = 8765
```

---

## ✅ 下一步

**请提供以下信息之一：**

1. **公网IP + 端口映射**
2. **域名 + SSL证书**
3. **FRP服务器信息**
4. **VPN配置**

**然后我将帮你：**
- 配置相应的访问方式
- 更新前端配置
- 测试公网访问
- 完成部署

---

**信息收集模板：**

```
访问方式：[直接公网IP / 域名 / FRP / VPN]

如果是公网IP：
  公网IP：________
  HTTP端口：________
  WebSocket端口：________
  HTTPS端口：________

如果是域名：
  域名：________
  是否有SSL证书：[是/否]
  证书路径：________

如果是FRP：
  服务器地址：________
  服务器端口：________
  Token：________

其他说明：
________
```

---

**文档版本：** v1.0
**创建日期：** 2026-03-29
