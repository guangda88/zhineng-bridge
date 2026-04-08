#!/usr/bin/env python3
"""
智桥公网配置更新脚本
配置公网IP: 100.66.1.8
"""

from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path("/home/ai/zhineng-bridge")

# 公网配置
PUBLIC_IP = "100.66.1.8"
HTTP_PORT = "8080"
WS_PORT = "8765"

print("="*60)
print("  智桥 (Zhineng-bridge) 公网访问配置")
print("="*60)
print(f"公网IP: {PUBLIC_IP}")
print(f"HTTP端口: {HTTP_PORT}")
print(f"WebSocket端口: {WS_PORT}")
print()

# 1. 更新client.js配置
print("1️⃣  更新前端WebSocket配置...")
client_js = PROJECT_ROOT / "web/ui/js/client.js"

if client_js.exists():
    with open(client_js, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经配置
    if PUBLIC_IP in content:
        print(f"✅ 前端已配置公网IP: {PUBLIC_IP}")
    else:
        # 更新默认主机列表
        old_line = "const wsHosts = window.ZHINENG_BRIDGE_CONFIG?.WS_HOSTS || ['100.66.1.8', '10.113.22.99'];"
        new_line = f"const wsHosts = window.ZHINENG_BRIDGE_CONFIG?.WS_HOSTS || ['{PUBLIC_IP}', '10.113.22.99', 'localhost'];"

        if old_line in content:
            content = content.replace(old_line, new_line)
            with open(client_js, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已更新前端配置，公网IP: {PUBLIC_IP}")
        else:
            print("⚠️  未找到配置行，可能已更新")
else:
    print(f"❌ 文件不存在: {client_js}")

# 2. 创建公网访问配置文件
print("\n2️⃣  创建公网访问配置文件...")
config_file = PROJECT_ROOT / "config" / "public_config.ini"

config_content = f"""[public]
# 公网访问配置
public_ip = {PUBLIC_IP}
http_port = {HTTP_PORT}
ws_port = {WS_PORT}

# 访问地址
http_url = http://{PUBLIC_IP}:{HTTP_PORT}/web/ui/index.html
ws_url = ws://{PUBLIC_IP}:{WS_PORT}
health_url = http://{PUBLIC_IP}:{HTTP_PORT}/health

# 服务说明
status = active
description = 智桥公网访问配置
date = 2026-03-29

[notes]
# 使用说明
1. 确保智桥服务正在运行
2. 确保端口{HTTP_PORT}和{WS_PORT}开放
3. 在任何设备浏览器访问: http://{PUBLIC_IP}:{HTTP_PORT}/web/ui/index.html
4. 手机和电脑都可以访问

# 移动端使用
iOS Safari: 访问地址 → 分享 → 添加到主屏幕
Android Chrome: 菜单 → 安装应用
"""

config_file.parent.mkdir(parents=True, exist_ok=True)
with open(config_file, 'w', encoding='utf-8') as f:
    f.write(config_content)
print(f"✅ 配置文件已创建: {config_file}")

# 3. 创建公网访问快捷方式
print("\n3️⃣  创建公网访问快捷方式...")
access_file = PROJECT_ROOT / "PUBLIC_ACCESS.txt"

access_content = f"""智桥 (Zhineng-bridge) 公网访问
=====================================

🌐 公网访问地址
--------------------------------------
HTTP访问: http://{PUBLIC_IP}:{HTTP_PORT}/web/ui/index.html

📱 移动端访问
--------------------------------------
1. 确保手机有网络连接（WiFi或4G/5G）
2. 打开浏览器
3. 访问: http://{PUBLIC_IP}:{HTTP_PORT}/web/ui/index.html
4. 选择工具，创建会话，发送命令

📲 PWA安装（推荐）
--------------------------------------
iOS Safari:
  - 访问上面地址
  - 点击分享按钮
  - 选择"添加到主屏幕"
  - 点击"添加"

Android Chrome:
  - 访问上面地址
  - 点击菜单（三个点）
  - 选择"安装应用"
  - 点击"安装"

✨ 功能列表
--------------------------------------
✅ 创建和管理AI会话
✅ 实时查看AI输出
✅ 发送命令给AI工具
✅ 文件提及功能
✅ PWA离线缓存
✅ 响应式移动界面

🔧 服务管理
--------------------------------------
启动服务:
  cd /home/ai/zhineng-bridge/relay-server
  python3 start_server.py &

  cd /home/ai/zhineng-bridge/phase1/session_manager
  python3 start_manager.py &

查看日志:
  tail -f /tmp/relay_server.log
  tail -f /tmp/session_manager.log

停止服务:
  pkill -f "start_server.py"
  pkill -f "start_manager.py"

📋 检查清单
--------------------------------------
[ ] 智桥服务正在运行
[ ] 端口{HTTP_PORT}和{WS_PORT}开放
[ ] 手机可以访问公网
[ ] 浏览器可以打开访问地址

❓ 常见问题
--------------------------------------
Q: 无法访问？
A: 检查服务是否运行，端口是否开放

Q: WebSocket连接失败？
A: 检查{WS_PORT}端口是否开放，服务是否正常

Q: PWA无法安装？
A: 使用Chrome或Safari，清除浏览器缓存重试

=====================================
最后更新: 2026-03-29
"""

with open(access_file, 'w', encoding='utf-8') as f:
    f.write(access_content)
print(f"✅ 快捷访问文件已创建: {access_file}")

# 4. 创建公网访问测试脚本
print("\n4️⃣  创建公网访问测试脚本...")
test_script = PROJECT_ROOT / "scripts" / "test_public_ip.py"

test_content = f'''#!/usr/bin/env python3
"""
测试公网访问 {PUBLIC_IP}
"""

import socket
import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket():
    """测试WebSocket连接"""
    print(f"\\n📡 测试WebSocket连接: ws://{PUBLIC_IP}:{WS_PORT}")

    try:
        async with websockets.connect(f"ws://{PUBLIC_IP}:{WS_PORT}") as ws:
            print("✅ WebSocket连接成功")

            # 发送ping
            await ws.send(json.dumps({{"type": "ping"}}))
            print("📤 已发送ping")

            # 等待pong
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(response)
                if data.get("type") == "pong":
                    print("📥 收到pong响应")
                    print("✅ WebSocket通信正常")
                    return True
            except asyncio.TimeoutError:
                print("⚠️  未收到pong响应")
                return False

    except Exception as e:
        print(f"❌ WebSocket连接失败: {{e}}")
        return False

def test_ports():
    """测试端口连通性"""
    print("\\n🔍 测试端口连通性:")

    ports = [
        (PUBLIC_IP, HTTP_PORT, "HTTP服务"),
        (PUBLIC_IP, WS_PORT, "WebSocket"),
    ]

    results = []
    for host, port, name in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                print(f"✅ {{name}} ({{port}}): 开放")
                results.append(True)
            else:
                print(f"❌ {{name}} ({{port}}): 关闭")
                results.append(False)
        except Exception as e:
            print(f"❌ {{name}} ({{port}}): 错误 - {{e}}")
            results.append(False)

    return all(results)

async def main():
    print("="*60)
    print("  智桥公网访问测试")
    print("="*60)
    print(f"公网IP: {{PUBLIC_IP}}")
    print(f"测试时间: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    print()

    # 测试端口
    ports_ok = test_ports()

    # 测试WebSocket
    ws_ok = await test_websocket()

    # 汇总
    print("\\n" + "="*60)
    print("  测试结果")
    print("="*60)
    print(f"端口测试: {{'✅ 通过' if ports_ok else '❌ 失败'}}")
    print(f"WebSocket测试: {{'✅ 通过' if ws_ok else '❌ 失败'}}")

    if ports_ok and ws_ok:
        print("\\n✅ 所有测试通过！公网访问正常")
        print(f"\\n访问地址: http://{PUBLIC_IP}:{HTTP_PORT}/web/ui/index.html")
        return True
    else:
        print("\\n❌ 部分测试失败，请检查服务状态")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\\n\\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\\n\\n测试发生错误: {{e}}")
        sys.exit(1)
'''

test_script.parent.mkdir(parents=True, exist_ok=True)
with open(test_script, 'w', encoding='utf-8') as f:
    f.write(test_content)
test_script.chmod(0o755)
print(f"✅ 测试脚本已创建: {test_script}")

print("\n" + "="*60)
print("  ✅ 公网访问配置完成！")
print("="*60)
print("\n🌐 公网访问地址:")
print(f"   http://{PUBLIC_IP}:{HTTP_PORT}/web/ui/index.html")
print("\n📱 移动端访问:")
print(f"   任何网络 → 浏览器 → {PUBLIC_IP}:{HTTP_PORT}")
print("\n🧪 测试命令:")
print("   python3 scripts/test_public_ip.py")
print("\n📋 使用说明:")
print("   cat PUBLIC_ACCESS.txt")
print("\n" + "="*60)
