# 智桥（Zhineng-bridge）脚本目录

本目录包含智桥的各种辅助脚本，用于自动化和简化开发、测试、发布等任务。

## 脚本列表

### verify-publish.py

**用途**: 发布前验证脚本，自动检查发布前的各项要求

**运行方式**:
```bash
# 从项目根目录运行
python3 scripts/verify-publish.py

# 指定项目路径
python3 scripts/verify-publish.py --project-path /path/to/project

# 跳过测试检查
python3 scripts/verify-publish.py --skip-tests

# 跳过构建检查
python3 scripts/verify-publish.py --skip-build
```

**检查项目**:
- ✅ 代码质量检查
  - 服务器文件完整性
  - Web UI 文件完整性
  - 依赖检查

- ✅ 测试检查
  - 单元测试（17/17）
  - 集成测试（17/17）
  - E2E 测试（16/16）
  - 测试覆盖率（目标: >=70%）

- ✅ 文档检查
  - 核心文档完整性
  - 示例文件完整性
  - CHANGELOG 检查

- ✅ 版本管理
  - 版本号一致性
  - 版本文件存在

- ✅ Git 状态
  - 工作区是否干净

- ✅ 构建检查
  - Python 包构建
  - Wheel 包生成
  - 源码包生成

**输出示例**:
```
======================================================================
智桥发布验证
======================================================================

======================================================================
代码质量
======================================================================

ℹ 检查服务器文件...
✓ relay-server/server.py 存在
✓ relay-server/start_server.py 存在
✓ phase1/session_manager/session_manager.py 存在
✓ phase1/session_manager/start_manager.py 存在

ℹ 检查 Web UI...
✓ web/ui/index.html 存在
✓ web/ui/js/app.js 存在
✓ web/ui/js/client.js 存在
✓ web/ui/css/base.css 存在

ℹ 检查依赖...
✓ 依赖检查通过

======================================================================
测试
======================================================================

ℹ 运行测试套件...
✓ 单元测试通过
✓ 集成测试通过
✓ E2E 测试通过

ℹ 检查测试覆盖率...
✓ 测试覆盖率: 82.0% (目标: >=70%)

======================================================================
文档
======================================================================

ℹ 检查文档完整性...
✓ README.md 存在
✓ CHANGELOG.md 存在
✓ QUICKSTART.md 存在
✓ USAGE_GUIDE.md 存在
✓ TROUBLESHOOTING.md 存在
✓ RELEASE_CHECKLIST.md 存在

ℹ 检查示例文件...
✓ examples/basic_usage.py 存在
✓ examples/cursor_config.md 存在
✓ examples/claude_config.md 存在
✓ examples/README.md 存在

ℹ 检查 CHANGELOG...
✓ 最新版本: 1.0.0

======================================================================
版本管理
======================================================================

ℹ 检查版本号一致性...
✓ VERSION 文件: 1.0.0
✓ README.md 版本号: 1.0.0

======================================================================
Git 状态
======================================================================

ℹ 检查 Git 状态...
✓ 工作区干净

======================================================================
构建
======================================================================

ℹ 检查构建...
✓ 构建成功
✓ Wheel 包: zhineng_bridge-1.0.0-py3-none-any.whl
✓ 源码包: zhineng-bridge-1.0.0.tar.gz

======================================================================
验证总结
======================================================================

✓ 所有关键检查通过！

✓ 准备发布
```

**返回值**:
- `0`: 所有检查通过，准备发布
- `1`: 部分检查失败，需要修复

## 使用建议

### 发布前检查

在发布新版本前，始终运行此脚本：

```bash
python3 scripts/verify-publish.py
```

如果所有检查都通过，可以继续发布流程。如果有检查失败，请修复后再重试。

### CI/CD 集成

可以将此脚本集成到 CI/CD 流程中：

```yaml
# .github/workflows/release.yml 示例
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install websockets pytest pytest-cov pytest-asyncio
      - name: Run release verification
        run: |
          python3 scripts/verify-publish.py
```

### 定期检查

即使不发布新版本，也可以定期运行此脚本来检查项目健康度：

```bash
# 每周运行一次
python3 scripts/verify-publish.py
```

## 未来脚本计划

以下脚本计划在未来添加：

### build.py
自动化构建脚本
- 清理旧的构建文件
- 构建所有目标平台
- 生成校验和
- 签名发布包

### test.py
增强测试脚本
- 并行运行测试
- 生成 HTML 报告
- 性能基准测试
- 集成测试报告

### deploy.py
部署脚本
- 部署到 PyPI
- 同步到 Gitea
- 发布 GitHub Release
- 更新文档站点

### benchmark.py
性能基准测试脚本
- 运行性能测试
- 生成性能报告
- 与历史版本比较
- 检测性能回归

### lint.py
代码质量检查脚本
- 运行 pylint
- 运行 mypy
- 运行 black（格式检查）
- 运行 isort（导入排序检查）

### update-dependencies.py
依赖更新脚本
- 检查依赖更新
- 更新依赖文件
- 测试兼容性
- 生成更新报告

## 贡献指南

如果您有新的脚本想法或改进现有脚本，欢迎贡献！

1. Fork 本仓库
2. 创建新脚本或改进现有脚本
3. 添加文档和使用说明
4. 测试脚本功能
5. 提交 PR

## 注意事项

1. **Python 版本**: 脚本需要 Python 3.8+
2. **依赖**: 部分脚本需要额外的 Python 包
3. **权限**: 某些脚本可能需要适当的文件系统权限
4. **网络**: 部分脚本可能需要网络连接（如更新依赖）
5. **环境变量**: 某些脚本可能需要配置环境变量

## 故障排查

### 问题 1: 脚本找不到模块

**症状**: `ModuleNotFoundError`

**解决方案**:
```bash
# 确保从项目根目录运行
cd /home/ai/zhineng-bridge
python3 scripts/verify-publish.py
```

### 问题 2: 测试失败

**症状**: 测试检查失败

**解决方案**:
```bash
# 先手动运行测试查看详细信息
python3 -m pytest tests/ -v

# 查看测试覆盖率
python3 -m pytest tests/ --cov=. --cov-report=html
```

### 问题 3: 构建失败

**症状**: 构建检查失败

**解决方案**:
```bash
# 手动构建查看详细信息
python3 -m build -v

# 检查依赖
python3 -m pip check
```

## 相关文档

- [发布检查清单](../RELEASE_CHECKLIST.md)
- [使用指南](../USAGE_GUIDE.md)
- [快速开始](../QUICKSTART.md)
- [故障排查](../TROUBLESHOOTING.md)

## 许可证

MIT License - 与智桥主项目相同

---

**版本**: 1.0.0
**更新时间**: 2026-03-24
