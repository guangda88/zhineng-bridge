# Chrome DevTools MCP - 快速开始指南

根据 GitHub 仓库 https://github.com/ChromeDevTools/chrome-devtools-mcp 安装和测试完成。

## 快速开始

### 1. 运行 E2E 测试

```bash
cd /home/ai/zhibridge
python3 chrome_devtools_mcp_e2e_test.py
```

### 2. 查看测试结果

```bash
cat chrome_devtools_e2e_test_results.json
```

### 3. 查看截图

```bash
ls -lh /tmp/zhineng_bridge_test.png
```

## 测试结果摘要

- **测试通过率**: 100% (6/6)
- **执行时间**: 3.07 秒
- **所有测试**: ✅ 通过

## 测试覆盖

1. ✅ 页面导航
2. ✅ 页面标题获取
3. ✅ 页面截图
4. ✅ WebSocket 连接
5. ✅ 页面元素检查
6. ✅ 控制台错误检查

## 文档

- [完成报告](chrome_devtools_mcp_e2e_test_completion_report.md) - 详细的任务完成报告
- [进度文档](chrome_devtools_mcp_e2e_test_progress.md) - 完整的实施进度
- [E2E 测试指南](docs/E2E_TESTING_WITH_CHROME_DEVTOOLS_MCP.md) - 测试使用指南

## Docker 镜像

- **名称**: chrome-devtools-mcp:latest
- **大小**: 1.23GB
- **包含**: Node.js v20.20.2, Chromium, Puppeteer, chrome-devtools-mcp

## 常用命令

```bash
# 启动 chrome-devtools-mcp (无头模式)
docker run --rm --network host chrome-devtools-mcp:latest \
  npx -y chrome-devtools-mcp@latest --headless=true

# 查看帮助
docker run --rm chrome-devtools-mcp:latest \
  npx -y chrome-devtools-mcp@latest --help

# 自定义视口
docker run --rm --network host chrome-devtools-mcp:latest \
  npx -y chrome-devtools-mcp@latest --viewport=1920x1080
```

## 注意事项

1. 确保 Relay Server 正在运行:
   ```bash
   cd /home/ai/zhibridge/relay-server
   python3 start_server.py
   ```

2. Docker 需要 `--network host` 或 `--add-host host.docker.internal:host-gateway` 来访问宿主机服务

3. 无头模式适合 CI/CD 环境，有头模式适合开发调试

## 故障排查

### Docker 构建失败

```bash
# 重新构建镜像
docker build -f Dockerfile.chrome-devtools -t chrome-devtools-mcp:latest .
```

### 测试失败

```bash
# 检查 Relay Server 状态
ps aux | grep start_server.py

# 检查端口占用
netstat -tuln | grep -E ':(8000|8765)'
```

### WebSocket 连接失败

确保 Relay Server 正在运行并且端口 8765 可访问。

---

**状态**: ✅ 安装和测试完成
**日期**: 2026-03-27
