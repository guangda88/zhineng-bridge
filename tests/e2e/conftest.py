#!/usr/bin/env python3
"""
E2E 测试配置文件

提供自动启动和停止服务器的 fixtures
"""

import pytest
import subprocess
import os
import signal
import time
import socket
from typing import Optional


class ServerManager:
    """服务器管理器"""

    def __init__(self):
        self.relay_server_process: Optional[subprocess.Popen] = None
        self.session_manager_process: Optional[subprocess.Popen] = None
        self.pid_file_relay = "/tmp/relay-server-test.pid"
        self.pid_file_session = "/tmp/session-manager-test.pid"

    def is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def kill_process_on_port(self, port: int) -> bool:
        """停止占用端口的进程"""
        try:
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip()
                os.kill(int(pid), signal.SIGKILL)
                time.sleep(0.5)
                return True
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ProcessLookupError, ValueError):
            pass
        return False

    def start_relay_server(self) -> subprocess.Popen:
        """启动 relay-server"""
        # 检查端口是否被占用
        if self.is_port_in_use(8765):
            print("⚠️  端口 8765 已被占用，尝试停止占用进程...")
            self.kill_process_on_port(8765)
            time.sleep(0.5)

        # 启动服务器
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'relay-server',
            'start_server.py'
        )

        # Disable rate limiting for E2E tests
        env = os.environ.copy()
        env['ZHINENG_BRIDGE_SECURITY_ENABLE_RATE_LIMIT'] = 'False'

        process = subprocess.Popen(
            ['python3', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
            env=env
        )

        # 保存 PID
        with open(self.pid_file_relay, 'w') as f:
            f.write(str(process.pid))

        # 等待服务器启动
        max_wait = 10  # 最多等待 10 秒
        for i in range(max_wait):
            if self.is_port_in_use(8765):
                print(f"✅ relay-server 已启动 (PID: {process.pid})")
                return process
            time.sleep(1)
            if process.poll() is not None:
                # 进程已经退出
                stdout, stderr = process.communicate()
                raise RuntimeError(
                    f"relay-server 启动失败\n"
                    f"stdout: {stdout.decode()}\n"
                    f"stderr: {stderr.decode()}"
                )

        raise RuntimeError("relay-server 启动超时")

    def start_session_manager(self) -> subprocess.Popen:
        """启动 session-manager"""
        # 检查端口是否被占用
        if self.is_port_in_use(8764):
            print("⚠️  端口 8764 已被占用，尝试停止占用进程...")
            self.kill_process_on_port(8764)
            time.sleep(0.5)

        # 启动服务器
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'phase1',
            'session_manager',
            'start_manager.py'
        )

        process = subprocess.Popen(
            ['python3', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )

        # 保存 PID
        with open(self.pid_file_session, 'w') as f:
            f.write(str(process.pid))

        print(f"✅ session-manager 已启动 (PID: {process.pid})")
        return process

    def stop_relay_server(self):
        """停止 relay-server"""
        if self.relay_server_process:
            try:
                # 发送 SIGTERM 到进程组
                os.killpg(os.getpgid(self.relay_server_process.pid), signal.SIGTERM)

                # 等待进程退出
                try:
                    self.relay_server_process.wait(timeout=5)
                    print("✅ relay-server 已停止")
                except subprocess.TimeoutExpired:
                    # 强制终止
                    os.killpg(os.getpgid(self.relay_server_process.pid), signal.SIGKILL)
                    self.relay_server_process.wait()
                    print("✅ relay-server 已强制停止")
            except (ProcessLookupError, OSError):
                pass
            finally:
                self.relay_server_process = None
                if os.path.exists(self.pid_file_relay):
                    os.remove(self.pid_file_relay)

    def stop_session_manager(self):
        """停止 session-manager"""
        if self.session_manager_process:
            try:
                # 发送 SIGTERM 到进程组
                os.killpg(os.getpgid(self.session_manager_process.pid), signal.SIGTERM)

                # 等待进程退出
                try:
                    self.session_manager_process.wait(timeout=5)
                    print("✅ session-manager 已停止")
                except subprocess.TimeoutExpired:
                    # 强制终止
                    os.killpg(os.getpgid(self.session_manager_process.pid), signal.SIGKILL)
                    self.session_manager_process.wait()
                    print("✅ session-manager 已强制停止")
            except (ProcessLookupError, OSError):
                pass
            finally:
                self.session_manager_process = None
                if os.path.exists(self.pid_file_session):
                    os.remove(self.pid_file_session)

    def cleanup(self):
        """清理所有服务器"""
        self.stop_session_manager()
        self.stop_relay_server()


@pytest.fixture(scope="function")
def server_manager():
    """创建服务器管理器 (function scope，每个测试重启服务器)"""
    manager = ServerManager()

    # 启动服务器
    print("\n🚀 启动测试服务器...")
    manager.session_manager_process = manager.start_session_manager()
    time.sleep(1)  # 等待 session-manager 完全启动

    manager.relay_server_process = manager.start_relay_server()
    time.sleep(1)  # 等待 relay-server 完全启动

    yield manager

    # 清理
    print("\n🧹 清理测试服务器...")
    manager.cleanup()


@pytest.fixture(scope="function")
def relay_server_process(server_manager):
    """获取 relay-server 进程 (function scope)"""
    return server_manager.relay_server_process


@pytest.fixture(scope="function")
def session_manager_process(server_manager):
    """获取 session-manager 进程 (function scope)"""
    return server_manager.session_manager_process
