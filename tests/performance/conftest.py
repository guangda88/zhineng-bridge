#!/usr/bin/env python3
"""
性能测试配置文件

提供自动启动和停止服务器的 fixtures
"""

import os
import signal
import socket
import subprocess
import time
from typing import Optional

import pytest


class PerformanceTestServer:
    """性能测试服务器管理器"""

    def __init__(self):
        self.relay_server_process: Optional[subprocess.Popen] = None
        self.session_manager_process: Optional[subprocess.Popen] = None
        self.relay_server_started = False

    def is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    def kill_process_on_port(self, port: int) -> bool:
        """停止占用端口的进程"""
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip()
                os.kill(int(pid), signal.SIGKILL)
                time.sleep(0.5)
                return True
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            ProcessLookupError,
            ValueError,
        ):
            pass
        return False

    def start_relay_server(self):
        """启动 relay-server"""
        if self.is_port_in_use(8765):
            print("⚠️  端口 8765 已被占用，尝试停止占用进程...")
            self.kill_process_on_port(8765)
            time.sleep(0.5)

        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "relay-server",
            "start_server.py",
        )

        # Disable rate limiting for performance tests
        env = os.environ.copy()
        env["ZHINENG_BRIDGE_SECURITY_ENABLE_RATE_LIMIT"] = "False"

        process = subprocess.Popen(
            ["python3", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
            env=env,
        )

        # 等待服务器启动
        max_wait = 15
        for i in range(max_wait):
            if self.is_port_in_use(8765):
                print(f"✅ relay-server 已启动 (PID: {process.pid})")
                self.relay_server_process = process
                self.relay_server_started = True
                return process
            time.sleep(1)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise RuntimeError(
                    f"relay-server 启动失败\n"
                    f"stdout: {stdout.decode()}\n"
                    f"stderr: {stderr.decode()}"
                )

        raise RuntimeError("relay-server 启动超时")

    def stop_relay_server(self):
        """停止 relay-server"""
        if self.relay_server_process:
            try:
                os.killpg(os.getpgid(self.relay_server_process.pid), signal.SIGTERM)
                try:
                    self.relay_server_process.wait(timeout=5)
                    print("✅ relay-server 已停止")
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(self.relay_server_process.pid), signal.SIGKILL)
                    self.relay_server_process.wait()
                    print("✅ relay-server 已强制停止")
            except (ProcessLookupError, OSError):
                pass
            finally:
                self.relay_server_process = None
                self.relay_server_started = False


@pytest.fixture(scope="session")
def performance_server():
    """创建性能测试服务器 (session scope)"""
    server = PerformanceTestServer()

    print("\n🚀 启动性能测试服务器...")
    server.start_relay_server()
    time.sleep(2)  # 等待服务器完全启动

    yield server

    # 清理
    print("\n🧹 清理性能测试服务器...")
    server.stop_relay_server()
