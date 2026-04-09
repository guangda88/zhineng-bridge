# 依赖管理指南

**版本**: 1.0.0
**日期**: 2026-03-25

---

## 概述

智桥提供多个依赖配置文件，适用于不同的使用场景：

| 文件 | 用途 | 依赖数量 | 安装时间 |
|------|------|---------|---------|
| `requirements-minimal.txt` | 最小安装 (仅核心功能) | ~3 | ~30秒 |
| `requirements.txt` | 生产安装 (包含监控和日志) | ~8 | ~1-2分钟 |
| `requirements-dev.txt` | 开发安装 (包含测试和开发工具) | ~20 | ~2-3分钟 |

---

## 快速开始

### 方法 1: 使用安装脚本 (推荐)

```bash
# 运行安装脚本
python3 install_deps.py

# 按照提示选择安装模式:
# 1. 最小安装 (仅核心功能)
# 2. 生产安装 (包含监控和日志) - 推荐
# 3. 开发安装 (包含测试和开发工具)
# 4. 完整安装 (所有依赖)
```

### 方法 2: 手动安装

```bash
# 最小安装
pip install -r requirements-minimal.txt

# 生产安装
pip install -r requirements.txt

# 开发安装 (需要先安装生产依赖)
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 方法 3: 使用虚拟环境 (推荐)

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果是开发环境

# 完成后退出虚拟环境
deactivate
```

---

## 依赖说明

### 核心依赖

| 包名 | 版本 | 用途 | 必需 |
|------|------|------|------|
| websockets | 12.0-14.0 | WebSocket 服务器 | ✅ 是 |
| pydantic | 2.5-3.0 | 数据验证 | ✅ 是 |
| pydantic-settings | 2.1-3.0 | 设置管理 | ✅ 是 |
| python-dotenv | 1.0-2.0 | 环境变量 | ✅ 是 |

### 监控和日志

| 包名 | 版本 | 用途 | 必需 |
|------|------|------|------|
| psutil | 5.9-6.0 | 系统监控 | ⚠️ 生产推荐 |
| prometheus-client | 0.19-1.0 | Prometheus 指标 | ⚠️ 生产推荐 |
| structlog | 23.2-24.0 | 结构化日志 | ⚠️ 生产推荐 |

### 开发工具

| 包名 | 版本 | 用途 |
|------|------|------|
| pytest | 8.0-9.0 | 测试框架 |
| pytest-asyncio | 0.23-1.0 | asyncio 测试支持 |
| pytest-cov | 5.0-6.0 | 测试覆盖率 |
| pytest-benchmark | 5.0-6.0 | 性能基准测试 |
| black | 24.0-25.0 | 代码格式化 |
| isort | 5.13-6.0 | 导入排序 |
| flake8 | 7.0-8.0 | Linting |
| mypy | 1.8-2.0 | 类型检查 |

### 安全依赖 (生产环境)

| 包名 | 版本 | 用途 | 必需 |
|------|------|------|------|
| bcrypt | 4.1-5.0 | 密码哈希 | ⚠️ 生产推荐 |
| python-jose | 3.3-4.0 | JWT 令牌 | ⚠️ 生产推荐 |
| cryptography | 41.0-42.0 | 加密 | ⚠️ 生产推荐 |

---

## 版本锁定

所有依赖都使用范围锁定 (`>=x.y,<z.z`)，而不是固定版本。

**优点**:
- 允许获取安全更新和 bug 修复
- 不会因补丁版本升级而破坏兼容性

**缺点**:
- 次版本升级可能引入破坏性变更

**生产环境建议**:
```bash
# 生成精确版本锁定
pip freeze > requirements-lock.txt

# 生产环境使用锁定文件
pip install -r requirements-lock.txt
```

---

## 虚拟环境

### 为什么使用虚拟环境?

1. **隔离性**: 避免与系统 Python 包冲突
2. **可重现性**: 确保不同环境使用相同的依赖版本
3. **权限**: 不需要 root/sudo 权限
4. **清理**: 容易删除和重建

### 虚拟环境管理

```bash
# 创建
python3 -m venv venv

# 激活
source venv/bin/activate

# 导出依赖列表
pip freeze > requirements-freeze.txt

# 从列表恢复
pip install -r requirements-freeze.txt

# 停用
deactivate

# 删除虚拟环境
rm -rf venv
```

---

## 故障排除

### 问题: pip 安装失败

**解决方案**:
```bash
# 升级 pip
pip install --upgrade pip

# 使用镜像源 (中国用户)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用其他镜像源
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 问题: 依赖冲突

**解决方案**:
```bash
# 查看依赖树
pip install pipdeptree
pipdeptree

# 强制重新安装
pip install --force-reinstall -r requirements.txt
```

### 问题: Python 版本不兼容

**解决方案**:
```bash
# 检查 Python 版本 (需要 3.8+)
python3 --version

# 安装指定版本的 Python (Ubuntu/Debian)
sudo apt install python3.11

# 或使用 pyenv 安装多版本 Python
pyenv install 3.11.0
pyenv global 3.11.0
```

---

## 持续集成

### GitHub Actions 示例

```yaml
name: Install Dependencies

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
```

---

## 更新依赖

### 定期更新

```bash
# 查看过期的包
pip list --outdated

# 更新所有包
pip install --upgrade -r requirements.txt

# 更新特定包
pip install --upgrade websockets
```

### 安全更新

```bash
# 检查安全漏洞
pip install safety
safety check

# 修复已知漏洞
safety check --fix
```

---

## 最佳实践

### 1. 使用虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 锁定生产环境版本

```bash
pip freeze > requirements-lock.txt
```

### 3. 定期更新依赖

```bash
pip install --upgrade -r requirements.txt
```

### 4. 使用 .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
venv/
env/
ENV/

# Dependencies
*.egg-info/
dist/
build/
```

### 5. 版本控制

**提交**: `requirements.txt`, `requirements-dev.txt`, `requirements-minimal.txt`
**不提交**: `venv/`, `__pycache__/`, `requirements-lock.txt` (可选)

---

## 总结

| 场景 | 使用文件 | 命令 |
|------|---------|------|
| 快速测试 | requirements-minimal.txt | `pip install -r requirements-minimal.txt` |
| 生产部署 | requirements.txt | `pip install -r requirements.txt` |
| 开发环境 | requirements.txt + requirements-dev.txt | `pip install -r requirements.txt -r requirements-dev.txt` |
| 自动安装 | 安装脚本 | `python3 install_deps.py` |

---

**更新日期**: 2026-03-25
**维护者**: Zhineng-bridge Team
