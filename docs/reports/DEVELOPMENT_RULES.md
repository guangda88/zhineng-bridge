# 智桥（Zhineng-bridge）项目开发规则

**版本**: 1.0.0
**日期**: 2026-03-25
**状态**: 生效中

---

## 目录

1. [项目结构规范](#1-项目结构规范)
2. [代码编写规范](#2-代码编写规范)
3. [类型系统](#3-类型系统)
4. [测试规范](#4-测试规范)
5. [Git工作流规范](#5-git工作流规范)
6. [日志规范](#6-日志规范)
7. [禁止事项](#7-禁止事项)

---

## 1. 项目结构规范

### 1.1 目录结构

```
zhineng-bridge/
├── relay-server/          # WebSocket 中继服务器
│   ├── __init__.py
│   ├── server.py          # 主服务器
│   ├── config.py          # 配置管理
│   ├── models.py          # 数据模型
│   ├── logger.py          # 日志系统
│   ├── exceptions.py      # 异常定义
│   ├── metrics.py         # 性能指标
│   ├── auth.py            # 认证模块
│   ├── rate_limit.py      # 限流模块
│   └── start_server.py    # 启动脚本
├── phase1/                # 第一阶段功能
│   └── session_manager/   # 会话管理器
├── phase3/                # 第三阶段功能
│   └── storage/           # 存储模块
├── phase4/                # 第四阶段功能
├── mcp-server/            # MCP 服务器
├── web/                   # Web UI
├── tests/                 # 测试代码
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   ├── e2e/               # 端到端测试
│   └── performance/       # 性能测试
├── scripts/               # 工具脚本
├── docs/                  # 文档
├── config/                # 配置文件
├── CHANGELOG.md           # 变更日志
├── CONTRIBUTING.md        # 贡献指南
├── README.md              # 项目说明
└── DEVELOPMENT_RULES.md   # 本文件
```

### 1.2 文件命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| Python模块 | 小写+下划线 | `relay_server.py`, `session_manager.py` |
| 类名 | 大驼峰 | `CrushRelayServer`, `SessionManager` |
| 函数名 | 小写+下划线 | `create_session`, `handle_message` |
| 变量名 | 小写+下划线 | `session_id`, `max_connections` |
| 常量名 | 大写+下划线 | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| 私有成员 | 前缀下划线 | `_internal_method`, `_config` |

---

## 2. 代码编写规范

### 2.1 Python代码规范

遵循 **PEP 8** 风格：

```python
# 缩进：4空格
# 行长度：最大120字符（实际可读性优先）
# 导入顺序：标准库 -> 第三方库 -> 本地模块
```

### 2.2 类型注解规范

**新代码必须添加类型注解**：

```python
from typing import Dict, List, Optional, Any

# 正确：完整类型注解
def create_session(
    tool_name: str,
    args: Optional[List[str]] = None
) -> str:
    """创建新会话"""
    if args is None:
        args = []
    # 实现...

# 正确：返回类型注解
async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
    """处理消息"""
    # 实现...
```

### 2.3 文档字符串规范

**所有公共API必须有docstring**（Google风格）：

```python
def create_session(self, tool_name: str, args: Optional[List[str]] = None) -> str:
    """创建新会话

    Args:
        tool_name: 工具名称，如 "crush", "cursor"
        args: 工具参数列表，可选

    Returns:
        会话 ID (UUID 字符串)

    Raises:
        ValueError: 当工具名称无效时
        SessionManagerError: 当会话创建失败时

    Example:
        >>> session_id = create_session("crush", ["--help"])
        >>> print(session_id)
        a1b2c3d4-e5f6-7890-abcd-ef1234567890
    """
```

### 2.4 错误处理规范

```python
# 正确：捕获具体异常，记录上下文
import logging

logger = logging.getLogger(__name__)

try:
    session_id = self.manager.create_session(tool_name)
    return {"success": True, "session_id": session_id}
except InvalidToolNameError as e:
    logger.error(f"无效的工具名称: {tool_name}")
    return {"success": False, "error": f"无效的工具名称: {tool_name}"}
except SessionManagerError as e:
    logger.error(f"创建会话失败: {tool_name}, {e}", exc_info=True)
    return {"success": False, "error": str(e)}
```

### 2.5 代码复杂度限制

| 指标 | 建议值 | 硬性限制 |
|------|--------|----------|
| 函数行数 | < 50 | < 100 |
| 类行数 | < 300 | < 500 |
| 圈复杂度 | < 10 | < 15 |
| 参数数量 | < 5 | < 8 |

---

## 3. 类型系统

### 3.1 统一返回值类型（推荐）

使用字典类型的统一返回值：

```python
from typing import Dict, Any, Optional

def execute_command(self, command: str) -> Dict[str, Any]:
    """执行命令

    Returns:
        统一格式返回值:
        {
            "success": bool,      # 是否成功
            "data": Any,         # 返回数据
            "error": str | None  # 错误信息
        }
    """
    try:
        result = self._do_execute(command)
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}
```

### 3.2 统一异常体系

定义在 `relay-server/exceptions.py`：

```python
class ZhinengBridgeError(Exception):
    """智桥基础异常"""
    pass

class SessionManagerError(ZhinengBridgeError):
    """会话管理器异常"""
    pass

class InvalidToolNameError(ZhinengBridgeError):
    """无效工具名称异常"""
    pass

class ToolExecutionError(ZhinengBridgeError):
    """工具执行异常"""
    pass
```

---

## 4. 测试规范

### 4.1 测试目录结构

```
tests/
├── unit/              # 单元测试
│   ├── test_server.py
│   ├── test_config.py
│   └── test_models.py
├── integration/       # 集成测试
│   └── test_session_manager.py
├── e2e/              # 端到端测试
│   └── test_websocket.py
├── performance/      # 性能测试
│   └── test_benchmark.py
└── conftest.py       # pytest 配置
```

### 4.2 测试命名规范

```python
# 测试文件：test_*.py
# 测试类：Test<ClassName>
# 测试函数：test_<function>_<scenario>

class TestCrushRelayServer:
    """CrushRelayServer 测试"""

    def test_server_init_with_default_config(self):
        """测试使用默认配置初始化服务器"""
        server = CrushRelayServer()
        assert server.host == "0.0.0.0"
        assert server.port == 8765

    def test_server_init_with_custom_config(self):
        """测试使用自定义配置初始化服务器"""
        server = CrushRelayServer(host="127.0.0.1", port=8080)
        assert server.host == "127.0.0.1"
        assert server.port == 8080
```

### 4.3 测试覆盖率目标

| 代码类型 | 目标覆盖率 |
|----------|------------|
| 核心逻辑 | > 80% |
| 业务功能 | > 70% |
| 工具函数 | > 70% |
| CLI/入口 | > 60% |

### 4.4 测试最佳实践

```python
# 1. 使用 fixture 减少重复
import pytest

@pytest.fixture
def server():
    """创建服务器实例"""
    return CrushRelayServer()

def test_server_host(server):
    assert server.host == "0.0.0.0"

# 2. 测试边界条件
def test_session_with_empty_args():
    result = create_session("crush", [])
    assert result["success"] is True

# 3. 测试异常情况
def test_session_with_invalid_tool():
    result = create_session("invalid_tool")
    assert result["success"] is False
    assert "error" in result
```

---

## 5. Git工作流规范

### 5.1 分支策略

```
main (主分支，稳定版本)
├── feature/xxx (功能分支)
├── fix/xxx (修复分支)
└── refactor/xxx (重构分支)
```

### 5.2 提交消息格式

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(relay-server): 添加连接池支持` |
| `fix` | Bug 修复 | `fix(session-manager): 修复会话 ID 冲突` |
| `docs` | 文档更新 | `docs: 更新 README.md` |
| `style` | 代码格式 | `style: 使用 Black 格式化代码` |
| `refactor` | 重构 | `refactor: 重构会话管理器` |
| `perf` | 性能优化 | `perf: 优化消息处理性能` |
| `test` | 测试相关 | `test: 添加会话管理测试` |
| `chore` | 构建/工具 | `chore: 更新依赖` |

### 5.3 提交示例

```
feat(relay-server): 添加连接池支持

实现连接池以提高 WebSocket 连接性能。

- 添加 ConnectionPool 类
- 实现连接复用
- 添加连接超时处理

Closes #123
```

### 5.4 提交前检查

```bash
# 1. 运行测试
python3 -m pytest tests/ -v

# 2. 代码格式化
black .
isort .

# 3. 类型检查（可选）
mypy relay-server/
```

---

## 6. 日志规范

### 6.1 日志级别使用

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG: 开发调试信息
logger.debug(f"处理参数: {params}")

# INFO: 一般信息
logger.info(f"执行工具: {tool_name}")

# WARNING: 警告信息
logger.warning(f"配置使用默认值: {key}")

# ERROR: 错误信息
logger.error(f"工具执行失败: {error}", exc_info=True)

# CRITICAL: 严重错误
logger.critical(f"系统无法启动: {error}")
```

### 6.2 日志格式

```python
# 正确：包含上下文
logger.info(f"执行工具: {tool_name}, 参数: {params}")
logger.error(f"处理失败: {error}", exc_info=True)

# 错误：缺少上下文
logger.info("执行工具")
logger.error("失败")
```

---

## 7. 禁止事项

### 7.1 严格禁止

1. ❌ 硬编码密码、密钥等敏感信息
2. ❌ 跳过测试直接合并代码
3. ❌ 在主分支直接开发
4. ❌ 提交包含调试代码（print、断点等）
5. ❌ 破坏向后兼容性

### 7.2 不推荐

1. ⚠️ 过度优化 premature optimization
2. ⚠️ 过度抽象 over-abstraction
3. ⚠️ 添加不必要的外部依赖
4. ⚠️ 忽略类型注解（新代码）
5. ⚠️ 忽略文档字符串（公共API）

---

## 8. 开发检查清单

### 8.1 新功能开发

- [ ] 在 feature 分支开发
- [ ] 添加类型注解
- [ ] 添加 docstring
- [ ] 编写/更新测试
- [ ] 本地测试通过
- [ ] 更新相关文档

### 8.2 Bug 修复

- [ ] 在 fix/xxx 分支修复
- [ ] 添加回归测试
- [ ] 验证修复有效
- [ ] 确认无副作用

### 8.3 发布前

- [ ] 版本号更新
- [ ] CHANGELOG.md 更新
- [ ] 文档更新
- [ ] 标签创建
- [ ] 推送到远程

---

## 9. 常用命令

### 9.1 开发

```bash
# 运行测试
python3 -m pytest tests/ -v

# 运行测试并生成覆盖率报告
python3 -m pytest tests/ --cov=. --cov-report=html

# 代码格式化
black .
isort .

# 启动服务器
cd relay-server && python3 start_server.py
```

### 9.2 代码检查

```bash
# 类型检查
mypy relay-server/

# 代码风格
flake8 relay-server/ --max-line-length=120

# 复杂度检查
radon cc relay-server/ -a
```

---

## 10. 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 工程流程 | `docs/ENGINEERING_DELIVERY_PROCESS.md` | 完整开发流程 |
| 贡献指南 | `CONTRIBUTING.md` | 贡献流程 |
| 使用指南 | `USAGE_GUIDE.md` | 使用说明 |
| 故障排查 | `TROUBLESHOOTING.md` | 问题解决 |

---

**最后更新**: 2026-03-25
**版本**: 1.0.0
