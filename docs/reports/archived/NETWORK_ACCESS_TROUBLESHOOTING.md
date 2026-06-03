# 网络访问问题解决方案

## 问题描述
- **主机地址**: 100.66.1.8, 10.113.22.99
- **网络状态**: ✅ 可以 ping 通
- **服务状态**: ❌ 无法访问服务 (8080, 8765)

## 诊断结果

### ✅ 本地测试通过
从服务器本身测试，所有端口都可以访问：
- 127.0.0.1:8080 ✅
- 127.0.0.1:8765 ✅
- 10.113.22.99:8080 ✅
- 10.113.22.99:8765 ✅
- 100.66.1.8:8080 ✅
- 100.66.1.8:8765 ✅

### 网络接口
服务器有多个网络接口：
- `enp4s0`: 192.168.2.1 (本地网络)
- `enp5s0`: 192.168.31.99 (本地网络)
- `ztcdcgcbxp`: 10.113.22.99 (ZeroTier 虚拟网络)
- `NodeBabyLink`: 100.66.1.8 (另一个网络接口)

### 🔍 问题分析
1. **服务器监听**: ✅ 监听在 `0.0.0.0` (所有接口)
2. **本地访问**: ✅ 可以从服务器本身访问所有接口
3. **外部访问**: ❌ 从外部无法访问

**结论**: 问题很可能是**防火墙阻止了外部访问**

---

## 解决方案

### 方案 1: 使用 UFW 开放端口 (推荐)

```bash
# 检查 UFW 状态
sudo ufw status

# 开放端口
sudo ufw allow 8080/tcp
sudo ufw allow 8765/tcp

# 重新加载防火墙规则
sudo ufw reload

# 验证规则
sudo ufw status numbered
```

### 方案 2: 使用 iptables 开放端口

```bash
# 允许访问 8080 端口
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# 允许访问 8765 端口
sudo iptables -A INPUT -p tcp --dport 8765 -j ACCEPT

# 保存规则
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

### 方案 3: 允许来自特定网络的访问

如果只想允许来自特定网络的访问：

```bash
# 允许来自 10.113.22.0/24 网络的访问
sudo ufw allow from 10.113.22.0/24 to any port 8080
sudo ufw allow from 10.113.22.0/24 to any port 8765

# 允许来自 100.66.1.0/24 网络的访问
sudo ufw allow from 100.66.1.0/24 to any port 8080
sudo ufw allow from 100.66.1.0/24 to any port 8765
```

### 方案 4: 临时关闭防火墙 (仅用于测试)

**⚠️ 注意**: 这会降低系统安全性，仅用于诊断问题

```bash
# 关闭 UFW
sudo ufw disable

# 测试访问
# 测试完成后重新启用
sudo ufw enable
```

---

## 验证步骤

### 1. 检查防火墙规则

```bash
# 查看 UFW 规则
sudo ufw status verbose

# 查看 iptables 规则
sudo iptables -L -n -v
```

### 2. 测试端口监听

```bash
# 检查端口监听状态
sudo ss -tlnp | grep -E "8080|8765"

# 或者使用 lsof
sudo lsof -i :8080
sudo lsof -i :8765
```

### 3. 从外部测试访问

```bash
# 从另一台机器上测试
telnet 10.113.22.99 8080
telnet 100.66.1.8 8080

# 或者使用 nc
nc -zv 10.113.22.99 8080
nc -zv 100.66.1.8 8080
```

### 4. 测试 HTTP 访问

```bash
# 从浏览器或 curl 测试
curl http://10.113.22.99:8080/health
curl http://100.66.1.8:8080/health
```

---

## 常见问题排查

### 问题 1: UFW 未安装

```bash
# 安装 UFW
sudo apt update
sudo apt install ufw -y

# 启用 UFW
sudo ufw enable
```

### 问题 2: 防火墙规则冲突

```bash
# 重置 UFW 到默认状态
sudo ufw --force reset

# 重新配置
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 8080/tcp
sudo ufw allow 8765/tcp
sudo ufw enable
```

### 问题 3: Docker 防火墙干扰

如果使用了 Docker，可能会影响防火墙规则：

```bash
# 检查 Docker 是否在运行
sudo systemctl status docker

# 如果 Docker 干扰了防火墙，可以考虑：
# 1. 停止 Docker 测试
sudo systemctl stop docker

# 2. 或者在 Docker 配置中禁用 iptables
# 编辑 /etc/docker/daemon.json
# 添加: { "iptables": false }
```

### 问题 4: 网络接口配置问题

检查网络接口是否正确配置：

```bash
# 查看网络接口配置
ip addr show

# 检查路由
ip route show

# 测试网络连接
ping -c 3 10.113.22.99
ping -c 3 100.66.1.8
```

---

## 快速诊断脚本

如果问题仍然存在，可以运行诊断脚本：

```bash
cd /home/ai/zhibridge
python3 scripts/diagnose_network.py
```

---

## 安全建议

1. **最小权限原则**: 只开放必要的端口
2. **限制访问源**: 只允许可信网络的访问
3. **定期审计**: 定期检查防火墙规则
4. **日志监控**: 启用防火墙日志以监控可疑活动

---

## 联系支持

如果以上方案都无法解决问题，请收集以下信息：

1. 防火墙规则: `sudo ufw status` 或 `sudo iptables -L -n`
2. 端口监听: `sudo ss -tlnp | grep -E "8080|8765"`
3. 网络接口: `ip addr show`
4. 路由表: `ip route show`
5. 错误日志: 查看服务器日志

---

**文档版本**: 1.0.0
**最后更新**: 2026-03-29
**作者**: Crush AI Assistant
