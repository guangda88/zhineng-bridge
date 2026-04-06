"""根页面 HTML — 从 handlers.py 中提取"""

ROOT_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智桥 (Zhineng-Bridge) - 健康检查服务器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .logo {
            font-size: 48px;
            margin-bottom: 10px;
        }
        h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        .version {
            color: #666;
            font-size: 14px;
        }
        .endpoints {
            display: grid;
            gap: 15px;
            margin-bottom: 30px;
        }
        .endpoint {
            display: flex;
            align-items: center;
            padding: 15px 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        .endpoint:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }
        .endpoint a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            flex: 1;
        }
        .endpoint a:hover {
            color: #764ba2;
        }
        .method {
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 15px;
        }
        .description {
            color: #666;
            font-size: 14px;
            margin-left: 10px;
        }
        .footer {
            text-align: center;
            color: #999;
            font-size: 14px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        .status {
            display: inline-block;
            padding: 6px 16px;
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🌉</div>
            <h1>智桥 (Zhineng-Bridge)</h1>
            <div class="version">版本 1.0.0 | 跨平台实时同步和通信 SDK</div>
            <div class="status">✅ 服务运行正常</div>
        </div>

        <h2 style="color: #333; margin-bottom: 20px;">📡 可用端点</h2>
        <div class="endpoints">
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/health">/health</a>
                <span class="description">健康检查</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/status">/status</a>
                <span class="description">服务状态和配置</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/metrics">/metrics</a>
                <span class="description">性能指标</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/prometheus">/prometheus</a>
                <span class="description">Prometheus 指标</span>
            </div>
            <div class="endpoint" style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);">
                <span class="method">GET</span>
                <a href="/docs" style="color: #764ba2;">/docs</a>
                <span class="description">📘 API 文档 (Swagger UI)</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/openapi.yaml">/openapi.yaml</a>
                <span class="description">OpenAPI 规范</span>
            </div>
        </div>

        <div class="footer">
            <p>支持 8 个 AI 编码工具：Crush, Claude Code, iFlow CLI, Cursor, Trae, Droid, OpenClaw, GitHub Copilot</p>
            <p style="margin-top: 10px;">
                <a href="https://github.com/guangda88/zhineng-bridge" target="_blank">GitHub</a> |
                <a href="http://zhinenggitea.iepose.cn/guangda/zhineng-bridge" target="_blank">Gitea</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
