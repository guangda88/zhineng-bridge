# 常见问题解答

## Q: simple_chat.py 的正确用法是什么？

**A**: `simple_chat.py` 是与 Crush **AI对话**的工具，不是终端命令执行器。

### ✅ 正确用法：AI对话

```
👤 You: What is 2+2?
💬 Crush:
4

👤 You: 用中文解释什么是Python？
💬 Crush:
Python是一种高级编程语言...

👤 You: Write a function to merge two sorted lists
💬 Crush:
```python
def merge_sorted_lists(list1, list2):
    ...
```
```

### ❌ 错误用法：终端命令

```
👤 You: ls              # ❌ 这是终端命令
💬 Crush:
ls是一个Unix-like操作系统的命令，用于列出目录内容...

👤 You: /model          # ❌ 这是错误的模型切换方式
💬 Crush:
/model不是一个有效的提示...

👤 You: cd /home        # ❌ 这是终端命令
💬 Crush:
cd命令用于切换目录...
```

## Q: 如何切换模型？

**A**: 使用 `model` 命令（不是 `/model`）

```
👤 You: model
📋 当前模型: zai/glm-4.5
📋 可用模型: zai/glm-4.5, zai/glm-4.5-air, zai/glm-4.6, zai/glm-4.7

👤 You: model zai/glm-4.6
✅ 模型已切换到: zai/glm-4.6
```

## Q: 如果需要执行终端命令怎么办？

**A**: `simple_chat.py` 不支持执行终端命令。你有两个选项：

### 选项1: 直接在终端执行

打开新的终端窗口：
```bash
# 列出文件
ls -la

# 查看可用模型
crush models

# 切换目录
cd /home

# 查看文件内容
cat file.txt
```

### 选项2: 让Crush解释命令，然后手动执行

```
👤 You: 告诉我如何列出当前目录的所有文件，包括隐藏文件？

💬 Crush:
要列出当前目录的所有文件，包括隐藏文件（以.开头的文件），你可以使用：

Linux/macOS:
```bash
ls -la
```

Windows PowerShell:
```powershell
Get-ChildItem -Force
```

选项说明：
- -l: 使用长格式显示
- -a: 显示所有文件，包括隐藏文件
```

然后在你的终端执行 `ls -la`。

## Q: 我收到了 "ConnectionClosedOK" 错误

**A**: 这是正常的WebSocket行为，不是错误。

### 解释

当客户端正常关闭连接后，服务器还尝试发送消息（如session_stopped确认）时，会产生这个错误。这是WebSocket协议的正常行为。

### 影响

- **功能**: 无影响
- **用户体验**: 无影响
- **需要修复**: 不需要

### 示例日志

```
{"error": "received 1000 (OK); then sent 1000 (OK)",
 "event": "Failed to send message",
 "level": "error",
 ...
}
```

## Q: 为什么有时输出很慢？

**A**: Crush的首次输出延迟是固有特性。

### 响应时间

| 模型 | 平均响应时间 |
|------|-------------|
| zai/glm-4.5 | 11.18秒 |
| zai/glm-4.5-air | 11.02秒 |
| zai/glm-4.6 | 29.19秒 |
| zai/glm-4.7 | 27.38秒 |

### 原因

1. **模型初始化**: Crush需要加载和初始化模型
2. **网络延迟**: API请求需要时间
3. **计算复杂度**: 复杂问题需要更多计算

### 解决方案

1. 使用 `zai/glm-4.5` 模型（最快）
2. 简化问题
3. 使用流式输出（已默认启用）

## Q: 超时了怎么办？

**A**: 使用重试机制或简化问题

### 重试

```
👤 You: Write a comprehensive guide about software engineering

[10秒无新消息]
⏱️  超时：Crush思考时间太长了，可能问题太复杂
💡 提示: 输入 'retry' 重试，或简化问题

👤 You: retry
🔄 重试第 1 次...
[成功获得回复]
```

### 简化问题

将复杂问题分解为多个简单问题：

**❌ 太复杂**:
```
👤 You: Write a comprehensive guide about software engineering covering: 1) Requirements gathering and analysis, 2) System design and architecture patterns, 3) Database design principles, 4) API design best practices, 5) Testing strategies (unit, integration, E2E), 6) CI/CD pipelines, 7) Monitoring and observability, 8) Security best practices, 9) Performance optimization, 10) Code review processes. For each topic, provide detailed explanations, examples, and best practices.
```

**✅ 分解后**:
```
👤 You: What is software engineering?
💬 Crush: [回答]

👤 You: What are the main phases of software development?
💬 Crush: [回答]

👤 You: What is requirements gathering?
💬 Crush: [回答]
```

## Q: 如何查看可用模型？

**A**: 使用 `model` 命令查看当前模型和可用模型列表。

```
👤 You: model
📋 当前模型: zai/glm-4.5
📋 可用模型: zai/glm-4.5, zai/glm-4.5-air, zai/glm-4.6, zai/glm-4.7
```

## Q: 哪个模型最好？

**A**: 根据你的需求选择。

### zai/glm-4.5 ⭐⭐⭐⭐（推荐）

**适用场景**:
- 日常对话
- 快速问答
- 代码生成
- 一般编程问题

**性能**:
- 平均响应: 11.18秒
- 成功率: 100%
- 稳定性: 最高

### zai/glm-4.5-air ⭐⭐⭐

**适用场景**:
- 简单问答
- 不需要代码生成的任务
- 需要更详细输出的场景

**性能**:
- 平均响应: 11.02秒（最快）
- 成功率: 75%
- 注意: 代码生成可能超时

### zai/glm-4.6 ⭐⭐⭐

**适用场景**:
- 复杂问题
- 需要深度推理的任务
- 不在意响应时间的场景

**性能**:
- 平均响应: 29.19秒
- 成功率: 100%
- 注意: 响应较慢

### zai/glm-4.7 ⭐⭐⭐

**适用场景**:
- 复杂问题
- 需要深度推理的任务

**性能**:
- 平均响应: 27.38秒
- 成功率: 75%
- 注意: 代码生成可能超时

## Q: 如何退出对话？

**A**: 使用以下任一命令：

```
👤 You: quit
👋 对话结束

👤 You: exit
👋 对话结束

👤 You: q
👋 对话结束

👤 You: 退出
👋 对话结束
```

## Q: 我可以重试消息吗？

**A**: 可以，使用 `retry` 命令。

```
👤 You: Explain quantum computing in detail

[超时]

👤 You: retry
🔄 重试第 1 次...
[成功获得回复]
```

最多可以重试3次。

## Q: 服务连接失败怎么办？

**A**: 检查服务器状态并重新启动。

### 检查状态

```bash
# 检查relay server
pgrep -f "python3.*server.py"

# 检查session manager
pgrep -f "python3.*start_manager.py"
```

### 如果未运行，重新启动

```bash
# 终端1: 启动relay server
cd relay-server
python3 start_server.py

# 终端2: 启动session manager
cd phase1/session_manager
python3 start_manager.py
```

### 查看日志

```bash
# Relay server日志
tail -f /tmp/relay_server.log

# Session manager日志
tail -f /tmp/session_manager.log
```

## Q: 我应该向Crush问什么？

**A**: 你可以问任何编程或技术相关的问题。

### 好的问题示例

```
👤 You: What is the difference between list and tuple in Python?
💬 Crush: [详细解释]

👤 You: Write a function to merge two sorted lists
💬 Crush: [提供代码]

👤 You: Explain how HTTP works
💬 Crush: [详细说明]

👤 You: What are best practices for writing Python code?
💬 Crush: [提供最佳实践]
```

### 不好的问题示例

```
👤 You: ls
💬 Crush: ls是一个Unix命令，用于列出文件... [这不是AI对话]

👤 You: tell me a joke
💬 Crush: [可能回答，但不是最佳用途]
```

## Q: 如何获得更好的回答？

**A**: 遵循以下最佳实践。

### 1. 具体明确

```
❌ 不明确: "What's the difference?"
✅ 具体明确: "Explain the difference between list and tuple in Python"
```

### 2. 提供上下文

```
❌ 无上下文: "Why is this not working?"
✅ 有上下文: "I'm getting an IndexError in this Python code. Here's the code..."
```

### 3. 使用简洁的语言

```
❌ 过长: "I would like to ask you if you could please help me understand what is going on when I try to run my Python program..."
✅ 简洁: "Why is my Python program failing with this error?"
```

### 4. 选择合适的模型

| 场景 | 推荐模型 |
|------|---------|
| 快速问答 | zai/glm-4.5-air |
| 代码生成 | zai/glm-4.5 |
| 复杂问题 | zai/glm-4.6 |
| 日常对话 | zai/glm-4.5 |

## 相关文档

- **用户指南**: `docs/CHAT_USER_GUIDE.md`
- **模型性能**: `docs/CRUSH_MODEL_BENCHMARK.md`
- **优化报告**: `docs/CONVERSATION_OPTIMIZATION_REPORT.md`
- **Agent指南**: `AGENTS.md`

## 仍然有问题？

如果这个FAQ没有解决你的问题：

1. 查看日志: `tail -f /tmp/relay_server.log`
2. 检查错误: `grep -i error /tmp/relay_server.log`
3. 查看完整的用户指南: `docs/CHAT_USER_GUIDE.md`

---

**最后更新**: 2026-03-28
**版本**: v1.0.0
