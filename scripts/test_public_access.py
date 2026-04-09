#!/usr/bin/env python3
"""
公网访问功能测试脚本

测试内容：
1. SSL证书验证
2. HTTPS本地访问测试
3. wss:// WebSocket连接测试
4. 前端协议自动检测测试
"""

import asyncio
import json
import ssl
import sys
from pathlib import Path

import websockets

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


# 颜色输出
def print_success(msg):
    print(f"✅ {msg}")


def print_error(msg):
    print(f"❌ {msg}")


def print_warning(msg):
    print(f"⚠️  {msg}")


def print_info(msg):
    print(f"ℹ️  {msg}")


def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


# 测试SSL证书
def test_ssl_certificate():
    print_header("测试1: SSL证书验证")

    cert_path = Path("/home/ai/zhineng-bridge/nginx/ssl/cert.pem")
    key_path = Path("/home/ai/zhineng-bridge/nginx/ssl/key.pem")

    if not cert_path.exists():
        print_error("SSL证书文件不存在")
        return False

    if not key_path.exists():
        print_error("SSL私钥文件不存在")
        return False

    try:
        # 验证证书文件
        import subprocess

        result = subprocess.run(
            ["openssl", "x509", "-in", str(cert_path), "-noout", "-text"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print_success("SSL证书格式正确")
            print_info(f"证书文件大小: {cert_path.stat().st_size} 字节")
            print_info(f"私钥文件大小: {key_path.stat().st_size} 字节")

            # 提取证书信息
            output = result.stdout
            if "Not Before" in output and "Not After" in output:
                import re

                not_after = re.search(r"Not After\s*:\s*(.+)", output)
                if not_after:
                    print_info(f"有效期至: {not_after.group(1).strip()}")

            return True
        else:
            print_error("SSL证书验证失败")
            print_error(result.stderr)
            return False

    except Exception as e:
        print_error(f"SSL证书验证失败: {e}")
        return False


# 测试HTTPS本地访问
async def test_https_access():
    print_header("测试2: HTTPS本地访问")

    hosts = ["10.113.22.99", "100.66.1.8", "192.168.2.1", "localhost"]
    port = 443

    for host in hosts:
        try:
            print_info(f"测试连接: https://{host}:{port}/health")

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port, ssl=context), timeout=5
            )

            request = f"GET /health HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            writer.write(request.encode())
            await writer.drain()

            response = await reader.read(1024)
            writer.close()
            await writer.wait_closed()

            if b"200 OK" in response or b"200" in response:
                print_success(f"HTTPS访问成功: {host}")
                return True
            else:
                print_warning(f"HTTPS响应异常: {host}")

        except asyncio.TimeoutError:
            print_warning(f"HTTPS连接超时: {host}")
        except ConnectionRefusedError:
            print_warning(f"HTTPS连接被拒绝: {host}")
        except Exception as e:
            print_warning(f"HTTPS连接失败 {host}: {e}")

    print_error("所有HTTPS连接测试失败")
    print_info("提示: 请确保nginx已启动并监听443端口")
    return False


# 测试WSS WebSocket连接
async def test_websocket_secure():
    print_header("测试3: WSS WebSocket连接测试")

    hosts = ["10.113.22.99", "100.66.1.8", "192.168.2.1", "localhost"]
    port = 443

    for host in hosts:
        try:
            print_info(f"测试WSS连接: wss://{host}:{port}")

            # 禁用SSL验证（因为使用自签名证书）
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            uri = f"wss://{host}:{port}"
            async with websockets.connect(uri, ssl=ssl_context, timeout=5) as ws:
                print_success(f"WSS连接成功: {host}")

                # 发送ping
                await ws.send(json.dumps({"type": "ping"}))
                print_info("已发送ping消息")

                # 等待pong
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(response)
                    if data.get("type") == "pong":
                        print_success("收到pong响应")
                        return True
                except asyncio.TimeoutError:
                    print_warning("未收到pong响应（超时）")

        except websockets.exceptions.InvalidStatusCode as e:
            print_warning(f"WSS连接失败 {host}: HTTP {e.status_code}")
        except asyncio.TimeoutError:
            print_warning(f"WSS连接超时: {host}")
        except ConnectionRefusedError:
            print_warning(f"WSS连接被拒绝: {host}")
        except Exception as e:
            print_warning(f"WSS连接失败 {host}: {e}")

    print_error("所有WSS连接测试失败")
    print_info("提示: 请确保nginx正确代理WebSocket到8765端口")
    return False


# 测试前端协议检测
def test_frontend_protocol_detection():
    print_header("测试4: 前端协议自动检测")

    client_js_path = Path("/home/ai/zhineng-bridge/web/ui/js/client.js")

    if not client_js_path.exists():
        print_error("client.js文件不存在")
        return False

    try:
        with open(client_js_path, "r") as f:
            content = f.read()

        # 检查关键代码
        checks = [
            ("window.location.protocol === 'https:'", "检测HTTPS协议"),
            ("const protocol = isSecure ? 'wss:' : 'ws:';", "设置WebSocket协议"),
            ("const port = isSecure ? 443 : wsPort;", "设置端口"),
        ]

        all_passed = True
        for pattern, description in checks:
            if pattern in content:
                print_success(f"{description} - 已实现")
            else:
                print_error(f"{description} - 未找到")
                all_passed = False

        return all_passed

    except Exception as e:
        print_error(f"读取client.js失败: {e}")
        return False


# 测试frp配置
def test_frp_configuration():
    print_header("测试5: FRP配置检查")

    frpc_config_path = Path("/home/ai/zhineng-bridge/config/frpc.ini")

    if not frpc_config_path.exists():
        print_warning("FRP配置文件不存在")
        print_info("配置位置: /home/ai/zhineng-bridge/config/frpc.ini")
        print_info("需要配置:")
        print_info("  1. server_addr: FRP服务器地址")
        print_info("  2. token: FRP认证令牌")
        return False

    try:
        with open(frpc_config_path, "r") as f:
            content = f.read()

        checks = [
            ("server_addr", "服务器地址"),
            ("token", "认证令牌"),
            ("zhineng_bridge_websocket", "WebSocket代理"),
        ]

        all_passed = True
        for pattern, description in checks:
            if pattern in content:
                print_success(f"{description} - 已配置")
            else:
                print_error(f"{description} - 未找到")
                all_passed = False

        if all_passed:
            print_info("FRP配置看起来完整，但需要验证:")
            print_info("  - server_addr是否为实际FRP服务器")
            print_info("  - token是否正确")
            print_info("  - 端口是否与FRP服务器配置匹配")

        return all_passed

    except Exception as e:
        print_error(f"读取FRP配置失败: {e}")
        return False


# 主测试函数
async def main():
    print_header("🌐 智桥公网访问功能测试")
    print_info("测试环境: 本地开发环境")
    test_time = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print_info(f"测试日期: {test_time}")

    results = {}

    # 测试1: SSL证书
    results["ssl_certificate"] = test_ssl_certificate()

    # 测试2: HTTPS访问
    results["https_access"] = await test_https_access()

    # 测试3: WSS连接
    results["websocket_secure"] = await test_websocket_secure()

    # 测试4: 前端协议检测
    results["frontend_protocol"] = test_frontend_protocol_detection()

    # 测试5: FRP配置
    results["frp_config"] = test_frp_configuration()

    # 汇总结果
    print_header("测试结果汇总")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print_info(f"总测试数: {total}")
    print_success(f"通过: {passed}")
    print_error(f"失败: {failed}")

    print("\n详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")

    # 给出建议
    print_header("下一步建议")

    if results["ssl_certificate"] and results["frontend_protocol"]:
        print_success("基础配置已完成")
        print_info("下一步:")
        print_info("  1. 启动nginx服务（监听443端口）")
        print_info("  2. 配置FRP客户端（config/frpc.ini）")
        print_info("  3. 启动FRP客户端")
        print_info("  4. 测试公网访问")
    else:
        print_warning("基础配置不完整")
        print_info("请检查失败的测试项")

    if results["frp_config"]:
        print_info("\nFRP配置已就绪，需要:")
        print_info("  1. 安装frp客户端")
        print_info("  2. 填写实际的server_addr和token")
        print_info("  3. 启动frpc")

    print("\n" + "=" * 60)
    print_info("测试完成！")
    print("=" * 60 + "\n")

    return all(results.values())


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
