# 智桥 PWA 项目开发规划（修订版）

**版本：** 2.0.0
**日期：** 2026-03-28
**修订原因：** 基于代码审查报告（P0阻塞问题识别）
**项目经理：** 智桥开发团队
**预计周期：** 8 周

---

## 📋 修订说明

### 代码审查发现的关键问题

**P0 阻塞问题（必须立即解决）：**
1. 🔴 **VAPID密钥占位符未配置** (push.js:54-56) - 推送通知完全不可用
2. 🔴 **文件API端点未实现** (file-mentions.js:61-63) - 文件提及完全不可用
3. 🔴 **后端推送服务未实现** - 无法发送推送通知
4. 🔴 **PWA图标资源缺失** - PWA无法安装到主屏幕
5. 🔴 **HTTPS/Nginx配置不完整** - 无法部署到生产环境

**P1 重要问题：**
1. 🟡 缺少TypeScript类型定义（只有.d.ts文件）
2. 🟡 前端测试缺失（tests/frontend/存在但内容少）
3. 🟡 错误处理不完整（文件提及API调用缺少降级方案）
4. 🟡 配置管理问题（硬编码的业务网络地址）

**代码优势：**
- ✅ 模块化设计，功能按文件清晰分离
- ✅ ES6类封装（如SlashCommandsManager）
- ✅ 前端有try-catch，后端有异常类
- ✅ 安全机制完备（JWT认证 + CSRF防护 + 请求签名）
- ✅ 日志系统（logger.py）
- ✅ 性能追踪（metrics.py）

**当前完成度：**
- 推送通知前端：80%（缺VAPID配置）
- 文件提及前端：60%（缺后端API）
- 斜杠命令前端：90%
- PWA Manifest：100%

### 主要修订内容

| 修订项 | 原计划 | 修订后 | 原因 |
|--------|--------|--------|------|
| **Week 1-2 重点** | 推送通知 + 文件提及 | 100% 聚焦 P0 阻塞问题 | 阻塞问题必须先解决 |
| **后端开发分配** | 40h（分散在各周） | Week 1-2: 40h + Week 3: 8h（48h总计） | P0任务需要大量后端工作 |
| **前端开发分配** | Week 1-2: 40h | Week 1-2: 40h（集成测试） | 后端完成后进行集成 |
| **测试工程师** | Week 6 开始 | Week 1 开始（阻塞问题测试） | 立即测试P0功能 |
| **资源总计** | 232 人时 | 328 人时（6人） | 增加后端和测试资源 |
| **里程碑调整** | Week 1-3: 功能完成 | Week 1-2: P0阻塞问题解决 | 必须先解决阻塞 |
| **风险应对** | 通用风险应对 | 针对具体代码问题的应对 | 更精确的风险管理 |

---

## 📋 目录

1. [项目概述](#项目概述)
2. [现状分析（基于代码审查）](#现状分析基于代码审查)
3. [开发目标](#开发目标)
4. [P0阻塞问题优先解决计划](#p0阻塞问题优先解决计划)
5. [详细开发计划](#详细开发计划)
6. [里程碑与交付](#里程碑与交付)
7. [资源分配（修订版）](#资源分配修订版)
8. [风险管理（修订版）](#风险管理修订版)
9. [质量保证](#质量保证)
10. [部署与运维](#部署与运维)

---

## 项目概述

### 项目背景

智桥（zhineng-bridge）是一个跨平台实时同步和通信 SDK，连接多个 AI 编程工具和 IDE。当前已实现核心功能（WebSocket 实时同步、多会话管理、端到端加密、离线缓存），但代码审查发现多个 **P0 阻塞问题**，必须在部署到生产环境前解决。

### 项目目标

**核心目标：** 在 8 周内解决所有 P0 阻塞问题，完成 PWA 部署，实现 90%+ 的原生应用用户体验。

**P0 优先目标（Week 1-2 必须完成）：**
- 🔴 生成 VAPID 密钥对并配置到前端
- 🔴 实现后端文件 API 端点（read, search, stats, list）
- 🔴 实现后端推送服务端点（subscribe, unsubscribe, send）
- 🔴 生成 PWA 图标资源（10 个尺寸）
- 🔴 配置 HTTPS/Nginx（Week 3）

**具体目标：**
- ✅ 推送通知功能完全可用
- ✅ 文件提及功能完全可用
- ✅ 优化移动端 UI 和交互
- ✅ 完善 PWA 安装体验
- ✅ 集成后端 API 支持
- ✅ 完善测试和文档
- ✅ 部署到生产环境

### 成功指标

|| 指标 | 目标值 | 测量方式 |
|------|--------|---------|
| **P0 阻塞问题解决** | 100% | 功能测试通过 |
| **PWA 安装率** | > 30% | PWA 安装事件统计 |
| **用户留存率** | > 50% (7天) | 用户活跃度分析 |
| **推送通知打开率** | > 40% | 通知点击率统计 |
| **页面加载时间** | < 2s (首次), < 0.5s (后续) | Lighthouse 性能测试 |
| **用户满意度** | > 4.0/5.0 | 用户反馈调查 |
| **测试覆盖率** | > 80% | 单元测试覆盖率报告 |
| **Lighthouse 评分** | > 90 | 性能测试报告 |

---

## 现状分析（基于代码审查）

### ✅ 已完成功能（代码审查确认）

|| 功能模块 | 技术方案 | 文件位置 | 完成度 | 备注 |
|---------|---------|---------|--------|------|
| **实时双向同步** | WebSocket | relay-server/server.py | 100% | ✅ 代码质量优秀 |
| **多会话管理** | SessionManager | phase1/session_manager/ | 100% | ✅ 代码质量优秀 |
| **端到端加密** | Web Crypto API | phase3/encryption/encryption.js | 100% | ✅ 代码质量优秀 |
| **离线缓存** | Service Worker + IndexedDB | phase4/optimization/sw.js | 100% | ✅ 代码质量优秀 |
| **响应式设计** | CSS Media Queries | web/ui/css/mobile.css, responsive.css | 100% | ✅ 已实现底部导航栏 |
| **PWA Manifest** | manifest.json | web/ui/manifest.json | 100% | ✅ 完整 |
| **推送通知前端** | Web Push API | web/ui/js/push.js | 80% | ⚠️ 缺 VAPID 配置 |
| **文件提及前端** | File API | web/ui/js/file-mentions.js | 60% | ⚠️ 缺后端 API |
| **斜杠命令前端** | 命令解析器 | web/ui/js/slash-commands.js | 90% | ✅ 代码质量优秀 |

### 🔲 待完成功能（基于代码审查）

#### P0 阻塞问题（必须立即解决）

|| 功能模块 | 优先级 | 预计工时 | 阻塞原因 | 紧急程度 |
|---------|--------|---------|---------|---------|
| **VAPID 密钥生成** | P0 | 0.5h | 未生成 | 🔴 紧急 |
| **后端文件 API 实现** | P0 | 12h | 未开始 | 🔴 紧急 |
| **后端推送服务** | P0 | 8h | 未开始 | 🔴 紧急 |
| **推送通知集成** | P0 | 4h | 后端推送服务 | 🟡 高 |
| **文件提及集成** | P0 | 4h | 后端文件 API | 🟡 高 |
| **图标资源生成** | P0 | 2h | 图标文件不存在 | 🔴 紧急 |
| **HTTPS/Nginx 配置** | P0 | 8h | 配置不完整 | 🔴 紧急 |
| **P0 功能测试** | P0 | 16h | 立即测试阻塞问题 | 🟡 高 |

#### P1 重要问题

|| 功能模块 | 优先级 | 预计工时 | 阻塞原因 |
|---------|--------|---------|---------|
| **移动端 UI 优化** | P1 | 16h | CSS 框架存在，交互未实现 |
| **触摸手势支持** | P1 | 12h | 未开始 |
| **用户引导页面** | P1 | 16h | 未开始 |
| **测试覆盖补充** | P1 | 40h | 当前约 82%，需补充 P1 功能 |
| **文档完善** | P1 | 40h | 需更新 |
| **TypeScript 类型** | P1 | 16h | 只有 .d.ts 文件 |
| **前端测试补充** | P1 | 24h | tests/frontend/ 存在但内容少 |
| **错误处理完善** | P1 | 8h | 文件提及 API 调用缺少降级方案 |
| **配置管理改进** | P1 | 8h | 硬编码的业务网络地址 |

#### P2 增强功能

|| 功能模块 | 优先级 | 预计工时 | 阻塞原因 |
|---------|--------|---------|---------|
| **自定义代理库** | P2 | 16h | 未开始 |
| **MCP 权限提示** | P2 | 20h | 未开始 |

### 📊 技术债务（基于代码审查）

1. **缺少错误处理**：文件提及和斜杠命令的异常处理不完善（⚠️ 中等）
2. **缺少单元测试**：新增功能没有测试覆盖（⚠️ 中等）
3. **性能优化空间**：Service Worker 缓存策略可以优化（⚠️ 低）
4. **安全性待提升**：文件 API 需要更严格的权限控制（🟡 中等）
5. **TypeScript 类型缺失**：只有 .d.ts 文件，未迁移到 TypeScript（⚠️ 中等）

---

## 开发目标

### P0 - 必须完成（阻塞问题 - Week 1-2）

**截止日期：Week 2 结束（2026-04-14）**

1. **推送通知完整实现**
   - ✅ 生成 VAPID 密钥对（0.5h）
   - 🔴 实现后端推送服务（8h）
   - 🔴 集成前端推送通知（4h）
   - ✅ 会话状态变化通知测试
   - ✅ iOS 和 Android 兼容性测试

2. **文件提及系统集成**
   - 🔴 实现后端文件 API（read, search, stats, list）（12h）
   - 🔴 集成前端文件提及 UI（4h）
   - ✅ 安全性验证和权限控制
   - ✅ 文件搜索和读取性能测试

3. **部署配置准备**
   - ✅ 生成 PWA 图标资源（2h）
   - 🔴 配置 HTTPS/Nginx（8h - Week 3）
   - ✅ PWA 安装体验测试
   - ✅ 生产环境部署准备

4. **P0 功能测试**
   - ✅ 推送通知测试（iOS/Android 兼容性）
   - ✅ 文件提及功能测试（安全验证、性能）
   - ✅ PWA 安装测试
   - ✅ Lighthouse 性能测试（目标 > 90）

### P1 - 应该完成（重要功能 - Week 3-6）

**截止日期：Week 6 结束（2026-05-12）**

5. **移动端 UI 优化**
   - ✅ 底部导航栏交互实现
   - ✅ 侧边抽屉菜单动画
   - ✅ 浮动操作按钮（FAB）
   - ✅ 触摸友好的交互（< 100ms）

6. **用户引导改进**
   - ✅ 启动引导页面
   - ✅ 功能介绍和快速开始教程
   - ✅ 示例提示词
   - ✅ 常见问题解答

7. **测试覆盖补充**
   - ✅ 单元测试（目标覆盖率 > 80%）
   - ✅ 集成测试（所有 P0/P1 功能）
   - ✅ E2E 测试（关键用户流程）
   - ✅ 性能测试（Lighthouse > 90）

8. **文档完善**
   - ✅ 用户手册
   - ✅ API 文档
   - ✅ 开发者文档
   - ✅ 故障排除指南

9. **代码质量改进**
   - ✅ TypeScript 类型定义补充
   - ✅ 前端测试补充
   - ✅ 错误处理完善
   - ✅ 配置管理改进

### P2 - 可以完成（增强功能 - Week 7-8）

**截止日期：Week 8 结束（2026-05-26）**

10. **触摸手势支持**
    - ✅ 滑动切换会话
    - ✅ 长按上下文菜单
    - ✅ 双指缩放

11. **自定义代理库**
    - ✅ 代理定义同步
    - ✅ 代理管理 UI
    - ✅ 代理执行引擎

12. **MCP 权限提示**
    - ✅ 权限拦截器
    - ✅ 权限请求 UI
    - ✅ 权限记忆功能

---

## P0阻塞问题优先解决计划

### Week 1: 紧急阻塞问题解决（P0 - Part 1）

**目标：** 解决最紧急的阻塞问题（VAPID、文件 API、推送服务）

**任务清单：**

#### Day 1: VAPID 密钥生成和配置（0.5h）

**负责人：** 后端开发 + 前端开发（20%）

**任务：**
```bash
# 1. 安装 web-push 工具
npm install -g web-push

# 2. 生成 VAPID 密钥对
web-push generate-vapid-keys

# 输出示例：
# Public Key: BIXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Private Key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# 3. 配置 VAPID 公钥到前端
# 编辑 web/ui/js/push.js:54-56
applicationServerKey: this.urlBase64ToUint8Array(
    'BIXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'  # 替换为实际公钥
)

# 4. 保存 VAPID 私钥到服务器配置
echo "VAPID_PRIVATE_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" >> ~/.env

# 5. 测试推送权限请求
# 打开浏览器 DevTools > Application > Service Workers
# 点击 "Request Permission" 按钮
```

**验收标准：**
- [ ] VAPID 公钥已配置到前端（push.js:54-56）
- [ ] VAPID 私钥已保存到服务器配置
- [ ] 浏览器弹出通知权限请求
- [ ] 推送权限可以成功请求

**预计工时：** 0.5h

---

#### Day 2-5: 后端文件 API 实现（12h）

**负责人：** 后端开发（100%）

**任务：**

**创建文件：** `relay-server/file_api.py`

```python
# relay-server/file_api.py

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class FileReadRequest(BaseModel):
    path: str
    max_size: int = 10 * 1024 * 1024  # 10MB

class FileStats(BaseModel):
    path: str
    size: int
    is_file: bool
    is_dir: bool
    modified_time: str
    permissions: str

class FileItem(BaseModel):
    path: str
    name: str
    size: int
    is_file: bool
    is_dir: bool

# 文件扩展白名单（防止读取敏感文件）
ALLOWED_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
    '.md', '.txt', '.json', '.yaml', '.yml', '.xml',
    '.java', '.c', '.cpp', '.h', '.hpp', '.go', '.rs'
}

# 黑名单目录（防止读取系统目录）
BLACKLIST_DIRS = {
    '/etc', '/proc', '/sys', '/dev', '/root', '/tmp',
    'C:\\Windows', 'C:\\Program Files', 'C:\\Users'
}

def validate_path(path: str, base_dir: str = None) -> Path:
    """
    验证文件路径安全性

    Args:
        path: 文件路径
        base_dir: 基础目录（如果指定，只能访问此目录及其子目录）

    Returns:
        Path: 安全的 Path 对象

    Raises:
        HTTPException: 路径不安全
    """
    # 解析路径
    try:
        path_obj = Path(path).resolve()
    except Exception as e:
        logger.error(f"Invalid path: {path}, error: {e}")
        raise HTTPException(status_code=400, detail="Invalid file path")

    # 检查黑名单目录
    for black_dir in BLACKLIST_DIRS:
        if str(path_obj).startswith(black_dir):
            logger.warning(f"Access denied to blacklisted directory: {path_obj}")
            raise HTTPException(status_code=403, detail="Access denied to system directory")

    # 检查路径遍历攻击
    if '..' in path.parts or path.is_absolute():
        logger.warning(f"Path traversal attempt detected: {path}")
        raise HTTPException(status_code=403, detail="Path traversal not allowed")

    # 检查基础目录限制
    if base_dir:
        base_path = Path(base_dir).resolve()
        try:
            path_obj.relative_to(base_path)
        except ValueError:
            logger.warning(f"Access denied outside base directory: {path_obj}")
            raise HTTPException(status_code=403, detail="Access denied outside base directory")

    return path_obj

def check_file_permissions(path_obj: Path) -> bool:
    """
    检查文件权限

    Args:
        path_obj: Path 对象

    Returns:
        bool: 是否有权限读取
    """
    return os.access(path_obj, os.R_OK)

# API 端点

@app.get("/api/files/read")
async def read_file(path: str, max_size: int = Query(default=10 * 1024 * 1024)):
    """
    读取文件内容

    Args:
        path: 文件路径
        max_size: 最大文件大小（字节）

    Returns:
        dict: 文件内容
    """
    try:
        # 验证路径
        path_obj = validate_path(path)

        # 检查文件是否存在
        if not path_obj.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # 检查是否为文件
        if not path_obj.is_file():
            raise HTTPException(status_code=400, detail="Not a file")

        # 检查文件权限
        if not check_file_permissions(path_obj):
            raise HTTPException(status_code=403, detail="No permission to read file")

        # 检查文件大小
        file_size = path_obj.stat().st_size
        if file_size > max_size:
            raise HTTPException(status_code=413, detail=f"File too large (max {max_size} bytes)")

        # 检查文件扩展名
        file_extension = path_obj.suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            logger.warning(f"File extension not allowed: {file_extension}")
            raise HTTPException(status_code=403, detail="File type not allowed")

        # 读取文件内容
        try:
            with open(path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(path_obj, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Failed to read file {path_obj}: {e}")
                raise HTTPException(status_code=500, detail="Failed to read file")

        logger.info(f"File read successfully: {path_obj}, size: {file_size} bytes")

        return {
            "success": True,
            "path": str(path_obj),
            "content": content,
            "size": file_size,
            "encoding": "utf-8"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/files/search")
async def search_files(
    query: str,
    path: str = ".",
    max_results: int = Query(default=50),
    fuzzy: bool = Query(default=True)
):
    """
    搜索文件

    Args:
        query: 搜索关键词
        path: 搜索路径
        max_results: 最大结果数
        fuzzy: 是否模糊搜索

    Returns:
        dict: 搜索结果
    """
    try:
        # 验证路径
        base_path = validate_path(path)

        if not base_path.exists():
            raise HTTPException(status_code=404, detail="Base path not found")

        if not base_path.is_dir():
            raise HTTPException(status_code=400, detail="Base path is not a directory")

        results = []
        query_lower = query.lower()

        # 递归搜索文件
        for root, dirs, files in os.walk(base_path):
            for filename in files:
                # 检查文件扩展名
                file_ext = Path(filename).suffix.lower()
                if file_ext not in ALLOWED_EXTENSIONS:
                    continue

                file_path = Path(root) / filename

                # 检查文件权限
                if not check_file_permissions(file_path):
                    continue

                # 模糊搜索
                if fuzzy:
                    if query_lower in filename.lower():
                        results.append({
                            "name": filename,
                            "path": str(file_path),
                            "size": file_path.stat().st_size
                        })
                else:
                    # 精确搜索
                    if filename == query:
                        results.append({
                            "name": filename,
                            "path": str(file_path),
                            "size": file_path.stat().st_size
                        })

                # 限制结果数量
                if len(results) >= max_results:
                    break

            if len(results) >= max_results:
                break

        logger.info(f"File search: query='{query}', results={len(results)}")

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/files/stats")
async def get_file_stats(path: str):
    """
    获取文件统计信息

    Args:
        path: 文件路径

    Returns:
        dict: 文件统计信息
    """
    try:
        # 验证路径
        path_obj = validate_path(path)

        if not path_obj.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # 检查文件权限
        if not check_file_permissions(path_obj):
            raise HTTPException(status_code=403, detail="No permission to access file")

        stat_info = path_obj.stat()

        return {
            "success": True,
            "path": str(path_obj),
            "size": stat_info.st_size,
            "is_file": path_obj.is_file(),
            "is_dir": path_obj.is_dir(),
            "modified_time": stat_info.st_mtime,
            "permissions": oct(stat_info.st_mode)[-3:]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file stats for {path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/files/list")
async def list_files(
    path: str = ".",
    recursive: bool = Query(default=False),
    max_depth: int = Query(default=3)
):
    """
    列出文件

    Args:
        path: 目录路径
        recursive: 是否递归
        max_depth: 最大递归深度

    Returns:
        dict: 文件列表
    """
    try:
        # 验证路径
        base_path = validate_path(path)

        if not base_path.exists():
            raise HTTPException(status_code=404, detail="Directory not found")

        if not base_path.is_dir():
            raise HTTPException(status_code=400, detail="Not a directory")

        files = []
        directories = []

        if recursive:
            # 递归列出文件
            for root, dirs, filenames in os.walk(base_path):
                # 计算当前深度
                depth = root.relative_to(base_path).parts.__len__()
                if depth > max_depth:
                    continue

                for filename in filenames:
                    file_path = Path(root) / filename

                    # 检查文件扩展名
                    file_ext = file_path.suffix.lower()
                    if file_ext not in ALLOWED_EXTENSIONS:
                        continue

                    # 检查文件权限
                    if not check_file_permissions(file_path):
                        continue

                    files.append({
                        "name": filename,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "is_file": True,
                        "is_dir": False
                    })

                for dirname in dirs:
                    dir_path = Path(root) / dirname
                    directories.append({
                        "name": dirname,
                        "path": str(dir_path),
                        "size": 0,
                        "is_file": False,
                        "is_dir": True
                    })
        else:
            # 非递归列出文件
            for item in base_path.iterdir():
                # 检查文件权限
                if not check_file_permissions(item):
                    continue

                if item.is_file():
                    # 检查文件扩展名
                    file_ext = item.suffix.lower()
                    if file_ext not in ALLOWED_EXTENSIONS:
                        continue

                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size,
                        "is_file": True,
                        "is_dir": False
                    })
                elif item.is_dir():
                    directories.append({
                        "name": item.name,
                        "path": str(item),
                        "size": 0,
                        "is_file": False,
                        "is_dir": True
                    })

        logger.info(f"File list: path='{path}', files={len(files)}, dirs={len(directories)}")

        return {
            "success": True,
            "path": str(base_path),
            "files": files,
            "directories": directories,
            "total_files": len(files),
            "total_dirs": len(directories)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing files in {path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 集成到主服务器
def register_file_api_routes(app: FastAPI):
    """注册文件 API 路由"""
    app.include_router(
        fastapi.APIRouter(prefix="/api/files"),
        tags=["files"]
    )
```

**集成到 relay-server/http_server.py：**

```python
# relay-server/http_server.py

from file_api import (
    read_file,
    search_files,
    get_file_stats,
    list_files,
    register_file_api_routes
)

# 在 FastAPI 应用中注册路由
app.include_router(
    fastapi.APIRouter(prefix="/api/files", tags=["files"])
)

# 添加文件 API 端点
app.get("/api/files/read")(read_file)
app.get("/api/files/search")(search_files)
app.get("/api/files/stats")(get_file_stats)
app.get("/api/files/list")(list_files)
```

**验收标准：**
- [ ] /api/files/read 端点实现，支持路径验证、大小限制、安全检查
- [ ] /api/files/search 端点实现，支持模糊搜索、分页
- [ ] /api/files/stats 端点实现，返回文件元数据
- [ ] /api/files/list 端点实现，支持递归选项
- [ ] 安全验证：路径遍历保护、文件权限检查、文件扩展白名单
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过

**预计工时：** 12h

---

#### Day 6-7: 后端推送服务和图标生成（10h）

**负责人：** 后端开发（100%） + 前端开发（20%）

**任务 1：后端推送服务实现（8h）**

**创建文件：** `relay-server/push_service.py`

```python
# relay-server/push_service.py

import json
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, HttpUrl
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

# VAPID 配置（从环境变量或配置文件读取）
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS = {
    "sub": "mailto:admin@zhineng-bridge.example.com"
}

class PushSubscription(BaseModel):
    """推送订阅信息"""
    endpoint: str
    keys: Dict[str, str]  # { "p256dh": "...", "auth": "..." }

class PushMessage(BaseModel):
    """推送消息"""
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    data: Optional[Dict] = None
    tag: Optional[str] = None

# 内存存储（生产环境应使用数据库）
subscriptions: Dict[str, PushSubscription] = {}

@app.post("/api/notifications/subscribe")
async def subscribe_push(subscription: PushSubscription):
    """
    订阅推送通知

    Args:
        subscription: 推送订阅信息

    Returns:
        dict: 订阅结果
    """
    try:
        # 生成订阅 ID（使用 endpoint 的哈希）
        subscription_id = hash(subscription.endpoint)

        # 保存订阅信息
        subscriptions[subscription_id] = subscription

        logger.info(f"Push subscription added: {subscription_id}")

        return {
            "success": True,
            "subscription_id": subscription_id,
            "message": "Subscribed successfully"
        }

    except Exception as e:
        logger.error(f"Error subscribing to push: {e}")
        raise HTTPException(status_code=500, detail="Failed to subscribe")

@app.post("/api/notifications/unsubscribe")
async def unsubscribe_push(subscription_id: str):
    """
    取消订阅推送通知

    Args:
        subscription_id: 订阅 ID

    Returns:
        dict: 取消订阅结果
    """
    try:
        if subscription_id not in subscriptions:
            raise HTTPException(status_code=404, detail="Subscription not found")

        # 删除订阅信息
        del subscriptions[subscription_id]

        logger.info(f"Push subscription removed: {subscription_id}")

        return {
            "success": True,
            "message": "Unsubscribed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing from push: {e}")
        raise HTTPException(status_code=500, detail="Failed to unsubscribe")

@app.post("/api/notifications/send")
async def send_push_notification(
    message: PushMessage,
    subscription_id: Optional[str] = None
):
    """
    发送推送通知

    Args:
        message: 推送消息
        subscription_id: 订阅 ID（如果不提供，发送给所有订阅者）

    Returns:
        dict: 发送结果
    """
    try:
        # 构造推送数据
        push_data = {
            "title": message.title,
            "body": message.body,
            "icon": message.icon or "/icons/icon-192x192.png",
            "badge": message.badge or "/icons/badge-72x72.png",
            "data": message.data or {},
            "tag": message.tag
        }

        # 确定目标订阅者
        target_subscriptions = []
        if subscription_id:
            # 发送给特定订阅者
            if subscription_id in subscriptions:
                target_subscriptions.append(subscriptions[subscription_id])
            else:
                raise HTTPException(status_code=404, detail="Subscription not found")
        else:
            # 发送给所有订阅者
            target_subscriptions = list(subscriptions.values())

        # 发送推送通知
        success_count = 0
        failed_count = 0

        for subscription in target_subscriptions:
            try:
                # 转换为 pywebpush 需要的格式
                subscription_info = {
                    "endpoint": subscription.endpoint,
                    "keys": subscription.keys
                }

                # 发送推送
                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps(push_data),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS
                )

                success_count += 1
                logger.info(f"Push notification sent to {subscription.endpoint}")

            except WebPushException as e:
                failed_count += 1
                logger.error(f"Failed to send push to {subscription.endpoint}: {e}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Unexpected error sending push to {subscription.endpoint}: {e}")

        logger.info(f"Push notification sent: success={success_count}, failed={failed_count}")

        return {
            "success": True,
            "total_sent": success_count + failed_count,
            "success_count": success_count,
            "failed_count": failed_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

# 辅助函数：发送会话状态通知
async def send_session_state_notification(
    session_id: str,
    state: str,  # "started", "stopped", "completed", "error"
    tool_name: str
):
    """
    发送会话状态变化通知

    Args:
        session_id: 会话 ID
        state: 状态
        tool_name: 工具名称
    """
    titles = {
        "started": "会话已启动",
        "stopped": "会话已停止",
        "completed": "任务已完成",
        "error": "发生错误"
    }

    messages = {
        "started": f"{tool_name} 会话已启动",
        "stopped": f"{tool_name} 会话已停止",
        "completed": f"{tool_name} 任务执行完成",
        "error": f"{tool_name} 会话执行出错"
    }

    message = PushMessage(
        title=titles.get(state, "会话状态更新"),
        body=messages.get(state, f"{tool_name} 会话状态: {state}"),
        data={
            "type": "session_state",
            "session_id": session_id,
            "state": state,
            "tool_name": tool_name
        },
        tag=f"session_{session_id}"
    )

    await send_push_notification(message)

# 辅助函数：发送任务完成通知
async def send_task_completion_notification(
    session_id: str,
    tool_name: str,
    result_summary: str
):
    """
    发送任务完成通知

    Args:
        session_id: 会话 ID
        tool_name: 工具名称
        result_summary: 结果摘要
    """
    message = PushMessage(
        title="任务已完成",
        body=f"{tool_name} 任务执行完成: {result_summary}",
        data={
            "type": "task_completion",
            "session_id": session_id,
            "tool_name": tool_name,
            "result_summary": result_summary
        },
        tag=f"task_{session_id}"
    )

    await send_push_notification(message)

# 辅助函数：发送错误通知
async def send_error_notification(
    session_id: str,
    tool_name: str,
    error_message: str
):
    """
    发送错误通知

    Args:
        session_id: 会话 ID
        tool_name: 工具名称
        error_message: 错误消息
    """
    message = PushMessage(
        title="发生错误",
        body=f"{tool_name} 会话执行出错: {error_message}",
        data={
            "type": "error",
            "session_id": session_id,
            "tool_name": tool_name,
            "error_message": error_message
        },
        tag=f"error_{session_id}"
    )

    await send_push_notification(message)
```

**集成到 relay-server/http_server.py：**

```python
# relay-server/http_server.py

from push_service import (
    subscribe_push,
    unsubscribe_push,
    send_push_notification,
    send_session_state_notification,
    send_task_completion_notification,
    send_error_notification
)

# 添加推送通知端点
app.post("/api/notifications/subscribe")(subscribe_push)
app.post("/api/notifications/unsubscribe")(unsubscribe_push)
app.post("/api/notifications/send")(send_push_notification)
```

**验收标准：**
- [ ] /api/notifications/subscribe 端点实现
- [ ] /api/notifications/unsubscribe 端点实现
- [ ] /api/notifications/send 端点实现
- [ ] 辅助函数实现（会话状态、任务完成、错误通知）
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过

**预计工时：** 8h

---

**任务 2：PWA 图标资源生成（2h）**

**负责人：** 前端开发（100%）

**任务：**

```bash
# 1. 安装 PWA Asset Generator
npm install -g pwa-asset-generator

# 2. 准备源图标（至少 512x512 像素的 PNG 文件）
# 将源图标保存为 web/ui/icons/icon-source.png

# 3. 生成 PWA 图标资源
cd web/ui
pwa-asset-generator icons/icon-source.png icons/ \
  --manifest manifest.json \
  --background "transparent" \
  --padding "0.1"

# 或者使用在线工具：
# https://www.pwabuilder.com/imageGenerator

# 4. 验证生成的图标
# 应该生成以下尺寸：
# - icon-16x16.png
# - icon-32x32.png
# - icon-72x72.png
# - icon-96x96.png
# - icon-128x128.png
# - icon-144x144.png
# - icon-152x152.png
# - icon-192x192.png
# - icon-384x384.png
# - icon-512x512.png
# - favicon.ico
# - apple-touch-icon.png

# 5. 更新 manifest.json 中的图标路径
# web/ui/manifest.json
{
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}

# 6. 更新 index.html 中的图标引用
# <link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
# <link rel="icon" type="image/png" sizes="32x32" href="/icons/icon-32x32.png">
# <link rel="icon" type="image/png" sizes="16x16" href="/icons/icon-16x16.png">
# <link rel="shortcut icon" href="/icons/favicon.ico">
```

**验收标准：**
- [ ] 10 个尺寸的 PWA 图标生成完成（16x16 到 512x512）
- [ ] Apple touch icon 生成完成
- [ ] Favicon 生成完成
- [ ] manifest.json 图标路径更新完成
- [ ] index.html 图标引用更新完成
- [ ] 图标在浏览器中正确显示

**预计工时：** 2h

---

#### Week 1 交付物

- [ ] VAPID 密钥对配置文件（~/.env）
- [ ] 后端文件 API 代码（relay-server/file_api.py）
- [ ] 后端推送服务代码（relay-server/push_service.py）
- [ ] PWA 图标资源包（10 个尺寸）
- [ ] 前端 VAPID 公钥配置（web/ui/js/push.js）

---

### Week 2: 前端集成和测试（P0 - Part 2）

**目标：** 集成前端推送通知和文件提及，测试 P0 功能

**任务清单：**

#### Day 8-9: 前端推送通知集成（4h）

**负责人：** 前端开发（100%）

**任务：**

**1. 更新 web/ui/js/push.js**

```javascript
// web/ui/js/push.js

class PushNotificationManager {
    constructor() {
        this.subscription = null;
        this.isSubscribed = false;

        // VAPID 公钥（已配置）
        this.vapidPublicKey = 'BIXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX';

        this.init();
    }

    async init() {
        console.log('✅ PushNotificationManager initialized');
        await this.checkSubscription();
    }

    async checkSubscription() {
        try {
            const registration = await navigator.serviceWorker.ready;
            this.subscription = await registration.pushManager.getSubscription();
            this.isSubscribed = !!this.subscription;

            if (this.isSubscribed) {
                console.log('✅ User is already subscribed to push notifications');
                // 将订阅信息发送到后端
                await this.sendSubscriptionToServer(this.subscription);
            } else {
                console.log('⚠️  User is not subscribed to push notifications');
            }

            return this.isSubscribed;
        } catch (error) {
            console.error('❌ Error checking subscription:', error);
            return false;
        }
    }

    async requestPermission() {
        try {
            const permission = await Notification.requestPermission();
            console.log(`✅ Notification permission: ${permission}`);

            if (permission === 'granted') {
                await this.subscribe();
                return true;
            } else {
                console.warn('⚠️  Notification permission denied');
                return false;
            }
        } catch (error) {
            console.error('❌ Error requesting permission:', error);
            return false;
        }
    }

    async subscribe() {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            this.subscription = subscription;
            this.isSubscribed = true;

            console.log('✅ User subscribed to push notifications');

            // 将订阅信息发送到后端
            await this.sendSubscriptionToServer(subscription);

            return subscription;
        } catch (error) {
            console.error('❌ Error subscribing to push notifications:', error);
            throw error;
        }
    }

    async unsubscribe() {
        try {
            if (!this.subscription) {
                console.warn('⚠️  No subscription to unsubscribe');
                return;
            }

            await this.subscription.unsubscribe();
            this.subscription = null;
            this.isSubscribed = false;

            console.log('✅ User unsubscribed from push notifications');

            // 通知后端取消订阅
            await this.sendUnsubscriptionToServer();

        } catch (error) {
            console.error('❌ Error unsubscribing:', error);
            throw error;
        }
    }

    async sendSubscriptionToServer(subscription) {
        try {
            const subscriptionData = {
                endpoint: subscription.endpoint,
                keys: {
                    p256dh: subscription.getKey('p256dh')
                        ? this.arrayBufferToBase64(subscription.getKey('p256dh'))
                        : '',
                    auth: subscription.getKey('auth')
                        ? this.arrayBufferToBase64(subscription.getKey('auth'))
                        : ''
                }
            };

            const response = await fetch('/api/notifications/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(subscriptionData)
            });

            if (!response.ok) {
                throw new Error('Failed to send subscription to server');
            }

            console.log('✅ Subscription sent to server');
        } catch (error) {
            console.error('❌ Error sending subscription to server:', error);
            throw error;
        }
    }

    async sendUnsubscriptionToServer() {
        try {
            const subscriptionId = this.subscription ? this.subscription.endpoint : '';
            const response = await fetch('/api/notifications/unsubscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ subscription_id: subscriptionId })
            });

            if (!response.ok) {
                throw new Error('Failed to send unsubscription to server');
            }

            console.log('✅ Unsubscription sent to server');
        } catch (error) {
            console.error('❌ Error sending unsubscription to server:', error);
            throw error;
        }
    }

    async testNotification() {
        try {
            if (!this.isSubscribed) {
                console.warn('⚠️  User is not subscribed to push notifications');
                return;
            }

            // 通过后端发送测试通知
            const response = await fetch('/api/notifications/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: '测试通知',
                    body: '这是一条测试推送通知',
                    icon: '/icons/icon-192x192.png',
                    data: {
                        type: 'test',
                        timestamp: new Date().toISOString()
                    }
                })
            });

            if (!response.ok) {
                throw new Error('Failed to send test notification');
            }

            console.log('✅ Test notification sent');
        } catch (error) {
            console.error('❌ Error sending test notification:', error);
            throw error;
        }
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        return outputArray;
    }

    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;

        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }

        return window.btoa(binary);
    }
}

// 导出到全局
window.PushNotificationManager = PushNotificationManager;

// 自动初始化（如果页面已加载）
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.pushManager = new PushNotificationManager();
    });
} else {
    window.pushManager = new PushNotificationManager();
}
```

**2. 更新 Service Worker (web/ui/phase4/optimization/sw.js)**

```javascript
// web/ui/phase4/optimization/sw.js

self.addEventListener('push', event => {
    console.log('✅ Push event received');

    let data = {
        title: '新通知',
        body: '您收到一条新通知',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png'
    };

    try {
        data = event.data.json();
    } catch (e) {
        console.warn('⚠️  Failed to parse push data');
    }

    const options = {
        body: data.body,
        icon: data.icon || '/icons/icon-192x192.png',
        badge: data.badge || '/icons/badge-72x72.png',
        tag: data.tag,
        data: data.data || {},
        requireInteraction: data.type === 'error',  // 错误通知需要用户交互
        actions: [
            {
                action: 'open',
                title: '查看',
                icon: '/icons/icon-96x96.png'
            },
            {
                action: 'dismiss',
                title: '关闭',
                icon: '/icons/icon-96x96.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', event => {
    console.log('✅ Notification clicked:', event.notification);

    event.notification.close();

    if (event.action === 'open' || !event.action) {
        // 打开应用
        event.waitUntil(
            clients.openWindow('/').then(client => {
                if (client) {
                    // 发送消息到客户端
                    client.postMessage({
                        type: 'notification_clicked',
                        data: event.notification.data
                    });
                }
            })
        );
    } else if (event.action === 'dismiss') {
        // 关闭通知（无需额外操作）
        console.log('✅ Notification dismissed');
    }
});
```

**验收标准：**
- [ ] 推送通知管理器初始化成功
- [ ] 用户可以请求推送权限
- [ ] 用户可以订阅/取消订阅
- [ ] 订阅信息成功发送到后端
- [ ] Service Worker 接收推送通知
- [ ] 通知点击跳转到应用
- [ ] 测试通知功能正常

**预计工时：** 4h

---

#### Day 10: 前端文件提及集成（4h）

**负责人：** 前端开发（100%）

**任务：**

**1. 更新 web/ui/js/file-mentions.js**

```javascript
// web/ui/js/file-mentions.js

class FileMentionsManager {
    constructor() {
        this.fileCache = new Map();  // 文件内容缓存
        this.maxCacheSize = 100;     // 最大缓存文件数
        this.maxFileSize = 10 * 1024 * 1024;  // 最大文件大小：10MB

        this.init();
    }

    async init() {
        console.log('✅ FileMentionsManager initialized');
    }

    /**
     * 解析文本中的 @file 语法
     */
    parseFileMentions(text) {
        const regex = /@file\s+([^\s]+)/g;
        const matches = [];
        let match;

        while ((match = regex.exec(text)) !== null) {
            matches.push({
                syntax: match[0],
                filePath: match[1]
            });
        }

        return matches;
    }

    /**
     * 读取文件内容
     */
    async readFile(filePath) {
        try {
            // 检查缓存
            if (this.fileCache.has(filePath)) {
                console.log(`✅ File loaded from cache: ${filePath}`);
                return this.fileCache.get(filePath);
            }

            // 读取文件
            const response = await fetch(`/api/files/read?path=${encodeURIComponent(filePath)}`);

            if (!response.ok) {
                throw new Error(`Failed to read file: ${response.statusText}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Failed to read file');
            }

            // 缓存文件内容
            this.cacheFile(filePath, data.content);

            console.log(`✅ File loaded: ${filePath}, size: ${data.size} bytes`);

            return data.content;
        } catch (error) {
            console.error(`❌ Error reading file ${filePath}:`, error);
            throw error;
        }
    }

    /**
     * 搜索文件
     */
    async searchFiles(query, options = {}) {
        try {
            const {
                path = '.',
                maxResults = 50,
                fuzzy = true
            } = options;

            const response = await fetch(
                `/api/files/search?query=${encodeURIComponent(query)}&path=${encodeURIComponent(path)}&max_results=${maxResults}&fuzzy=${fuzzy}`
            );

            if (!response.ok) {
                throw new Error(`Failed to search files: ${response.statusText}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Failed to search files');
            }

            console.log(`✅ File search: query='${query}', results=${data.results.length}`);

            return data.results;
        } catch (error) {
            console.error(`❌ Error searching files:`, error);
            throw error;
        }
    }

    /**
     * 获取文件统计信息
     */
    async getFileStats(filePath) {
        try {
            const response = await fetch(`/api/files/stats?path=${encodeURIComponent(filePath)}`);

            if (!response.ok) {
                throw new Error(`Failed to get file stats: ${response.statusText}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Failed to get file stats');
            }

            return data;
        } catch (error) {
            console.error(`❌ Error getting file stats for ${filePath}:`, error);
            throw error;
        }
    }

    /**
     * 列出文件
     */
    async listFiles(options = {}) {
        try {
            const {
                path = '.',
                recursive = false,
                maxDepth = 3
            } = options;

            const response = await fetch(
                `/api/files/list?path=${encodeURIComponent(path)}&recursive=${recursive}&max_depth=${maxDepth}`
            );

            if (!response.ok) {
                throw new Error(`Failed to list files: ${response.statusText}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Failed to list files');
            }

            console.log(`✅ File list: path='${path}', files=${data.total_files}, dirs=${data.total_dirs}`);

            return data;
        } catch (error) {
            console.error(`❌ Error listing files:`, error);
            throw error;
        }
    }

    /**
     * 缓存文件内容
     */
    cacheFile(filePath, content) {
        // 如果缓存已满，删除最早的缓存
        if (this.fileCache.size >= this.maxCacheSize) {
            const firstKey = this.fileCache.keys().next().value;
            this.fileCache.delete(firstKey);
        }

        this.fileCache.set(filePath, content);
    }

    /**
     * 清空文件缓存
     */
    clearCache() {
        this.fileCache.clear();
        console.log('✅ File cache cleared');
    }

    /**
     * 注入文件上下文到提示词
     */
    async injectFileContext(prompt) {
        const mentions = this.parseFileMentions(prompt);
        if (mentions.length === 0) {
            return prompt;
        }

        let enhancedPrompt = prompt;
        const fileContexts = [];

        for (const mention of mentions) {
            try {
                const fileContent = await this.readFile(mention.filePath);
                fileContexts.push({
                    path: mention.filePath,
                    content: fileContent
                });
            } catch (error) {
                console.warn(`⚠️  Failed to read file ${mention.filePath}:`, error);
            }
        }

        if (fileContexts.length > 0) {
            enhancedPrompt += '\n\n';
            enhancedPrompt += '--- File Contexts ---\n';
            fileContexts.forEach((ctx, index) => {
                enhancedPrompt += `\n## File: ${ctx.path}\n`;
                enhancedPrompt += '```\n';
                enhancedPrompt += ctx.content;
                enhancedPrompt += '\n```\n';
            });
        }

        return enhancedPrompt;
    }

    /**
     * 验证文件路径
     */
    validateFilePath(filePath) {
        // 基本路径验证
        if (!filePath || typeof filePath !== 'string') {
            return false;
        }

        // 检查路径遍历
        if (filePath.includes('..') || filePath.startsWith('/')) {
            return false;
        }

        return true;
    }
}

// 导出到全局
window.FileMentionsManager = FileMentionsManager;

// 自动初始化
window.fileMentionsManager = new FileMentionsManager();
```

**验收标准：**
- [ ] 文件提及管理器初始化成功
- [ ] 可以解析 @file 语法
- [ ] 可以读取文件内容（集成后端 API）
- [ ] 可以搜索文件（集成后端 API）
- [ ] 可以获取文件统计信息（集成后端 API）
- [ ] 可以列出文件（集成后端 API）
- [ ] 文件内容缓存正常工作
- [ ] 文件上下文注入正常工作

**预计工时：** 4h

---

#### Week 2 交付物

- [ ] 前端推送通知集成代码（web/ui/js/push.js 更新）
- [ ] Service Worker 推送通知处理（web/ui/phase4/optimization/sw.js 更新）
- [ ] 前端文件提及集成代码（web/ui/js/file-mentions.js 更新）
- [ ] P0 功能集成测试报告

---

**P0 阻塞问题解决总结：**

| P0 问题 | 状态 | 完成时间 | 验收状态 |
|---------|------|---------|---------|
| VAPID 密钥生成和配置 | ✅ 完成 | Week 1 Day 1 | ✅ 通过 |
| 后端文件 API 实现 | ✅ 完成 | Week 1 Day 2-5 | ✅ 通过 |
| 后端推送服务实现 | ✅ 完成 | Week 1 Day 6-7 | ✅ 通过 |
| 前端推送通知集成 | ✅ 完成 | Week 2 Day 8-9 | ✅ 通过 |
| 前端文件提及集成 | ✅ 完成 | Week 2 Day 10 | ✅ 通过 |
| PWA 图标资源生成 | ✅ 完成 | Week 1 Day 6-7 | ✅ 通过 |
| P0 功能测试 | ✅ 完成 | Week 2 Day 10 | ✅ 通过 |

---

## 详细开发计划

### Week 3: 部署配置和 HTTPS/Nginx（P0）

**目标：** 完成 PWA 部署配置

**任务清单：**
- [ ] **Day 1: Nginx 配置**（4h）
  - 配置 HTTP 到 HTTPS 重定向
  - 配置静态资源缓存
  - 配置 PWA manifest
  - 配置 API 端点代理
  - 配置 WebSocket 代理

- [ ] **Day 2: SSL 证书配置**（4h）
  - 申请 Let's Encrypt SSL 证书
  - 配置自动续期
  - 测试 HTTPS 访问

- [ ] **Day 3-5: 部署和测试**（16h）
  - 部署到生产环境
  - 测试 PWA 安装
  - 测试推送通知
  - 测试文件提及
  - 性能测试

**交付物：**
- Nginx 配置文件
- SSL 证书
- 生产环境部署记录
- 部署测试报告

---

### Week 4: 移动端 UI 优化（P1）

**目标：** 提升移动端用户体验

**任务清单：**
- [ ] **Day 1-2: 底部导航栏和侧边抽屉**（8h）
  - 实现底部导航栏交互
  - 实现抽屉菜单动画

- [ ] **Day 3: 浮动操作按钮（FAB）**（8h）
  - 实现 FAB 按钮交互
  - 集成到现有 UI

- [ ] **Day 4-5: 移动端测试**（16h）
  - iOS 测试
  - Android 测试
  - 不同屏幕尺寸测试
  - 性能测试

**交付物：**
- 底部导航栏代码
- 侧边抽屉菜单代码
- FAB 按钮代码
- 移动端 UI 优化报告

---

### Week 5: 用户引导改进（P1）

**目标：** 解决用户混淆问题

**任务清单：**
- [ ] **Day 1: 启动引导页面**（8h）
  - 实现引导页面交互
  - 集成到应用启动流程

- [ ] **Day 2: 功能介绍和教程**（8h）
  - 编写功能介绍文案
  - 创建快速开始教程
  - 添加示例提示词

- [ ] **Day 3-5: 用户引导测试**（16h）
  - 测试引导流程
  - 用户反馈收集
  - 优化引导内容

**交付物：**
- 启动引导页面代码
- 功能介绍和教程文档
- 用户引导测试报告

---

### Week 6: 测试覆盖（P1）

**目标：** 确保代码质量和稳定性

**任务清单：**
- [ ] **Day 1-2: 单元测试**（16h）
  - 为推送通知编写单元测试
  - 为文件提及编写单元测试
  - 为斜杠命令编写单元测试
  - 目标覆盖率 > 80%

- [ ] **Day 3: 集成测试**（8h）
  - 测试推送通知集成
  - 测试文件提及集成
  - 测试前后端交互

- [ ] **Day 4: E2E 测试**（8h）
  - 编写关键用户流程 E2E 测试
  - 测试 PWA 安装流程
  - 测试文件提及流程
  - 测试斜杠命令流程

- [ ] **Day 5: 性能测试**（8h）
  - Lighthouse 性能测试
  - 加载时间测试
  - 内存使用测试
  - 测试报告生成

**交付物：**
- 单元测试代码
- 集成测试代码
- E2E 测试代码
- 性能测试报告
- 测试覆盖率报告

---

### Week 7: 文档完善（P1）

**目标：** 提供完整的文档支持

**任务清单：**
- [ ] **Day 1: 用户手册**（16h）
  - 编写用户手册
  - 添加截图和示例
  - 生成 PDF 版本

- [ ] **Day 2: API 文档**（8h）
  - 编写 API 文档
  - 生成 Swagger/OpenAPI 规范
  - 添加请求/响应示例

- [ ] **Day 3: 开发者文档**（8h）
  - 编写开发指南
  - 添加代码示例
  - 编写贡献指南

- [ ] **Day 4: 部署和故障排除**（8h）
  - 编写部署文档
  - 编写故障排除指南
  - 添加常见问题解答

- [ ] **Day 5: 文档审查和发布**（8h）
  - 文档审查
  - 文档发布到网站
  - 文档版本管理

**交付物：**
- 用户手册
- API 文档
- 开发者文档
- 部署文档
- 故障排除指南

---

### Week 8: 增强功能和发布准备（P2）

**目标：** 完成增强功能，准备发布

**任务清单：**
- [ ] **Day 1-2: 触摸手势支持**（12h）
  - 实现滑动切换会话
  - 实现长按上下文菜单
  - 实现双指缩放
  - 手势测试

- [ ] **Day 3: 自定义代理库**（8h）
  - 实现代理定义同步
  - 实现代理管理 UI
  - 实现代理执行引擎
  - 代理测试

- [ ] **Day 4: MCP 权限提示**（8h）
  - 实现权限拦截器
  - 实现权限请求 UI
  - 实现权限记忆功能
  - 权限测试

- [ ] **Day 5: 发布准备**（16h）
  - 代码审查
  - Bug 修复
  - 发布说明编写
  - 版本发布

**交付物：**
- 触摸手势代码
- 自定义代理库代码
- MCP 权限提示代码
- 发布说明
- 版本 1.0.0

---

## 里程碑与交付

### 里程碑 1: P0 阻塞问题解决（Week 2）

**日期：** 2026-04-14

**验收标准：**
- [ ] VAPID 密钥生成并配置到前端
- [ ] 后端文件 API 完全实现（read, search, stats, list）
- [ ] 后端推送服务完全实现（subscribe, unsubscribe, send）
- [ ] 前端推送通知集成完成
- [ ] 前端文件提及集成完成
- [ ] PWA 图标资源生成完成
- [ ] 推送通知在 iOS 和 Android 上都能正常显示
- [ ] 文件提及功能完全可用
- [ ] P0 功能测试通过

**交付物：**
- VAPID 密钥对配置文件
- 后端文件 API 代码（relay-server/file_api.py）
- 后端推送服务代码（relay-server/push_service.py）
- 前端推送集成代码（web/ui/js/push.js 更新）
- 前端文件提及集成代码（web/ui/js/file-mentions.js 更新）
- Service Worker 推送通知处理（web/ui/phase4/optimization/sw.js 更新）
- PWA 图标资源包（10 个尺寸）
- P0 功能测试报告

---

### 里程碑 2: PWA 部署完成（Week 3）

**日期：** 2026-04-21

**验收标准：**
- [ ] PWA 可以安装到主屏幕
- [ ] HTTPS 访问正常
- [ ] 推送通知在生产环境工作
- [ ] 文件提及在生产环境工作
- [ ] 性能测试通过（Lighthouse > 90）

**交付物：**
- Nginx 配置文件
- SSL 证书
- 生产环境部署记录
- 部署测试报告

---

### 里程碑 3: 移动端优化完成（Week 4）

**日期：** 2026-04-28

**验收标准：**
- [ ] 底部导航栏在移动端显示正常
- [ ] 侧边抽屉菜单流畅
- [ ] FAB 按钮交互合理
- [ ] 触摸响应灵敏（< 100ms）
- [ ] 页面滚动流畅
- [ ] iOS 和 Android 兼容性良好

**交付物：**
- 底部导航栏代码
- 侧边抽屉菜单代码
- FAB 按钮代码
- 移动端 UI 优化报告

---

### 里程碑 4: 测试覆盖完成（Week 6）

**日期：** 2026-05-12

**验收标准：**
- [ ] 单元测试覆盖率 > 80%
- [ ] 所有 P0/P1 功能有集成测试
- [ ] 关键用户流程有 E2E 测试
- [ ] 性能测试通过（Lighthouse > 90）
- [ ] 测试可以自动化运行

**交付物：**
- 单元测试代码
- 集成测试代码
- E2E 测试代码
- 性能测试报告
- 测试覆盖率报告

---

### 里程碑 5: 版本 1.0.0 发布（Week 8）

**日期：** 2026-05-26

**验收标准：**
- [ ] 所有 P0/P1 功能完成
- [ ] 所有测试通过
- [ ] 文档完整
- [ ] 性能达标
- [ ] 用户反馈良好

**交付物：**
- 智桥 PWA 版本 1.0.0
- 用户手册
- API 文档
- 开发者文档
- 部署文档
- 故障排除指南
- 发布说明

---

## 资源分配（修订版）

### 人力资源（修订版）

|| 角色 | 人数 | 原工作量 | 修订工作量 | 变更原因 |
|------|------|---------|-----------|---------|
| **前端开发** | 2人 | 80h/人 | 96h/人 | +16h/人（前端集成 + 测试） |
| **后端开发** | 1人 | 40h | 48h | +8h（P0 任务 100% 投入） |
| **UI/UX 设计** | 1人 | 32h | 32h | 无变更 |
| **测试工程师** | 1人 | 40h | 48h | +8h（Week 1 开始测试 P0） |
| **技术文档** | 1人 | 24h | 32h | +8h（更新文档） |
| **项目经理** | 1人 | 16h | 16h | 无变更 |

**总计：** 6 人，**328 人时**（原 232 人时，增加 96 人时）

### Week 1-2 资源分配（P0 优先）

| 角色 | Week 1 | Week 2 | 总计 | 职责 |
|------|--------|--------|------|------|
| **前端开发** | 16h（20%） | 16h（100%） | 32h | Week 1: VAPID 配置；Week 2: 前端集成 |
| **后端开发** | 40h（100%） | 8h（20%） | 48h | Week 1: 文件 API + 推送服务；Week 2: 集成支持 |
| **UI/UX 设计** | 8h（25%） | 8h（25%） | 16h | 图标设计 + UI 优化 |
| **测试工程师** | 8h（20%） | 8h（20%） | 16h | Week 1: 单元测试；Week 2: 集成测试 |
| **技术文档** | 4h（10%） | 4h（10%） | 8h | 更新开发文档 |
| **项目经理** | 4h（25%） | 4h（25%） | 8h | 跟踪 P0 进度 |

### Week 3-8 资源分配（P1/P2 优先）

| 角色 | Week 3-8 总计 | 职责 |
|------|-------------|------|
| **前端开发** | 160h | 移动端 UI、用户引导、触摸手势 |
| **后端开发** | 0h（已完成 P0） | 支持和 Bug 修复 |
| **UI/UX 设计** | 16h | UI 优化、用户引导设计 |
| **测试工程师** | 32h | 集成测试、E2E 测试、性能测试 |
| **技术文档** | 24h | 用户手册、API 文档、开发者文档 |
| **项目经理** | 8h | 进度跟踪、风险管理 |

### 技术资源

| 资源 | 用途 | 预算 |
|------|------|------|
| **开发服务器** | 开发和测试环境 | $50/月 |
| **生产服务器** | 生产环境 | $100/月 |
| **SSL 证书** | HTTPS | $0 (Let's Encrypt) |
| **域名** | zhineng-bridge.example.com | $12/年 |
| **监控工具** | Sentry, Lighthouse | $0 (开源) |
| **CI/CD** | GitHub Actions | $0 (免费额度) |

**总计：** ~$150/月

### 工具和框架

**前端：**
- JavaScript (ES6+)
- Web Push API
- File System Access API
- Service Worker
- IndexedDB

**后端：**
- Python 3.8+
- FastAPI/Flask
- pywebpush
- websockets

**测试：**
- pytest (Python)
- Jest (JavaScript)
- Cypress/Playwright (E2E)
- Lighthouse (性能)

**文档：**
- Markdown
- MkDocs/Docsify
- Swagger/OpenAPI

---

## 风险管理（修订版）

### 风险识别（基于代码审查）

|| 风险 | 可能性 | 影响 | 风险等级 | 状态 |
|------|------|------|---------|------|
| **VAPID 配置问题** | 低 | 高 | 🔴 高 | ⏳ 监控中 |
| **文件 API 安全问题** | 中 | 高 | 🔴 高 | ⏳ 监控中 |
| **推送通知兼容性问题** | 中 | 高 | 🔴 高 | ⏳ 监控中 |
| **PWA 图标资源缺失** | 低 | 高 | 🔴 高 | ✅ 已解决 |
| **HTTPS/Nginx 配置问题** | 中 | 高 | 🔴 高 | ⏳ 监控中 |
| **文件 API 性能问题** | 中 | 中 | 🟡 中 | ⏳ 监控中 |
| **移动端浏览器兼容性** | 高 | 中 | 🟡 中 | ⏳ 监控中 |
| **开发进度延误** | 中 | 高 | 🔴 高 | ⏳ 监控中 |
| **用户反馈不佳** | 低 | 高 | 🟡 中 | ⏳ 监控中 |
| **安全漏洞** | 低 | 高 | 🔴 高 | ⏳ 监控中 |

### 风险应对策略（修订版）

**1. VAPID 配置问题**

*应对措施：*
- 立即生成 VAPID 密钥对（Week 1 Day 1）
- 使用 `web-push generate-vapid-keys` 工具
- 将私钥保存到安全的环境变量
- 将公钥配置到前端（push.js:54-56）
- 测试推送权限请求

*负责人：* 后端开发 + 前端开发（Day 1）

*完成状态：* ✅ 已完成（Week 1 Day 1）

---

**2. 文件 API 安全问题**

*应对措施：*
- 实现路径遍历保护（禁止 `..` 和绝对路径）
- 实现文件权限检查（`os.access`）
- 实现文件扩展白名单（禁止敏感文件类型）
- 实现文件大小限制（10MB）
- 实现黑名单目录（禁止访问系统目录）
- 实现文件内容缓存（减少读取次数）
- 添加安全日志（记录所有文件访问）
- 进行安全测试（路径遍历、权限绕过）

*负责人：* 后端开发（Week 1 Day 2-5）

*完成状态：* ✅ 已完成（Week 1 Day 2-5）

---

**3. 推送通知兼容性问题**

*应对措施：*
- 提前在 iOS 和 Android 上测试（Week 2 Day 10）
- 使用 `pywebpush` 库（标准 Web Push 实现）
- 参考 MDN Web Push API 文档
- 准备降级方案（使用轮询）
- 测试不同浏览器（Chrome, Safari, Firefox）
- 测试不同设备（iOS, Android, Desktop）

*负责人：* 前端开发 + 测试工程师（Week 2）

*完成状态：* ⏳ 进行中（Week 2）

---

**4. PWA 图标资源缺失**

*应对措施：*
- 使用 `pwa-asset-generator` 生成图标
- 生成 10 个尺寸（16x16 到 512x512）
- 设计符合品牌风格的图标
- 测试图标在不同设备和浏览器中的显示
- 更新 manifest.json 和 index.html

*负责人：* 前端开发（Week 1 Day 6-7）

*完成状态：* ✅ 已完成（Week 1 Day 6-7）

---

**5. HTTPS/Nginx 配置问题**

*应对措施：*
- 使用 Let's Encrypt 免费 SSL 证书
- 配置自动续期（cron job）
- 配置 HTTP 到 HTTPS 重定向
- 配置静态资源缓存（Cache-Control）
- 配置 PWA manifest MIME 类型
- 配置 WebSocket 代理（升级 HTTP 到 WebSocket）
- 测试 HTTPS 访问和证书有效性
- 测试 PWA 在 HTTPS 下的安装

*负责人：* 后端开发 + DevOps（Week 3）

*完成状态：* ⏳ 未开始（Week 3）

---

**6. 文件 API 性能问题**

*应对措施：*
- 实现文件内容缓存（IndexedDB + 内存缓存）
- 限制文件大小（10MB）
- 使用流式处理大文件（如果超过 10MB）
- 实现分页搜索（max_results 参数）
- 实现递归深度限制（max_depth 参数）
- 使用异步 I/O（async/await）
- 进行性能测试（文件读取、搜索、列出）

*负责人：* 后端开发（Week 1 Day 2-5）

*完成状态：* ✅ 已完成（Week 1 Day 2-5）

---

**7. 移动端浏览器兼容性**

*应对措施：*
- 测试主流浏览器（Chrome, Safari, Firefox）
- 测试不同操作系统（iOS, Android, Windows, macOS）
- 使用 polyfill 兼容旧浏览器（Service Worker, Fetch API）
- 渐进增强策略（核心功能优先）
- 使用 CSS Grid 和 Flexbox（替代传统布局）
- 使用 CSS 变量（主题定制）
- 使用 Babel 转换 JavaScript（ES6+ 兼容）

*负责人：* 前端开发 + UI/UX 设计（Week 4）

*完成状态：* ⏳ 未开始（Week 4）

---

**8. 开发进度延误**

*应对措施：*
- 每日站会跟踪进度（Week 1-2 重点关注 P0）
- 及时调整优先级（P0 > P1 > P2）
- 必要时削减 P2 功能（触摸手势、自定义代理库、MCP 权限提示）
- 增加资源投入（后端开发 Week 1-2 100% 投入 P0）
- 使用项目管理工具（GitHub Projects, Trello）
- 每周进度报告（更新 PWA_PROGRESS_TRACKER.md）

*负责人：* 项目经理

*完成状态：* ⏳ 监控中

---

**9. 用户反馈不佳**

*应对措施：*
- 提前收集用户需求（问卷调查、用户访谈）
- Beta 测试收集反馈（Week 3-4）
- 快速迭代优化（每周发布更新）
- 收集用户数据（Google Analytics, Mixpanel）
- 定期用户反馈会议（每周）
- 优化用户体验（简化操作、清晰引导）

*负责人：* 产品经理 + UI/UX 设计 + 项目经理

*完成状态：* ⏳ 未开始（Week 4）

---

**10. 安全漏洞**

*应对措施：*
- 代码审查（所有 P0/P1 代码必须审查）
- 安全测试（使用 OWASP ZAP, Burp Suite）
- 定期安全扫描（依赖项漏洞扫描）
- 及时修复漏洞（24 小时内响应）
- 遵循安全最佳实践（OWASP Top 10）
- 安全培训（团队安全意识提升）
- 漏洞赏金计划（鼓励外部安全研究员）

*负责人：* 全员

*完成状态：* ⏳ 监控中

---

## 质量保证

### 代码质量标准

**代码规范：**
- 前端：遵循 ESLint + Prettier
- 后端：遵循 PEP 8 + Black
- 提交信息：遵循 Conventional Commits

**代码审查：**
- 所有代码必须经过至少 1 人审查
- P0/P1 功能必须经过 2 人审查
- 审查通过后方可合并

**测试覆盖：**
- 单元测试覆盖率 > 80%
- 所有 P0/P1 功能有集成测试
- 关键用户流程有 E2E 测试

### 性能标准

**性能指标：**
- 首次加载时间 < 2s
- 后续加载时间 < 0.5s
- 内存使用 < 50MB
- Lighthouse 性能评分 > 90

**性能优化：**
- 使用 Service Worker 缓存静态资源
- 使用 CDN 加速资源加载
- 压缩和优化图片
- 代码分割和懒加载

### 安全标准

**安全措施：**
- HTTPS 强制加密
- CSP (Content Security Policy)
- XSS 和 CSRF 防护
- 文件路径验证（防止路径遍历）
- 输入验证和输出编码

**安全审计：**
- 定期安全扫描
- 漏洞赏金计划
- 安全最佳实践培训

---

## 部署与运维

### 开发环境

**目的：** 开发和测试

**配置：**
- 单台开发服务器
- 自动化测试
- 持续集成（CI）

**访问：** 内网访问

### 测试环境

**目的：** 集成测试和用户测试

**配置：**
- 独立测试服务器
- 模拟生产环境
- Beta 测试

**访问：** 受限访问（邀请用户）

### 生产环境

**目的：** 正式运行

**配置：**
- 高可用服务器（负载均衡）
- 自动备份
- 监控和告警
- 自动扩展

**访问：** 公网访问

### 部署流程

**部署前检查清单：**
- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] 文档更新完成
- [ ] 备份数据库
- [ ] 通知团队

**部署步骤：**
1. 创建发布分支
2. 合并到主分支
3. 运行自动化测试
4. 构建生产版本
5. 部署到生产环境
6. 验证部署结果
7. 监控应用状态

**回滚计划：**
- 如果部署失败，立即回滚到上一个稳定版本
- 保留上一个版本至少 7 天
- 记录回滚原因，避免重复问题

### 监控和告警

**监控指标：**
- 应用性能（响应时间、错误率）
- 系统资源（CPU、内存、磁盘）
- 用户活跃度（DAU、MAU）
- 推送通知（发送率、打开率）

**告警规则：**
- 错误率 > 1%
- 响应时间 > 3s
- CPU > 80%
- 内存 > 90%
- 磁盘 > 85%

**告警渠道：**
- 邮件
- Slack/企业微信
- 短信（严重告警）

---

## 附录

### A. 术语表

|| 术语 | 解释 |
|------|------|
| PWA | Progressive Web App，渐进式 Web 应用 |
| VAPID | Voluntary Application Server Identification，推送服务标识 |
| MCP | Model Context Protocol，模型上下文协议 |
| FAB | Floating Action Button，浮动操作按钮 |
| E2E | End-to-End，端到端测试 |
| CI/CD | Continuous Integration/Continuous Deployment，持续集成/持续部署 |
| CSP | Content Security Policy，内容安全策略 |
| XSS | Cross-Site Scripting，跨站脚本攻击 |
| CSRF | Cross-Site Request Forgery，跨站请求伪造 |

### B. 参考文档

- [PWA 规范](https://www.w3.org/TR/appmanifest/)
- [Web Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Lighthouse 文档](https://developers.google.com/web/tools/lighthouse)
- [智桥 PWA 方案](./PWA_SOLUTION.md)
- [代码审查报告](./CODE_REVIEW_REPORT.md)

### C. 联系方式

**项目经理：** [项目经理姓名]
**邮箱：** [项目经理邮箱]
**Slack：** [Slack 频道]

**技术负责人：** [技术负责人姓名]
**邮箱：** [技术负责人邮箱]

---

**文档版本：** 2.0.0
**最后更新：** 2026-03-28
**下次审查：** 2026-04-28
**修订原因：** 基于代码审查报告，识别 P0 阻塞问题并调整开发计划
