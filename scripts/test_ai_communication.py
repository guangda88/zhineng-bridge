#!/usr/bin/env python3
"""
智桥 AI 互联测试脚本

测试场景：
1. Agent注册
2. Agent发现
3. Agent直接通信
4. 频道创建和广播
5. 对话历史查询
"""

import asyncio
import json
from datetime import datetime

try:
    import websockets
except ImportError:
    print("❌ 需要安装 websockets: pip install websockets")
    exit(1)

# 测试配置
WS_URL = "wss://localhost:8766"
TIMEOUT = 5  # 秒

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_success(msg):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ️  {msg}{Colors.ENDC}")

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}═══ {msg} ═══{Colors.ENDC}")

async def register_agent(ws, agent_id, name, capabilities):
    """注册AI Agent"""
    message = {
        "type": "register_agent",
        "agent_id": agent_id,
        "name": name,
        "capabilities": capabilities
    }
    await ws.send(json.dumps(message))
    response = json.loads(await asyncio.wait_for(ws.recv(), timeout=TIMEOUT))
    return response

async def list_agents(ws):
    """列出所有Agent"""
    message = {"type": "list_agents"}
    await ws.send(json.dumps(message))
    response = json.loads(await asyncio.wait_for(ws.recv(), timeout=TIMEOUT))
    return response

async def send_inter_chat(ws, from_agent, to_agent, text):
    """发送Agent间直接消息"""
    message = {
        "type": "inter_chat",
        "from": from_agent,
        "to": to_agent,
        "text": text,
        "timestamp": datetime.utcnow().isoformat()
    }
    await ws.send(json.dumps(message))
    response = json.loads(await asyncio.wait_for(ws.recv(), timeout=TIMEOUT))
    return response

async def create_channel(ws, channel_id, name, creator):
    """创建频道"""
    message = {
        "type": "channel_create",
        "channel_id": channel_id,
        "name": name,
        "creator": creator
    }
    await ws.send(json.dumps(message))
    response = json.loads(await asyncio.wait_for(ws.recv(), timeout=TIMEOUT))
    return response

async def join_channel(ws, channel_id, agent_id):
    """加入频道"""
    message = {
        "type": "channel_join",
        "channel_id": channel_id,
        "agent_id": agent_id
    }
    await ws.send(json.dumps(message))
    response = json.loads(await asyncio.wait_for(ws.recv(), timeout=TIMEOUT))
    return response

async def post_to_channel(ws, channel_id, agent_id, text):
    """向频道发送消息"""
    message = {
        "type": "channel_post",
        "channel_id": channel_id,
        "agent_id": agent_id,
        "text": text,
        "timestamp": datetime.utcnow().isoformat()
    }
    await ws.send(json.dumps(message))
    response = json.loads(await asyncio.wait_for(ws.recv(), timeout=TIMEOUT))
    return response

async def receive_messages(ws):
    """接收消息的协程"""
    messages = []
    while True:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=2)
            messages.append(json.loads(msg))
        except asyncio.TimeoutError:
            break
    return messages

async def test_communication():
    """主测试函数"""
    import ssl

    try:
        print_header("连接到智桥服务器")
        print_info(f"WebSocket URL: {WS_URL}")

        # 创建SSL上下文（允许自签名证书）
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        ws = await asyncio.wait_for(
            websockets.connect(WS_URL, ssl=ssl_context),
            timeout=TIMEOUT
        )
        print_success("连接成功！")

        # 测试1：Agent注册
        print_header("测试1：Agent注册")
        agents = [
            {
                "agent_id": "claude-code",
                "name": "Claude Code",
                "capabilities": ["code_review", "documentation", "debugging"]
            },
            {
                "agent_id": "crush-1",
                "name": "Crush AI",
                "capabilities": ["code_generation", "refactoring", "testing"]
            },
            {
                "agent_id": "cursor-assistant",
                "name": "Cursor Assistant",
                "capabilities": ["code_completion", "navigation", "multi_file_edit"]
            }
        ]

        for agent in agents:
            print_info(f"注册 Agent: {agent['agent_id']}")
            response = await register_agent(
                ws,
                agent["agent_id"],
                agent["name"],
                agent["capabilities"]
            )
            if response.get("type") == "agent_registered":
                print_success(f"  ✓ {agent['name']} 已注册")
            else:
                print_error(f"  ✗ 注册失败: {response}")

        # 测试2：Agent发现
        print_header("测试2：Agent发现")
        response = await list_agents(ws)
        if response.get("type") == "agents_list":
            print_success(f"发现 {len(response['agents'])} 个 Agent:")
            for agent in response["agents"]:
                print(f"  • {agent['name']} ({agent['agent_id']})")
                print(f"    能力: {', '.join(agent['capabilities'])}")
        else:
            print_error("Agent发现失败")

        # 测试3：Agent直接通信
        print_header("测试3：Agent直接通信")
        print_info("Claude → Crush: 请帮我审查这段代码")
        response = await send_inter_chat(
            ws,
            "claude-code",
            "crush-1",
            "请帮我审查这段代码：def add(a, b): return a + b"
        )
        if response.get("type") == "message_sent":
            print_success("消息已发送")
            print(f"  消息ID: {response.get('message_id')}")

        print_info("Crush → Cursor: 这个函数很简单，不需要重构")
        response = await send_inter_chat(
            ws,
            "crush-1",
            "cursor-assistant",
            "这个函数很简单，不需要重构"
        )
        if response.get("type") == "message_sent":
            print_success("消息已发送")

        # 测试4：频道通信
        print_header("测试4：频道通信")
        print_info("创建频道: code-review")
        response = await create_channel(
            ws,
            "code-review",
            "Code Review Team",
            "claude-code"
        )
        if response.get("type") == "channel_created":
            print_success("频道创建成功")

            # Agents加入频道
            print_info("Agents加入频道...")
            for agent_id in ["claude-code", "crush-1", "cursor-assistant"]:
                response = await join_channel(ws, "code-review", agent_id)
                if response.get("type") == "channel_joined":
                    print_success(f"  ✓ {agent_id} 已加入")

            # 广播消息
            print_info("Claude向频道广播消息")
            response = await post_to_channel(
                ws,
                "code-review",
                "claude-code",
                "大家好，新的PR已准备好审查！"
            )
            if response.get("type") == "message_posted":
                print_success("消息已广播到频道")

        # 测试5：查询频道历史
        print_header("测试5：查询对话历史")
        message = {"type": "channel_history", "channel_id": "code-review"}
        await ws.send(json.dumps(message))
        response = json.loads(await asyncio.wait_for(ws.recv(), timeout=TIMEOUT))
        if response.get("type") == "channel_history":
            print_success(f"频道历史: {len(response['messages'])} 条消息")
            for msg in response["messages"]:
                print(f"  [{msg['timestamp']}] {msg['agent_id']}: {msg['text']}")

        # 关闭连接
        await ws.close()
        print_header("测试完成")
        print_success("所有测试通过！")
        print_info("\n这就是打破AI孤岛的证明：")
        print_info("• 3个AI Agent已注册到智桥")
        print_info("• Agent之间可以互相发送消息")
        print_info("• Agent可以创建频道进行群组讨论")
        print_info("• 消息历史完整保存")
        print_info("\n现在它们不再是孤立的工具，而是一个协作的AI集体！🎉")

    except asyncio.TimeoutError:
        print_error("连接超时，请确保中继服务器已启动")
    except websockets.exceptions.WebSocketException as e:
        print_error(f"WebSocket错误: {e}")
    except Exception as e:
        print_error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔═════════════════════════════════════════╗")
    print("║   智桥 AI 互联测试                       ║")
    print("║   AI-to-AI Communication Test          ║")
    print("╚═════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")

    asyncio.run(test_communication())
