# 智桥（Zhineng-bridge）贡献指南

感谢您对智桥（Zhineng-bridge）的兴趣！我们欢迎各种形式的贡献。

## 目录

1. [如何贡献](#如何贡献)
2. [开发环境设置](#开发环境设置)
3. [代码规范](#代码规范)
4. [提交规范](#提交规范)
5. [测试要求](#测试要求)
6. [文档要求](#文档要求)
7. [Pull Request 流程](#pull-request-流程)
8. [问题反馈](#问题反馈)
9. [社区准则](#社区准则)

---

## 如何贡献

### 贡献类型

我们欢迎以下类型的贡献：

- 🐛 **Bug 修复**: 修复已知问题
- ✨ **新功能**: 添加新特性
- 📝 **文档**: 改进文档
- 🎨 **UI/UX**: 改进用户界面和体验
- ⚡ **性能**: 性能优化
- 🧪 **测试**: 添加或改进测试
- 🌍 **翻译**: 多语言支持
- 💡 **想法**: 提出建议和想法

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

详见下面的 [Pull Request 流程](#pull-request-流程)。

---

## 开发环境设置

### 前置要求

- Python 3.8+
- Node.js 16+（用于 Web UI 开发）
- Git
- 现代浏览器（Chrome, Firefox, Safari, Edge）

### 安装步骤

#### 1. 克隆仓库

```bash
git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge
```

#### 2. 安装 Python 依赖

```bash
# 安装基础依赖
pip install websockets asyncio

# 安装开发依赖
pip install pytest pytest-cov pytest-asyncio
pip install black isort pylint

# 安装 LingMinOpt（可选，用于参数优化）
cd /home/ai/LingMinOpt
pip install -e .
cd -
```

#### 3. 安装 JavaScript 依赖（可选）

```bash
cd web/ui
npm install
```

#### 4. 验证安装

```bash
# 运行测试
python3 -m pytest tests/ -v

# 检查版本
python3 -c "import sys; print(f'Python {sys.version}')"
```

### 开发工具推荐

#### IDE/编辑器
- VS Code（推荐）
- PyCharm
- WebStorm（用于 Web UI）

#### VS Code 扩展
- Python
- Pylance
- Black Formatter
- GitLens
- ES7+ React/Redux/React-Native snippets（用于 Web UI）

---

## 代码规范

### Python 代码规范

#### 文件命名
- 使用 snake_case: `relay_server.py`, `session_manager.py`
- 测试文件以 `test_` 开头: `test_relay_server.py`

#### 类命名
- 使用 PascalCase: `CrushRelayServer`, `SessionManager`

#### 函数和变量命名
- 使用 snake_case: `create_session()`, `session_id`

#### 常量命名
- 使用 UPPER_CASE: `MAX_CONNECTIONS`, `PING_INTERVAL`

#### 类型提示
- 使用类型提示：
```python
def create_session(self, tool_name: str, args: List[str] = None) -> str:
    """创建会话"""
    pass
```

#### 文档字符串
- 使用 Google 风格或标准 Python docstrings：
```python
def create_session(self, tool_name: str, args: List[str] = None) -> str:
    """
    创建新会话

    Args:
        tool_name: 工具名称
        args: 参数列表

    Returns:
        会话 ID

    Raises:
        ValueError: 如果工具名称无效
    """
    pass
```

#### 格式化
使用 Black 格式化代码：
```bash
# 格式化所有 Python 文件
black .

# 仅检查格式
black --check .
```

#### 导入排序
使用 isort 排序导入：
```bash
isort .
```

### JavaScript 代码规范

#### 文件命名
- 使用 camelCase: `client.js`, `app.js`

#### 类命名
- 使用 PascalCase: `EncryptionManager`, `PerformanceOptimizer`

#### 函数和变量命名
- 使用 camelCase: `connectWebSocket()`, `sendMessage()`

#### 常量命名
- 使用 UPPER_SNAKE_CASE: `MAX_CONNECTIONS`, `PING_INTERVAL`

#### 格式化
使用 Prettier：
```bash
# 格式化所有 JS 文件
npx prettier --write web/ui/**/*.js
```

### CSS 代码规范

#### 类命名
- 使用 kebab-case: `.page-title`, `.btn-primary`
- BEM 风格（可选）: `.block__element--modifier`

#### CSS 变量
使用 CSS 自定义属性：
```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
}
```

---

## 提交规范

### 提交消息格式

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加 Cursor 工具支持` |
| `fix` | 修复 Bug | `fix: 修复 WebSocket 连接超时` |
| `docs` | 文档更新 | `docs: 更新 README.md` |
| `style` | 代码格式（不影响功能） | `style: 使用 Black 格式化代码` |
| `refactor` | 重构（既不是新功能也不是修复） | `refactor: 重构会话管理器` |
| `perf` | 性能优化 | `perf: 优化消息处理性能` |
| `test` | 添加测试 | `test: 添加会话管理测试` |
| `chore` | 构建/工具链更新 | `chore: 更新依赖` |
| `revert` | 回滚提交 | `revert: feat: 添加某功能` |

#### Scope 范围

常用 Scope：
- `relay-server`: WebSocket 中继服务器
- `session-manager`: 会话管理器
- `web-ui`: Web UI
- `docs`: 文档
- `tests`: 测试
- `opt`: 优化
- `ci`: CI/CD

#### 示例

```
feat(relay-server): 添加连接池支持

实现连接池以提高 WebSocket 连接性能。

- 添加 ConnectionPool 类
- 实现连接复用
- 添加连接超时处理

Closes #123
```

```
fix(session-manager): 修复会话 ID 冲突问题

使用 UUID 生成器确保会话 ID 唯一性。

Fixes #456
```

### 提交最佳实践

1. **单个提交**: 每个提交只做一件事
2. **清晰描述**: 提交消息应该清晰描述更改
3. **使用现在时**: "Add feature" 而不是 "Added feature"
4. **不要结尾加句号**: 标题不加句号
5. **引用 Issue**: 使用 `Fixes #123` 或 `Closes #456`

---

## 测试要求

### 测试覆盖率

目标测试覆盖率: **>= 70%**
当前测试覆盖率: **82%**

### 测试类型

#### 1. 单元测试
测试单个函数或类。

```python
# tests/unit/test_relay_server.py
import pytest
from relay_server.server import CrushRelayServer

def test_relay_server_init():
    """测试中继服务器初始化"""
    server = CrushRelayServer()
    assert server.host == "0.0.0.0"
    assert server.port == 8765
```

运行单元测试：
```bash
python3 -m pytest tests/unit/ -v
```

#### 2. 集成测试
测试多个组件的集成。

```python
# tests/integration/test_session_manager.py
import pytest
from phase1.session_manager.session_manager import SessionManager

def test_session_workflow():
    """测试会话工作流"""
    manager = SessionManager()
    session_id = manager.create_session('crush')
    session = manager.get_session(session_id)
    assert session is not None
    manager.delete_session(session_id)
```

运行集成测试：
```bash
python3 -m pytest tests/integration/ -v
```

#### 3. E2E 测试
端到端测试整个系统。

```python
# tests/e2e/test_websocket.py
import pytest
import websockets
import json

@pytest.mark.asyncio
async def test_websocket_ping_pong():
    """测试 WebSocket 心跳"""
    async with websockets.connect("ws://localhost:8765") as ws:
        await ws.send(json.dumps({"type": "ping"}))
        response = await ws.recv()
        data = json.loads(response)
        assert data["type"] == "pong"
```

运行 E2E 测试：
```bash
python3 -m pytest tests/e2e/ -v
```

### 运行所有测试

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行测试并生成覆盖率报告
python3 -m pytest tests/ --cov=. --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 测试最佳实践

1. **测试隔离**: 每个测试应该独立
2. **使用 fixture**: 使用 pytest fixture 减少重复
3. **清晰命名**: 测试名称应该清晰描述测试内容
4. **测试边界**: 测试边界条件和异常情况
5. **快速执行**: 测试应该快速执行

---

## 文档要求

### 必需文档

以下文档必须保持更新：

1. **README.md**: 项目介绍和快速开始
2. **CHANGELOG.md**: 版本变更历史
3. **QUICKSTART.md**: 5 分钟快速开始
4. **USAGE_GUIDE.md**: 详细使用指南
5. **TROUBLESHOOTING.md**: 故障排查指南
6. **docs/API.md**: API 文档

### 文档风格

- 使用清晰简洁的语言
- 提供代码示例
- 包含截图（如果适用）
- 使用 Markdown 格式
- 添加目录和链接

### 更新文档

当您修改代码时，请同时更新相关文档：

- 添加新功能 → 更新 README.md 和 USAGE_GUIDE.md
- 修复 Bug → 更新 TROUBLESHOOTING.md
- 变更 API → 更新 docs/API.md
- 发布新版本 → 更新 CHANGELOG.md

---

## Pull Request 流程

### 1. Fork 和 Clone

```bash
# Fork 仓库到您的 GitHub 账户
# 然后克隆您的 fork
git clone https://github.com/YOUR_USERNAME/zhineng-bridge.git
cd zhineng-bridge
```

### 2. 配置上游仓库

```bash
# 添加上游仓库
git remote add upstream https://github.com/guangda88/zhineng-bridge.git

# 拉取最新代码
git fetch upstream
git merge upstream/main
```

### 3. 创建特性分支

```bash
# 创建新分支
git checkout -b feature/your-feature-name

# 或修复 Bug 分支
git checkout -b fix/bug-description
```

### 4. 进行更改

```bash
# 进行更改...
# 编写代码、测试、文档...
```

### 5. 提交更改

```bash
# 添加更改
git add .

# 提交
git commit -m "feat: 添加新功能描述"

# 或使用多个提交
git commit -m "feat: 添加功能 X"
git commit -m "fix: 修复问题 Y"
```

### 6. 推送到您的 Fork

```bash
git push origin feature/your-feature-name
```

### 7. 创建 Pull Request

1. 访问 GitHub 上的原仓库
2. 点击 "New Pull Request"
3. 选择您的特性分支
4. 填写 PR 模板
5. 提交 PR

### PR 审查清单

在提交 PR 前，请确保：

- [ ] 代码遵循项目规范
- [ ] 所有测试通过（`python3 -m pytest tests/ -v`）
- [ ] 测试覆盖率 >= 70%
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 提交消息遵循规范
- [ ] 没有 lint 警告
- [ ] 代码已格式化（Black）
- [ ] 导入已排序（isort）

### PR 模板

创建 PR 时，请使用以下模板：

```markdown
## 描述
简要描述此 PR 的目的和更改内容。

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 重大变更
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] E2E 测试通过
- [ ] 手动测试通过

## 相关 Issue
Closes #123

## 截图（如果适用）
在此添加截图

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 测试覆盖率 >= 70%
- [ ] 文档已更新
- [ ] 无 lint 警告
```

---

## 问题反馈

### 报告 Bug

如果您发现 Bug，请：

1. 检查 [现有 Issues](https://github.com/guangda88/zhineng-bridge/issues)
2. 如果 Bug 还没有被报告，创建新 Issue
3. 使用 Bug 报告模板

### Bug 报告模板

```markdown
## Bug 描述
简要描述 Bug

## 复现步骤
1. 执行 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

## 期望行为
描述您期望发生什么

## 实际行为
描述实际发生了什么

## 环境信息
- OS: [例如 Ubuntu 22.04]
- Python 版本: [例如 3.12.3]
- 智桥版本: [例如 1.0.0]
- 浏览器: [例如 Chrome 120]

## 截图
如果适用，添加截图

## 额外信息
任何其他相关信息
```

### 功能请求

如果您有功能建议，请：

1. 检查 [现有 Issues](https://github.com/guangda88/zhineng-bridge/issues)
2. 如果建议还未被提出，创建新 Issue
3. 使用功能请求模板

### 功能请求模板

```markdown
## 功能描述
简要描述您想要的功能

## 问题或用例
描述这个功能解决的问题或用例

## 建议的解决方案
描述您认为应该如何实现

## 替代方案
描述您考虑过的其他替代方案

## 额外信息
任何其他相关信息
```

---

## 社区准则

### 我们的承诺

为了营造开放和友好的环境，我们承诺：

1. **尊重**: 尊重不同的观点和经验
2. **包容**: 欢迎所有人参与
3. **协作**: 与他人合作建设社区
4. **专业**: 以专业和礼貌的方式互动

### 不可接受的行为

以下行为不可接受：

- 使用性化的语言或图像
- 人身攻击或侮辱
- 公开或私下骚扰
- 未经许可发布他人的私人信息
- 其他不专业或不恰当的行为

### 执行

项目维护者有权删除、编辑或拒绝不符合本准则的评论、提交、代码、wiki 编辑、问题和其他贡献。

---

## 获取帮助

如果您需要帮助：

- 📖 查看 [USAGE_GUIDE.md](./USAGE_GUIDE.md)
- 🔧 查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- 🚀 查看 [QUICKSTART.md](./QUICKSTART.md)
- 💬 在 GitHub 提交 [Issue](https://github.com/guangda88/zhineng-bridge/issues)
- 📧 联系维护者（如果提供）

---

## 许可证

通过贡献代码，您同意您的贡献将在 [MIT License](./LICENSE) 下许可。

---

## 致谢

感谢所有为智桥做出贡献的开发者！

---

**最后更新**: 2026-03-24
**版本**: 1.0.0
