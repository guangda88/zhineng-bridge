# Claude Desktop 配置示例

本示例展示如何在 Claude Desktop 中配置智桥（Zhineng-bridge）作为 MCP 服务器。

## 前置条件

1. 安装 Claude Desktop
2. 已完成智桥的安装和配置
3. 确保 relay-server 和 session_manager 正在运行

## 配置步骤

### 1. 创建 MCP 配置文件

在 Claude Desktop 的配置目录中创建或编辑 MCP 配置文件：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

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

使用环境变量来管理配置，便于跨平台使用：

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

包含智桥和其他常用 MCP 服务器的完整配置：

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
    },
    "fetch": {
      "command": "uvx",
      "args": [
        "mcp-server-fetch"
      ]
    }
  }
}
```

### 5. 配置智桥工具访问

如果需要访问智桥的特定工具，可以添加工具级配置：

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
      },
      "allowedTools": [
        "list_tools",
        "create_session",
        "execute_command",
        "get_output",
        "delete_session"
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
| `allowedTools` | array | 允许使用的工具列表 | 所有工具 |

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ZHINENG_BRIDGE_HOST` | WebSocket 服务器主机 | `localhost` |
| `ZHINENG_BRIDGE_PORT` | WebSocket 服务器端口 | `8765` |
| `ZHINENG_BRIDGE_PATH` | 智桥项目路径 | - |
| `ZHINENG_BRIDGE_SESSION_DIR` | 会话存储目录 | `/tmp/zhineng-bridge-sessions` |
| `ZHINENG_BRIDGE_DEBUG` | 调试模式 | `false` |
| `PYTHONPATH` | Python 模块路径 | 可选 |

## 使用示例

### 在 Claude Desktop 中使用智桥

配置完成后，重启 Claude Desktop，然后在对话中使用智桥：

```
请使用智桥创建一个 Crush 会话，执行 --help 命令
```

Claude 会调用智桥 MCP 服务器，返回执行结果。

### 常用操作

#### 1. 列出可用工具

```
使用智桥列出所有可用的 AI 工具
```

**响应示例**:
```
可用工具：
1. Crush - Charmbracelet 的 AI 编码工具
2. Claude Code - Anthropic 的 AI 编码工具
3. Cursor - Anysphere 的 AI IDE
4. iFlow CLI - 阿里巴巴的 AI 编码工具
5. Trae - 字节跳动的 AI 编码工具
6. Droid - Factory 的 AI 编码工具
7. OpenClaw - 开源 AI 编码工具
8. GitHub Copilot - GitHub 的 AI 编码助手
```

#### 2. 创建会话

```
使用智桥创建一个 Cursor 会话，参数为 --list-projects
```

**响应示例**:
```json
{
  "session_id": "abc123-def456-ghi789",
  "tool_name": "cursor",
  "args": ["--list-projects"],
  "status": "running",
  "created_at": "2026-03-24T10:00:00Z"
}
```

#### 3. 查看会话输出

```
使用智桥查看会话 abc123-def456-ghi789 的输出
```

**响应示例**:
```
会话输出：
Project List:
1. MyProject
2. DemoApp
3. TestSuite
```

#### 4. 列出所有会话

```
使用智桥列出所有活动会话
```

#### 5. 删除会话

```
使用智桥删除会话 abc123-def456-ghi789
```

### 复杂示例

#### 工作流自动化

```
帮我完成以下任务：
1. 使用智桥创建一个 Crush 会话
2. 执行 git status 命令
3. 查看输出结果
4. 清理会话
```

Claude 会自动调用智桥的 MCP 工具完成整个工作流。

#### 多工具协作

```
我想用智桥同时创建两个会话：
1. 一个 Cursor 会话执行代码分析
2. 一个 Crush 会话执行文件操作
然后比较两个工具的输出
```

## 高级配置

### 自定义端口

如果 relay-server 使用了非标准端口：

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

### 远程连接

连接到远程智桥服务器：

```json
{
  "mcpServers": {
    "zhineng-bridge": {
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

### 多实例配置

连接到多个智桥实例：

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

### 权限控制

限制智桥只能使用特定工具：

```json
{
  "mcpServers": {
    "zhineng-bridge": {
      "command": "python3",
      "args": [
        "/home/ai/zhineng-bridge/relay-server/mcp_server.py"
      ],
      "allowedTools": [
        "list_tools",
        "create_session",
        "get_output"
      ]
    }
  }
}
```

## 跨平台配置

### Windows 配置

```json
{
  "mcpServers": {
    "zhineng-bridge": {
      "command": "python",
      "args": [
        "C:\\Users\\YourName\\zhineng-bridge\\relay-server\\mcp_server.py"
      ],
      "env": {
        "ZHINENG_BRIDGE_HOST": "localhost",
        "ZHINENG_BRIDGE_PORT": "8765"
      }
    }
  }
}
```

### macOS 配置

```json
{
  "mcpServers": {
    "zhineng-bridge": {
      "command": "python3",
      "args": [
        "/Users/yourname/zhineng-bridge/relay-server/mcp_server.py"
      ],
      "env": {
        "ZHINENG_BRIDGE_HOST": "localhost",
        "ZHINENG_BRIDGE_PORT": "8765"
      }
    }
  }
}
```

## 故障排查

### 问题 1: 连接失败

**症状**: Claude Desktop 报错 "无法连接到 MCP 服务器"

**解决方案**:
1. 检查 relay-server 是否正在运行：
   ```bash
   ps aux | grep relay-server
   ```

2. 检查端口是否正确：
   ```bash
   netstat -an | grep 8765
   ```

3. 查看配置文件路径是否正确：
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### 问题 2: Python 找不到

**症状**: 报错 "python3: command not found"

**解决方案**:
1. 确保 Python 3 已安装：
   ```bash
   python3 --version
   ```

2. 使用完整 Python 路径：
   ```json
   {
     "command": "/usr/local/bin/python3"
   }
   ```

3. 或使用 `python` 而不是 `python3`：
   ```json
   {
     "command": "python"
   }
   ```

### 问题 3: 权限错误

**症状**: 报错 "Permission denied"

**解决方案**:
1. 确保配置文件有写入权限：
   ```bash
   chmod 644 ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. 确保 MCP 服务器脚本有执行权限：
   ```bash
   chmod +x /home/ai/zhineng-bridge/relay-server/mcp_server.py
   ```

### 问题 4: 模块导入错误

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

3. 检查 Python 版本：
   ```bash
   python3 --version  # 应该 >= 3.8
   ```

### 问题 5: 工具不可用

**症状**: Claude 说 "智桥工具不可用"

**解决方案**:
1. 重启 Claude Desktop
2. 检查 MCP 配置文件格式是否正确（有效的 JSON）
3. 查看日志文件：
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\Logs\`

## 验证配置

### 1. 检查 MCP 服务器状态

在 Claude Desktop 中，打开设置 → MCP，查看 "zhineng-bridge" 是否显示为已连接。

### 2. 测试基本连接

在 Claude 对话中输入：
```
使用智桥发送 ping
```

如果看到 "pong" 响应，说明连接正常。

### 3. 测试工具列表

```
使用智桥列出所有可用工具
```

应该能看到 8 个 AI 工具的列表。

### 4. 测试会话创建

```
使用智桥创建一个测试会话，工具为 crush，参数为 --help
```

应该能看到会话创建成功的响应。

## 最佳实践

### 1. 使用环境变量

避免在配置中硬编码路径和端口，使用环境变量：
```bash
export ZHINENG_BRIDGE_HOST=localhost
export ZHINENG_BRIDGE_PORT=8765
export ZHINENG_BRIDGE_PATH=$HOME/zhineng-bridge
```

### 2. 版本管理

在配置中记录智桥版本：
```json
{
  "mcpServers": {
    "zhineng-bridge": {
      "command": "python3",
      "args": [
        "/home/ai/zhineng-bridge/relay-server/mcp_server.py"
      ],
      "version": "1.0.0"
    }
  }
}
```

### 3. 定期重启

如果遇到问题，重启 Claude Desktop。

### 4. 监控日志

定期查看 Claude 和智桥的日志文件。

### 5. 资源清理

及时删除不需要的会话，避免资源浪费：
```
使用智桥列出所有会话，并删除已经完成的会话
```

### 6. 错误处理

在使用智桥时，添加错误处理：
```
尝试使用智桥创建会话，如果失败请告诉我错误信息
```

## 性能优化

### 1. 减少会话数量

避免创建过多的并发会话，建议最多同时维护 3-5 个活动会话。

### 2. 使用缓存

智桥会自动缓存常用操作，减少重复请求。

### 3. 批量操作

一次请求中包含多个操作：
```
使用智桥：1. 创建会话，2. 执行命令，3. 查看输出，4. 删除会话
```

## 安全建议

1. **不要暴露敏感信息**: 不要在配置文件中存储密码或 API 密钥
2. **限制工具权限**: 只允许使用必要的工具
3. **定期更新**: 保持智桥和 Claude Desktop 更新
4. **监控日志**: 定期检查日志文件，发现异常活动

## 相关链接

- [智桥使用指南](../USAGE_GUIDE.md)
- [智桥快速开始](../QUICKSTART.md)
- [智桥故障排查](../TROUBLESHOOTING.md)
- [Claude Desktop MCP 文档](https://docs.anthropic.com/claude/docs/mcp)
- [Cursor 配置示例](./cursor_config.md)

---

**版本**: 1.0.0
**更新时间**: 2026-03-24
