# Cursor IDE 配置示例

本示例展示如何在 Cursor IDE 中配置智桥（Zhineng-bridge）作为 MCP 服务器。

## 前置条件

1. 安装 Cursor IDE
2. 已完成智桥的安装和配置
3. 确保 relay-server 和 session_manager 正在运行

## 配置步骤

### 1. 创建 MCP 配置文件

在 Cursor 的配置目录中创建或编辑 MCP 配置文件：

**macOS**: `~/Library/Application Support/Cursor/User/mcp.json`
**Windows**: `%APPDATA%\Cursor\User\mcp.json`
**Linux**: `~/.config/Cursor/User/mcp.json`

### 2. 添加智桥 MCP 服务器配置

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

### 3. 使用环境变量配置（推荐）

也可以使用环境变量来管理配置：

```json
{
  "mcpServers": {
    "zhineng-bridge": {
      "command": "python3",
      "args": [
        "${ZHINENG_BRIDGE_PATH}/relay-server/mcp_server.py"
      ],
      "env": {
        "ZHINENG_BRIDGE_PATH": "${HOME}/zhineng-bridge",
        "ZHINENG_BRIDGE_HOST": "${ZHINENG_BRIDGE_HOST:-localhost}",
        "ZHINENG_BRIDGE_PORT": "${ZHINENG_BRIDGE_PORT:-8765}"
      }
    }
  }
}
```

### 4. 完整配置示例

```json
{
  "mcpServers": {
    "zhineng-bridge": {
      "command": "python3",
      "args": [
        "/home/ai/zhineng-bridge/relay-server/mcp_server.py",
        "--host", "localhost",
        "--port", "8765"
      ],
      "env": {
        "PYTHONPATH": "/home/ai/zhineng-bridge",
        "ZHINENG_BRIDGE_SESSION_DIR": "/tmp/zhineng-bridge-sessions"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/ai/zhineng-bridge"
      ]
    }
  }
}
```

## 配置说明

### 参数说明

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `command` | string | 要执行的命令 | `python3` |
| `args` | array | 命令参数 | MCP 服务器路径 |
| `env` | object | 环境变量 | 可选 |

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ZHINENG_BRIDGE_HOST` | WebSocket 服务器主机 | `localhost` |
| `ZHINENG_BRIDGE_PORT` | WebSocket 服务器端口 | `8765` |
| `ZHINENG_BRIDGE_PATH` | 智桥项目路径 | - |
| `ZHINENG_BRIDGE_SESSION_DIR` | 会话存储目录 | `/tmp/zhineng-bridge-sessions` |

## 使用示例

### 在 Cursor 中使用智桥

配置完成后，重启 Cursor，然后在聊天框中使用智桥：

```
请使用 zhineng-bridge 创建一个 Crush 会话，执行 --help 命令
```

智桥会返回执行结果，Cursor 会自动解析并展示。

### 支持的操作

- **列出工具**: 查看所有可用的 AI 工具
- **创建会话**: 为指定工具创建会话
- **执行命令**: 在会话中执行命令
- **查看输出**: 获取命令执行输出
- **删除会话**: 清理不再需要的会话

### 示例对话

**用户**:
```
帮我创建一个 Cursor 工具会话，执行 list-projects 命令
```

**智桥响应**:
```json
{
  "session_id": "abc123-def456-ghi789",
  "tool_name": "cursor",
  "status": "running",
  "output": "Project List:\n1. MyProject\n2. DemoApp\n3. TestSuite"
}
```

## 高级配置

### 自定义端口

如果 relay-server 使用了不同的端口：

```json
{
  "mcpServers": {
    "zhineng-bridge": {
      "command": "python3",
      "args": [
        "/home/ai/zhineng-bridge/relay-server/mcp_server.py"
      ],
      "env": {
        "ZHINENG_BRIDGE_PORT": "9000"
      }
    }
  }
}
```

### 多实例配置

如果需要连接多个智桥实例：

```json
{
  "mcpServers": {
    "zhineng-bridge-local": {
      "command": "python3",
      "args": [
        "/home/ai/zhineng-bridge/relay-server/mcp_server.py"
      ],
      "env": {
        "ZHINENG_BRIDGE_PORT": "8765"
      }
    },
    "zhineng-bridge-remote": {
      "command": "python3",
      "args": [
        "/home/ai/zhineng-bridge/relay-server/mcp_server.py"
      ],
      "env": {
        "ZHINENG_BRIDGE_HOST": "192.168.1.100",
        "ZHINENG_BRIDGE_PORT": "8765"
      }
    }
  }
}
```

### 调试模式

启用调试日志：

```json
{
  "mcpServers": {
    "zhineng-bridge": {
      "command": "python3",
      "args": [
        "/home/ai/zhineng-bridge/relay-server/mcp_server.py",
        "--debug"
      ],
      "env": {
        "ZHINENG_BRIDGE_DEBUG": "true"
      }
    }
  }
}
```

## 故障排查

### 问题 1: 连接失败

**症状**: Cursor 报错 "无法连接到 MCP 服务器"

**解决方案**:
1. 检查 relay-server 是否正在运行：
   ```bash
   ps aux | grep relay-server
   ```

2. 检查端口是否正确：
   ```bash
   netstat -an | grep 8765
   ```

3. 查看配置文件中的路径是否正确

### 问题 2: 权限错误

**症状**: 报错 "Permission denied"

**解决方案**:
1. 确保配置文件路径正确
2. 检查 Python 脚本是否有执行权限：
   ```bash
   chmod +x /home/ai/zhineng-bridge/relay-server/mcp_server.py
   ```

### 问题 3: 模块导入错误

**症状**: 报错 "ModuleNotFoundError"

**解决方案**:
1. 确保 PYTHONPATH 设置正确：
   ```json
   "env": {
     "PYTHONPATH": "/home/ai/zhineng-bridge"
   }
   ```

2. 确保依赖已安装：
   ```bash
   pip install websockets asyncio
   ```

## 验证配置

### 1. 检查 MCP 服务器

在 Cursor 中，打开设置 → MCP，查看 "zhineng-bridge" 是否显示为已连接。

### 2. 测试基本功能

在 Cursor 聊天中输入：
```
使用 zhineng-bridge 发送 ping
```

如果看到 "pong" 响应，说明配置成功。

### 3. 测试会话创建

```
使用 zhineng-bridge 创建一个测试会话
```

应该能看到会话 ID 和状态。

## 最佳实践

1. **使用环境变量**: 避免在配置中硬编码路径和端口
2. **定期重启**: 如果遇到问题，重启 Cursor
3. **查看日志**: 检查 Cursor 的 MCP 日志
4. **保持更新**: 定期更新智桥到最新版本
5. **资源清理**: 及时删除不需要的会话

## 相关链接

- [智桥使用指南](../USAGE_GUIDE.md)
- [智桥快速开始](../QUICKSTART.md)
- [智桥故障排查](../TROUBLESHOOTING.md)
- [Cursor MCP 文档](https://docs.cursor.sh/mcp)

---

**版本**: 1.0.0
**更新时间**: 2026-03-24
