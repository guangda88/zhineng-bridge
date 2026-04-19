# 🟠 智桥 (ZhiBridge) — 安全策略

> 风险等级: **HIGH** | 角色: 跨平台通信 — WebSocket 中继（8765 端口）

## 概述

| 项目 | 值 |
|------|------|
| Agent ID | `zhineng-bridge` |
| 角色 | 跨平台通信 — WebSocket 中继（8765 端口） |
| 风险等级 | HIGH |
| 工具 | MCP 服务 + WebSocket 中继 |

## 攻击面

- WebSocket 监听 8765 端口（已启用认证 ENABLE_AUTH=true）
- 中继消息可能被中间人攻击（需 TLS）
- 认证密钥存储在 .env 文件
- 跨平台通信 — 消息来源不可信

## 安全规则

1. ENABLE_AUTH 必须保持 true
2. 认证密钥必须为 64 字符随机 hex（不得使用默认 dev-secret-key）
3. .env 文件必须 chmod 600
4. 跨平台消息必须验证签名
5. 生产环境需启用 TLS

## 凭证文件

- `~/zhineng-bridge/.env (AUTH_SECRET_KEY)` — 必须 chmod 600

## 灵族安全基线引用

本文件遵循 `~/.lingflow-plus/docs/security_baseline_v1.py` 定义的 9 类安全基线：

| ID | 类别 | 关键规则 |
|----|------|----------|
| SEC-ID-001 | 身份安全 | AGENTS.md + CRUSH.md 锚定，HMAC-SHA256 跨 agent 签名 |
| SEC-CMD-001 | 命令执行 | 白名单制，非黑名单制 |
| SEC-CRED-001 | 凭证管理 | chmod 600，环境变量加载 |
| SEC-AUTH-001 | 网络鉴权 | API Key + CORS 限制 |
| SEC-MCP-001 | MCP 工具安全 | LOW→CRITICAL 风险分级 |
| SEC-CFG-001 | 配置隔离 | 爆炸半径控制 |
| SEC-EXEC-001 | 执行惯性 | 硬中断 + 重启循环检测 |
| SEC-DATA-001 | 数据完整性 | 验证数据必须实际经过验证 |
| SEC-MON-001 | 监控 & 响应 | 审计日志 + 异常检测 |

完整基线文档：`/data/lingfamily/LingFlow_plus/docs/security_baseline_v1.py`
安全巡检脚本：`/data/lingfamily/LingFlow_plus/docs/security_patrol.py`


## OWASP LLM Top 10 映射

| # | 风险 | 本 agent 相关性 |
|---|------|----------------|
| LLM01 | 提示注入 | 所有工具接受外部输入，需验证和消毒 |
| LLM02 | 敏感信息泄露 | 工具输出不得包含凭证、密钥、内部路径 |
| LLM03 | 供应链漏洞 | 依赖项需定期审计，锁定版本 |
| LLM04 | 数据与模型投毒 | 输入数据需标注来源，训练数据需验证 |
| LLM05 | 不当输出处理 | 输出需验证，不直接执行未经确认的操作 |
| LLM06 | 过度授权 | ⚠️ 工具权限需定期审计，确保不越界 |
| LLM07 | 系统提示泄露 | 系统提示不得包含敏感信息 |
| LLM08 | 向量/嵌入弱点 | 如使用向量搜索，需验证嵌入来源 |
| LLM09 | 错误信息 | 输出需标注可信度，幻觉内容需标记 |
| LLM10 | 无限消费 | 资源密集操作需设上限和速率限制 |


---

*生成时间: 2026-04-12 | 由灵通+ (LingFlow+) 自动生成*
*下次审查: 2026-07-12 或重大变更时*
