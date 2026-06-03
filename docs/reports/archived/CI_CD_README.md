# CI/CD 配置说明

本目录包含 zhineng-bridge 项目的 CI/CD 配置文件，支持 GitHub 和 Gitea 双仓库。

## 文件结构

```
.github/
└── workflows/
    ├── test.yml       # GitHub 测试工作流
    ├── lint.yml       # GitHub 代码质量检查
    ├── performance.yml # GitHub 性能测试
    ├── release.yml    # GitHub 发布工作流
    └── ci.yml         # GitHub 综合CI/CD工作流

.gitea/
└── workflows/
    └── ci.yml         # Gitea 综合CI/CD工作流
```

## 工作流说明

### GitHub 工作流

#### 1. test.yml
- **触发条件**: 推送到 main/master/develop 分支，或创建 Pull Request
- **功能**:
  - 在 Python 3.8-3.12 上运行测试
  - 运行单元测试、集成测试、E2E 测试
  - 生成代码覆盖率报告
  - 上传覆盖率到 Codecov
  - 检查覆盖率是否达到 70% 阈值
- **特别功能**:
  - Web UI 测试
  - 发布前验证

#### 2. lint.yml
- **触发条件**: 推送或 Pull Request
- **功能**:
  - 使用 Pylint 进行代码质量检查
  - 检查代码复杂度和长度

#### 3. performance.yml
- **触发条件**: 推送或 Pull Request
- **功能**:
  - 运行性能基准测试
  - 生成性能报告
  - 比较性能指标

#### 4. release.yml
- **触发条件**: 推送到 main/master 分支或手动触发
- **功能**:
  - 构建和发布 Docker 镜像
  - 创建 GitHub Release
  - 推送到 PyPI

#### 5. ci.yml
- **触发条件**: 推送到 main/master/develop 分支，或创建 Pull Request
- **功能**:
  - 综合CI/CD流程
  - 代码质量检查（Black, isort, flake8）
  - 运行所有测试
  - 构建和部署

### Gitea 工作流

#### ci.yml
- **触发条件**: 与 GitHub 相同
- **功能**: 与 GitHub ci.yml 相同
- **注意**: 使用 GitHub Actions 的基础镜像

## 使用方法

### GitHub Actions

1. **配置 Secrets**:
   - 进入仓库 Settings → Secrets and variables → Actions
   - 添加以下 Secrets:
     - `PYPI_TOKEN`: PyPI API Token（用于发布）
     - `CODECOV_TOKEN`: Codecov Token（用于覆盖率上传）

2. **触发工作流**:
   - Push 到 master/main/develop 分支
   - 创建 Pull Request
   - 在 Actions 标签页手动触发

### Gitea Actions

1. **配置 Secrets**:
   - 进入仓库 Settings → Secrets
   - 添加以下 Secrets:
     - `PYPI_TOKEN`: PyPI API Token
     - `CODECOV_TOKEN`: Codecov Token

2. **触发工作流**:
   - Push 到 master/main/develop 分支
   - 创建 Pull Request
   - 在 Actions 标签页手动触发

## 工作流状态查看

### GitHub Actions
- 访问: https://github.com/guangda88/zhineng-bridge/actions

### Gitea Actions
- 访问: http://zhinenggitea.iepose.cn/guangda/zhineng-bridge/actions

## 测试覆盖率要求

- **最低覆盖率**: 70%
- **目标覆盖率**: 80%+

## 性能要求

当前性能目标：
- 会话创建时间: < 50ms
- WebSocket 连接时间: < 20ms
- 页面加载时间: < 1s
- 内存使用: < 50MB

## 本地测试

### 使用测试启动脚本

```bash
# 运行完整测试套件（自动启动和停止服务器）
./scripts/run_tests_with_servers.sh

# 运行特定测试类型
./scripts/run_tests_with_servers.sh tests/unit/
./scripts/run_tests_with_servers.sh tests/integration/
./scripts/run_tests_with_servers.sh tests/e2e/

# 运行特定测试文件
./scripts/run_tests_with_servers.sh tests/unit/test_relay_server.py
```

### 手动测试

```bash
# 启动服务器
cd relay-server
python3 start_server.py &
python3 health_check.py &

# 运行测试
python3 -m pytest tests/ -v

# 停止服务器
pkill -f start_server.py
pkill -f health_check.py
```

## 故障排除

### 测试失败

1. 检查日志输出
2. 确保所有依赖已安装
3. 检查服务器是否正常运行
4. 查看详细的错误信息

### 覆盖率不足

1. 运行覆盖率报告：
   ```bash
   python3 -m pytest tests/ --cov=. --cov-report=html
   ```
2. 查看 HTML 报告：
   ```bash
   open htmlcov/index.html
   ```
3. 添加缺失的测试用例

### 性能问题

1. 运行性能测试：
   ```bash
   python3 -m pytest tests/performance/ -v
   ```
2. 查看性能基准报告
3. 优化慢速代码

## 更新日志

### 2026-03-29
- 创建综合 CI/CD 工作流
- 添加 Gitea Actions 支持
- 添加代码覆盖率检查
- 添加代码质量检查
- 添加性能基准测试

## 联系和支持

如有问题，请提交 Issue 或联系项目维护者。
