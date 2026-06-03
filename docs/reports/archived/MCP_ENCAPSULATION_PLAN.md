# Crush MCP 封装实施计划

**日期**: 2026-04-07  
**状态**: 规划阶段  
**目标**: 将 Crush 核心工具封装为 MCP Server，供任意 AI 客户端复用

---

## 一、架构设计

```
┌─────────────────────────────────────────────┐
│              MCP Client (任意 AI)             │
│  Claude / Copilot / Cursor / Trae / iFlow   │
└──────────────────┬──────────────────────────┘
                   │ MCP Protocol (stdio/SSE)
┌──────────────────▼──────────────────────────┐
│            Crush MCP Server                  │
│                                              │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Phase 1     │  │ Phase 2              │  │
│  │ fs.read     │  │ code.search          │  │
│  │ fs.write    │  │                      │  │
│  │ fs.search   │  │ Phase 3              │  │
│  │ shell.run   │  │ lsp.diagnostics      │  │
│  │             │  │ lsp.references       │  │
│  └─────────────┘  └──────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │ Security Layer                       │    │
│  │ - 命令黑名单 (sudo, rm -rf, etc.)    │    │
│  │ - 路径沙箱 (限制工作目录)            │    │
│  │ - 审计日志 (所有操作记录)            │    │
│  │ - 速率限制 (防滥用)                  │    │
│  └──────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### 技术栈

- **语言**: Python 3.10+（与 zhineng-bridge 一致）
- **MCP SDK**: `mcp` 官方 Python SDK
- **传输**: stdio（本地）+ SSE（远程，可选）
- **包管理**: pip / uv

---

## 二、Phase 1 — 核心文件操作 + Shell

### 2.1 工具定义

#### `fs.read` — 文件/目录读取

```python
@mcp.tool()
async def fs_read(
    path: str,                    # 文件或目录路径
    mode: str = "file",           # "file" | "dir" | "glob"
    pattern: str = "*",           # glob 模式 (mode="glob" 时)
    offset: int = 0,              # 起始行号 (mode="file" 时)
    limit: int = 2000,            # 最大行数
    encoding: str = "utf-8",      # 文件编码
) -> dict:
    """
    读取文件内容或目录列表。
    
    mode="file": 读取文件内容（含行号）
    mode="dir":  列出目录树结构
    mode="glob": 按模式匹配文件列表
    """
```

**合并来源**: view + ls + glob

#### `fs.write` — 文件写入/编辑

```python
@mcp.tool()
async def fs_write(
    path: str,                    # 目标文件路径
    operation: str = "create",    # "create" | "edit" | "multi_edit"
    content: str = "",            # 完整内容 (operation="create")
    old_string: str = "",         # 替换目标 (operation="edit")
    new_string: str = "",         # 替换内容 (operation="edit")
    edits: list = [],             # 批量编辑 (operation="multi_edit")
) -> dict:
    """
    创建或编辑文件。
    
    operation="create": 创建/覆盖文件
    operation="edit": 精确字符串替换
    operation="multi_edit": 批量替换
    """
```

**合并来源**: write + edit + multiedit

#### `fs.search` — 内容搜索

```python
@mcp.tool()
async def fs_search(
    pattern: str,                 # 搜索模式（正则或字面量）
    path: str = ".",              # 搜索目录
    literal: bool = False,        # True=精确匹配，False=正则
    include: str = "",            # 文件过滤 "*.py"
    max_results: int = 100,       # 最大结果数
) -> dict:
    """
    在文件内容中搜索模式。
    返回匹配文件列表及上下文。
    """
```

**合并来源**: grep

#### `shell.run` — 命令执行

```python
@mcp.tool()
async def shell_run(
    command: str,                 # 要执行的命令
    working_dir: str = "",        # 工作目录
    timeout: int = 60,            # 超时秒数
    background: bool = false,     # 是否后台运行
) -> dict:
    """
    执行 shell 命令（沙箱化）。
    
    安全限制：
    - 禁止命令: sudo, su, rm -rf /, mkfs, dd, mount, ...
    - 路径限制: 仅允许工作目录及其子目录
    - 超时保护: 默认 60 秒
    """
```

**来源**: bash（带安全增强）

### 2.2 安全层设计

```python
# shell 命令黑名单
BLOCKED_COMMANDS = [
    "sudo", "su", "doas",               # 权限提升
    "rm -rf /", "mkfs", "dd if=",       # 破坏性操作
    "curl", "wget", "nc", "ssh",        # 网络工具（防数据外泄）
    "apt", "yum", "pacman", "pip",      # 包管理（防篡改环境）
    "systemctl", "service",             # 系统服务
    "crontab", "at",                    # 定时任务
    "iptables", "ufw",                  # 防火墙
]

# 路径沙箱
ALLOWED_PATHS = [
    "${WORKSPACE_ROOT}",                # 工作区根目录
]

# 速率限制
RATE_LIMIT = {
    "calls_per_minute": 30,
    "calls_per_hour": 200,
    "shell_per_minute": 10,
}
```

### 2.3 项目结构

```
crush-mcp-server/
├── pyproject.toml           # 项目元数据 + 依赖
├── README.md                # 使用说明
├── src/
│   └── crush_mcp/
│       ├── __init__.py
│       ├── server.py        # MCP Server 入口
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── fs_read.py   # fs.read 实现
│       │   ├── fs_write.py  # fs.write 实现
│       │   ├── fs_search.py # fs.search 实现
│       │   └── shell.py     # shell.run 实现
│       ├── security/
│       │   ├── __init__.py
│       │   ├── command_filter.py  # 命令过滤
│       │   ├── path_sandbox.py    # 路径沙箱
│       │   └── rate_limiter.py    # 速率限制
│       └── config.py        # 配置管理
├── tests/
│   ├── test_fs_read.py
│   ├── test_fs_write.py
│   ├── test_fs_search.py
│   ├── test_shell.py
│   └── test_security.py
└── examples/
    ├── claude_desktop_config.json   # Claude Desktop 配置
    ├── cursor_config.json           # Cursor 配置
    └── copilot_config.json          # Copilot 配置
```

---

## 三、Phase 2 — 代码搜索

### `code.search` — Sourcegraph 搜索

```python
@mcp.tool()
async def code_search(
    query: str,                   # Sourcegraph 语法查询
    max_results: int = 10,        # 最大结果数
    context_lines: int = 10,      # 上下文行数
) -> dict:
    """
    使用 Sourcegraph 搜索公共代码仓库。
    支持正则、文件过滤、仓库过滤等。
    """
```

---

## 四、Phase 3 — LSP 集成

### `lsp.diagnostics` + `lsp.references`

需要额外管理 LSP 服务器进程，复杂度高。作为可选扩展。

---

## 五、实施步骤

### Step 1: 项目初始化 (0.5h)

```bash
mkdir -p crush-mcp-server/src/crush_mcp/{tools,security}
mkdir -p crush-mcp-server/{tests,examples}
cd crush-mcp-server
```

### Step 2: pyproject.toml (0.5h)

```toml
[project]
name = "crush-mcp-server"
version = "0.1.0"
description = "Crush AI Assistant MCP Server - 文件操作与命令执行"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]
```

### Step 3: 实现安全层 (1h)
- command_filter.py
- path_sandbox.py
- rate_limiter.py

### Step 4: 实现工具 (2h)
- fs_read.py (合并 view/ls/glob)
- fs_write.py (合并 edit/multiedit/write)
- fs_search.py (grep)
- shell.py (bash + 安全层)

### Step 5: Server 入口 (0.5h)
- server.py — 注册所有工具

### Step 6: 测试 (1h)
- 单元测试覆盖每个工具
- 安全测试（注入、越权）

### Step 7: 客户端配置示例 (0.5h)
- Claude Desktop
- Cursor
- Copilot

**预估总工时**: ~6h

---

## 六、客户端集成示例

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "crush": {
      "command": "python",
      "args": ["-m", "crush_mcp.server"],
      "env": {
        "WORKSPACE_ROOT": "/path/to/project"
      }
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)

```json
{
  "servers": {
    "crush": {
      "command": "python",
      "args": ["-m", "crush_mcp.server"],
      "env": {
        "WORKSPACE_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

---

## 七、与现有 MCP 工具的关系

| 现有 MCP Server | 功能 | 本计划 | 关系 |
|-----------------|------|--------|------|
| `mcp_zai-mcp-server` | 8 个多模态 AI 工具 | 不涉及 | **互补**，各自独立 |
| `mcp_zread` | 3 个 GitHub 仓库工具 | 不涉及 | **互补** |
| `mcp_web-reader` | 网页读取 | 不涉及 | **互补** |
| `mcp_web-search` | 网页搜索 | 不涉及 | **互补** |
| **crush-mcp-server (新)** | 4 个文件/Shell 工具 | Phase 1 | **新增**，填补文件操作空白 |

最终状态：5 个独立 MCP Server，共 15+ 工具，覆盖文件、Shell、多模态、代码搜索、网页访问。

---

## 八、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Shell 命令注入 | Critical | 命令黑名单 + 路径沙箱 + 审计日志 |
| 文件越权读写 | High | 路径白名单 + workspace 根目录限制 |
| 速率限制绕过 | Medium | 令牌桶算法 + IP 级限制 |
| MCP SDK 版本变动 | Low | 锁定版本 + 兼容性测试 |

---

**下一步**: 等待确认后开始 Phase 1 实现。
