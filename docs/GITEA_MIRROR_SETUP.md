# Gitea 镜像仓库和双仓库推送配置指南

本文档说明如何为智桥（Zhineng-bridge）项目配置 Gitea 镜像仓库并实现双仓库推送。

## 目录

1. [概述](#概述)
2. [Gitea 仓库创建](#gitea-仓库创建)
3. [本地 Git 配置](#本地-git-配置)
4. [自动同步配置](#自动同步配置)
5. [CI/CD 集成](#cicd-集成)
6. [验证配置](#验证配置)

---

## 概述

### 什么是镜像仓库？

镜像仓库是指将一个 Git 仓库的完整副本同步到另一个 Git 托管平台。

### 为什么需要双仓库？

- **GitHub**: 国际用户访问速度快，社区活跃，CI/CD 工具丰富
- **Gitea**: 国内用户访问速度快，符合本地法规，可自托管

### 智桥的双仓库策略

- **主仓库**: GitHub - https://github.com/guangda88/zhineng-bridge
- **镜像仓库**: Gitea - http://zhinenggitea.iepose.cn/guangda/zhineng-bridge

---

## Gitea 仓库创建

### 1. 登录 Gitea

访问: http://zhinenggitea.iepose.cn

### 2. 创建新仓库

1. 点击右上角的 "+" 按钮
2. 选择 "新建仓库"
3. 填写仓库信息：
   - 仓库所有者: guangda
   - 仓库名称: zhineng-bridge
   - 仓库描述: 跨平台实时同步和通信 SDK，支持多种 AI 编码工具
   - 是否私有: ❌ 不选择（公开仓库）
   - 初始化: ❌ 不选择（稍后推送）

4. 点击 "创建仓库"

### 3. 记录仓库信息

创建后，记录以下信息：

```
Gitea 仓库 URL: http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git
克隆 URL: http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git
```

---

## 本地 Git 配置

### 1. 添加 Gitea 远程仓库

```bash
cd /home/ai/zhineng-bridge

# 添加 Gitea 远程仓库
git remote add gitea http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git

# 验证远程仓库
git remote -v
```

输出应该显示：
```
origin  https://github.com/guangda88/zhineng-bridge.git (fetch)
origin  https://github.com/guangda88/zhineng-bridge.git (push)
gitea   http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git (fetch)
gitea   http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git (push)
```

### 2. 推送代码到 Gitea

```bash
# 首次推送所有分支和标签
git push gitea --all
git push gitea --tags
```

### 3. 配置推送 URL（可选）

如果你希望在推送时简化命令，可以配置推送 URL：

```bash
# 配置推送到所有远程仓库
git remote set-url --add --push origin https://github.com/guangda88/zhineng-bridge.git
git remote set-url --add --push origin http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git

# 现在推送一次会推送到两个仓库
git push origin main
```

注意：这种方法不推荐，因为推送失败时难以诊断。

---

## 自动同步配置

### 方法 1: 使用 Git 钩子

创建 post-push 钩子，在每次推送到 GitHub 后自动推送到 Gitea。

#### 创建钩子脚本

```bash
# 创建钩子目录
mkdir -p .git/hooks

# 创建 post-push 钩子
cat > .git/hooks/post-push << 'EOF'
#!/bin/bash

# 检查是否推送到 origin
if [ "$1" == "origin" ]; then
    echo "🔄 同步到 Gitea..."

    # 推送到 Gitea
    git push gitea --all
    git push gitea --tags

    echo "✅ 已同步到 Gitea"
fi
EOF

# 使钩子可执行
chmod +x .git/hooks/post-push
```

#### 使用钩子

修改 git push 命令以调用钩子：

```bash
# 安装 git-extras 工具
sudo apt-get install git-extras  # Ubuntu/Debian
brew install git-extras  # macOS

# 使用 git push-to-remote 命令
git push-to-remote origin main
```

### 方法 2: 使用 Git 别名

创建一个别名，简化双仓库推送。

```bash
# 添加 git 别名
git config --global alias.push-all '!git push origin --all && git push origin --tags && git push gitea --all && git push gitea --tags && echo "✅ 已推送到所有仓库"'

# 使用别名推送
git push-all
```

### 方法 3: 使用 Shell 脚本

创建一个 shell 脚本，封装推送逻辑。

```bash
# 创建推送脚本
cat > /home/ai/zhineng-bridge/scripts/push-all.sh << 'EOF'
#!/bin/bash

# 获取当前分支
BRANCH=$(git symbolic-ref --short HEAD)

echo "📤 推送到 GitHub..."
git push origin $BRANCH

echo "📤 推送到 Gitea..."
git push gitea $BRANCH

echo "🏷️  推送标签到 GitHub..."
git push origin --tags

echo "🏷️  推送标签到 Gitea..."
git push gitea --tags

echo "✅ 已推送到所有仓库"
EOF

# 使脚本可执行
chmod +x /home/ai/zhineng-bridge/scripts/push-all.sh
```

使用脚本：

```bash
# 推送到所有仓库
./scripts/push-all.sh
```

---

## CI/CD 集成

### GitHub Actions 同步到 Gitea

我们已经创建了 GitHub Actions 工作流（`.github/workflows/release.yml`），在发布时自动同步到 Gitea。

#### 配置 Gitea 令牌

1. 在 Gitea 中生成个人访问令牌：
   - 设置 → 应用 → 生成令牌
   - 令牌名称: GitHub Actions
   - 权限: `repo`（读写权限）

2. 将令牌添加到 GitHub Secrets：
   - GitHub 仓库 → Settings → Secrets and variables → Actions
   - 添加新的 secret:
     - Name: `GITEA_TOKEN`
     - Value: `<你的 Gitea 令牌>`
   - 添加仓库 URL:
     - Name: `GITEA_REPO_URL`
     - Value: `http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git`

#### 工作流配置

发布工作流（`.github/workflows/release.yml`）中已包含同步步骤：

```yaml
sync-to-gitea:
  name: Sync to Gitea
  runs-on: ubuntu-latest
  needs: create-github-release
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/')

  steps:
  - name: Checkout code
    uses: actions/checkout@v4

  - name: Push to Gitea
    run: |
      # Configure git for Gitea
      git remote add gitea ${{ secrets.GITEA_REPO_URL }}
      git config user.name "GitHub Actions"
      git config user.email "actions@github.com"

      # Push tag to Gitea
      git push gitea ${{ github.ref }} || echo "Gitea push failed or not configured"
```

### Gitea CI/CD（可选）

如果 Gitea 支持 CI/CD（如 Drone CI），可以配置：

1. 在 Gitea 中启用 CI/CD
2. 配置 `.drone.yml` 或相应文件
3. 推送代码到 Gitea

---

## 验证配置

### 1. 验证远程仓库

```bash
# 查看所有远程仓库
git remote -v
```

应该显示：
```
origin  https://github.com/guangda88/zhineng-bridge.git (fetch)
origin  https://github.com/guangda88/zhineng-bridge.git (push)
gitea   http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git (fetch)
gitea   http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git (push)
```

### 2. 验证推送

```bash
# 测试推送
git push origin main
git push gitea main
```

检查：
- GitHub: https://github.com/guangda88/zhineng-bridge
- Gitea: http://zhinenggitea.iepose.cn/guangda/zhineng-bridge

### 3. 验证标签同步

```bash
# 创建测试标签
git tag v0.0.1-test

# 推送标签
git push origin v0.0.1-test
git push gitea v0.0.1-test

# 清理测试标签
git tag -d v0.0.1-test
git push origin :refs/tags/v0.0.1-test
git push gitea :refs/tags/v0.0.1-test
```

### 4. 验证 CI/CD 同步

1. 在 GitHub 上创建 release 标签：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. 检查 GitHub Actions 是否运行

3. 等待 Actions 完成

4. 检查 Gitea 是否收到标签

---

## 最佳实践

### 1. 推送策略

- **主要仓库**: GitHub（主开发、Issue、PR）
- **镜像仓库**: Gitea（只读同步）

### 2. 工作流

```
开发 → GitHub → 提交 PR → 合并 → 推送到 Gitea
```

### 3. Issue 和 PR

- 在 GitHub 上创建 Issue 和 PR
- Gitea 仓库作为镜像，不直接接受 PR

### 4. 文档

- 在文档中说明有两个仓库
- 引导用户根据自己的地理位置选择合适的仓库

---

## 故障排查

### 问题 1: 推送到 Gitea 失败

**症状**:
```
error: failed to push some refs to 'http://zhinenggitea.iepose.cn/guangda/zhineng-bridge.git'
```

**解决方案**:
1. 检查网络连接
2. 验证 Gitea 凭证
3. 检查仓库 URL 是否正确
4. 检查权限设置

### 问题 2: 钩子不执行

**症状**: post-push 钩子未运行

**解决方案**:
1. 检查钩子权限：
   ```bash
   ls -l .git/hooks/post-push
   ```

2. 确保可执行：
   ```bash
   chmod +x .git/hooks/post-push
   ```

3. 检查 git core.hooksPath 设置：
   ```bash
   git config core.hooksPath
   ```

### 问题 3: CI/CD 同步失败

**症状**: GitHub Actions 推送失败

**解决方案**:
1. 检查 Secrets 是否正确配置
2. 检查 Gitea 令牌权限
3. 查看 Actions 日志

---

## 相关文档

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Gitea 文档](https://docs.gitea.io/)
- [Git 远程仓库文档](https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes)

---

**文档版本**: 1.0.0
**更新时间**: 2026-03-24
**适用范围**: 智桥（Zhineng-bridge）所有版本
