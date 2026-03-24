# 智桥（Zhineng-bridge）使用示例

本目录包含智桥的各种使用示例和配置文件。

## 目录

- [基础使用示例](#基础使用示例)
- [Cursor IDE 配置](#cursor-ide-配置)
- [Claude Desktop 配置](#claude-desktop-配置)

## 基础使用示例

### `basic_usage.py`

展示如何使用 Python API 与智桥交互的基本示例。

#### 运行示例

```bash
# 确保 relay-server 正在运行
cd /home/ai/zhineng-bridge/relay-server
python3 start_server.py

# 在另一个终端运行示例
python3 examples/basic_usage.py
```

#### 示例内容

1. **示例 1: 基本连接** - 连接到服务器并发送心跳
2. **示例 2: 列出会话** - 获取所有会话列表
3. **示例 3: 创建和删除会话** - 完整的会话生命周期
4. **示例 4: 多个会话** - 同时管理多个工具会话
5. **示例 5: 使用 SessionManager** - 直接使用 SessionManager API

#### 代码结构

```python
class ZhinengBridgeClient:
    """智桥客户端类"""

    async def connect()           # 连接到服务器
    async def disconnect()        # 断开连接
    async def list_sessions()     # 列出会话
    async def create_session()    # 创建会话
    async def stop_session()      # 停止会话
    async def delete_session()    # 删除会话
    async def ping()              # 发送心跳
```

#### 输出示例

```
=== 示例 1: 基本连接 ===

📡 连接到服务器: ws://localhost:8765
✅ 连接成功
📤 发送消息: ping
📥 收到响应: pong
⏹️  已断开连接

=== 示例 2: 列出会话 ===

📡 连接到服务器: ws://localhost:8765
✅ 连接成功
📤 发送消息: list_sessions
📥 收到响应: sessions_list

会话列表: {'type': 'sessions_list', 'sessions': [], 'count': 0}
会话数量: 0
⏹️  已断开连接
```

## Cursor IDE 配置

### `cursor_config.md`

详细的 Cursor IDE MCP 配置指南。

#### 前置条件

- 已安装 Cursor IDE
- 已完成智桥安装
- relay-server 正在运行

#### 快速配置

**macOS**: `~/Library/Application Support/Cursor/User/mcp.json`

```json
{
  "mcpServers": {
    "zhineng-bridge": {
      "command": "python3",
      "args": [
        "/home/ai/zhineng-bridge/relay-server/mcp_server.py"
      ],
      "env": {
        "ZHINENG_BRIDGE_HOST": "localhost",
        "ZHINENG_BRIDGE_PORT": "8765"
      }
    }
  }
}
```

**Windows**: `%APPDATA%\Cursor\User\mcp.json`

**Linux**: `~/.config/Cursor/User/mcp.json`

#### 配置完成后

1. 重启 Cursor IDE
2. 在聊天框中使用智桥：
   ```
   请使用 zhineng-bridge 创建一个 Crush 会话，执行 --help 命令
   ```

#### 更多信息

详见 [cursor_config.md](./cursor_config.md)

## Claude Desktop 配置

### `claude_config.md`

详细的 Claude Desktop MCP 配置指南。

#### 前置条件

- 已安装 Claude Desktop
- 已完成智桥安装
- relay-server 正在运行

#### 快速配置

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "zhineng-bridge": {
      "command": "python3",
      "args": [
        "/home/ai/zhineng-bridge/relay-server/mcp_server.py"
      ],
      "env": {
        "ZHINENG_BRIDGE_HOST": "localhost",
        "ZHINENG_BRIDGE_PORT": "8765"
      }
    }
  }
}
```

#### 配置完成后

1. 重启 Claude Desktop
2. 在对话中使用智桥：
   ```
   请使用智桥列出所有可用的 AI 工具
   ```

#### 更多信息

详见 [claude_config.md](./claude_config.md)

## 运行示例

### 前置准备

```bash
# 1. 克隆仓库（如果还没有）
git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge

# 2. 安装依赖
pip install websockets asyncio

# 3. 启动 relay-server
cd relay-server
python3 start_server.py

# 4. （可选）启动 session_manager
cd ../phase1/session_manager
python3 start_manager.py
```

### 运行 Python 示例

```bash
# 运行基础使用示例
python3 examples/basic_usage.py

# 运行特定示例（需要修改代码）
python3 examples/basic_usage.py  # 将执行所有示例
```

### 测试 MCP 配置

#### Cursor IDE

1. 按照 `cursor_config.md` 配置 MCP
2. 重启 Cursor
3. 在聊天中输入：
   ```
   使用 zhineng-bridge 发送 ping
   ```

#### Claude Desktop

1. 按照 `claude_config.md` 配置 MCP
2. 重启 Claude Desktop
3. 在对话中输入：
   ```
   使用智桥发送 ping
   ```

## 常见问题

### Q1: 运行示例时报错 "Connection refused"

**A**: 确保 relay-server 正在运行：
```bash
ps aux | grep relay-server
```

如果没运行，启动它：
```bash
cd /home/ai/zhineng-bridge/relay-server
python3 start_server.py
```

### Q2: Cursor/Claude 无法连接到智桥

**A**: 检查以下几点：
1. relay-server 是否正在运行（端口 8765）
2. 配置文件路径是否正确
3. Python 路径是否正确
4. 端口号是否正确

详见对应配置文档的故障排查部分。

### Q3: 示例代码需要修改哪些参数？

**A**: 根据您的环境修改：
```python
# basic_usage.py
client = ZhinengBridgeClient(
    host="localhost",  # 修改为您的服务器地址
    port=8765          # 修改为您的服务器端口
)
```

### Q4: 可以在 Windows 上运行吗？

**A**: 可以，但需要修改：
- Python 命令：`python3` → `python`
- 文件路径：`/home/ai/` → `C:\Users\YourName\`

### Q5: 如何查看更详细的日志？

**A**: 启用调试模式：
```python
# basic_usage.py
# 添加调试打印
import logging
logging.basicConfig(level=logging.DEBUG)
```

或者修改配置文件：
```json
{
  "env": {
    "ZHINENG_BRIDGE_DEBUG": "true"
  }
}
```

## 扩展示例

### 创建新的示例

1. 复制 `basic_usage.py`：
   ```bash
   cp examples/basic_usage.py examples/my_example.py
   ```

2. 修改示例代码

3. 运行：
   ```bash
   python3 examples/my_example.py
   ```

### 提交示例

如果您创建了有用的示例，欢迎提交 PR！

## 贡献指南

我们欢迎新的示例和改进！

1. Fork 本仓库
2. 创建新的示例文件
3. 添加文档说明
4. 提交 PR

详细贡献指南请参见 [CONTRIBUTING.md](../CONTRIBUTING.md)（如果存在）

## 许可证

MIT License - 与智桥主项目相同

## 相关链接

- [智桥主页](https://github.com/guangda88/zhineng-bridge)
- [智桥使用指南](../USAGE_GUIDE.md)
- [智桥快速开始](../QUICKSTART.md)
- [智桥故障排查](../TROUBLESHOOTING.md)
- [智桥 API 文档](../docs/API.md)

---

**版本**: 1.0.0
**更新时间**: 2026-03-24
