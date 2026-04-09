#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zhineng-bridge 综合监控仪表板
实时显示服务状态和日志
"""

import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests


class ServiceDashboard:
    """服务监控仪表板"""

    def __init__(self):
        self.network_addresses = ["100.66.1.8", "10.113.22.99", "192.168.2.1"]
        self.primary_host = self.network_addresses[0]

        self.services = {
            "websocket": {
                "name": "WebSocket Server",
                "port": 8765,
                "process_keywords": ["start_server"],
                "status_url": f"http://{self.primary_host}:8000/status",
            },
            "health_check": {
                "name": "Health Check Server",
                "port": 8000,
                "process_keywords": ["health_check", "uvicorn.*8000"],
                "health_url": f"http://{self.primary_host}:8000/health",
            },
            "session_manager": {
                "name": "Session Manager",
                "port": None,
                "process_keywords": ["start_manager", "session_manager"],
            },
        }

        self.log_files = {"session_manager": "/tmp/session_manager.log"}

        self.running = True
        self.last_logs = {name: [] for name in self.log_files.keys()}

    def clear_screen(self):
        """清屏"""
        os.system("clear" if os.name == "posix" else "cls")

    def get_process_status(self, keywords: List[str]) -> Dict:
        """获取进程状态"""
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

            for line in result.stdout.split("\n"):
                if any(keyword in line for keyword in keywords):
                    parts = line.split()
                    if len(parts) >= 11:
                        return {
                            "running": True,
                            "pid": parts[1],
                            "cpu": parts[2],
                            "mem": parts[3],
                            "cmd": " ".join(parts[10:13]),
                        }
        except Exception:
            pass

        return {"running": False, "pid": None, "cpu": "0.0", "mem": "0.0"}

    def check_port(self, port: Optional[int]) -> bool:
        """检查端口"""
        if not port:
            return False
        try:
            result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
            return "LISTEN" in result.stdout
        except Exception:
            return False

    def check_http_status(self, url: str) -> Dict:
        """检查HTTP状态"""
        if not url:
            return {"ok": False, "status_code": None}

        try:
            response = requests.get(url, timeout=2)
            return {
                "ok": response.status_code == 200,
                "status_code": response.status_code,
                "data": (
                    response.json()
                    if response.headers.get("content-type", "").startswith("application/json")
                    else None
                ),
            }
        except Exception as e:
            return {"ok": False, "status_code": None, "error": str(e)[:50]}

    def get_service_info(self, service_key: str) -> Dict:
        """获取服务信息"""
        service = self.services[service_key]

        # 进程状态
        process = self.get_process_status(service["process_keywords"])

        # 端口状态
        port_ok = self.check_port(service["port"])

        # HTTP状态
        http_status = self.check_http_status(service.get("health_url") or service.get("status_url"))

        return {
            "name": service["name"],
            "running": process["running"],
            "pid": process["pid"],
            "cpu": process["cpu"],
            "mem": process["mem"],
            "port_ok": port_ok,
            "port": service["port"],
            "http_ok": http_status["ok"],
            "http_status_code": http_status["status_code"],
        }

    def get_recent_logs(self, log_file: str, count: int = 3) -> List[str]:
        """获取最近日志"""
        if not os.path.exists(log_file):
            return []

        try:
            result = subprocess.run(
                ["tail", "-n", str(count), log_file], capture_output=True, text=True
            )
            return [line for line in result.stdout.split("\n") if line.strip()]
        except Exception:
            return []

    def draw_header(self):
        """绘制头部"""
        print("=" * 120)
        print(f"🔍 zhineng-bridge 监控仪表板 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 120)
        print()

    def draw_services(self):
        """绘制服务状态"""
        print("📊 服务状态")
        print("-" * 120)

        services_info = {key: self.get_service_info(key) for key in self.services.keys()}

        # 统计
        running_count = sum(1 for info in services_info.values() if info["running"])
        print(f"\n运行中: {running_count}/{len(services_info)}\n")

        # 详细信息
        for key, info in services_info.items():
            if info["running"]:
                icon = "🟢"
                status = "运行中"
            else:
                icon = "🔴"
                status = "未运行"

            print(f"{icon} {info['name']}")
            print(f"   状态: {status}")

            if info["running"]:
                print(f"   PID:  {info['pid']}")
                print(f"   CPU:  {info['cpu']}%")
                print(f"   MEM:  {info['mem']}%")

                if info["port"]:
                    port_icon = "🟢" if info["port_ok"] else "🔴"
                    print(
                        f"   端口: {port_icon} {info['port']} ({'监听' if info['port_ok'] else '未监听'})"
                    )

                if info["http_ok"]:
                    http_icon = "🟢"
                    print(f"   HTTP: {http_icon} 正常 (HTTP {info['http_status_code']})")
                elif info["http_status_code"]:
                    http_icon = "🟡"
                    print(f"   HTTP: {http_icon} HTTP {info['http_status_code']}")

            print()

    def draw_logs(self):
        """绘制日志"""
        print("\n📝 最近日志")
        print("-" * 120)

        for name, log_file in self.log_files.items():
            logs = self.get_recent_logs(log_file, 2)
            if logs:
                print(f"\n[{name.upper()}]")
                for log in logs:
                    print(f"  {log}")

    def draw_metrics(self):
        """绘制指标"""
        print("\n📈 快速指标")
        print("-" * 120)

        # 系统负载
        try:
            loadavg = os.getloadavg()
            print(
                f"  系统负载: {loadavg[0]:.2f} (1min) | {loadavg[1]:.2f} (5min) | {loadavg[2]:.2f} (15min)"
            )
        except:
            print("  系统负载: N/A")

        # 内存使用
        try:
            mem = (
                subprocess.run(["free", "-h"], capture_output=True, text=True)
                .stdout.split("\n")[1]
                .split()
            )
            print(f"  内存使用: {mem[2]} / {mem[1]} ({mem[3]})")
        except:
            print("  内存使用: N/A")

        # Python进程数
        try:
            result = subprocess.run(
                ["ps", "-C", "python3", "--no-headers"], capture_output=True, text=True
            )
            count = len([line for line in result.stdout.split("\n") if line.strip()])
            print(f"  Python进程: {count}")
        except:
            print("  Python进程: N/A")

        print()
        print("-" * 120)
        print("💡 按 Ctrl+C 退出 | 刷新间隔: 2秒")

    def draw_footer(self):
        """绘制底部"""
        print("=" * 120)

    def run(self):
        """运行仪表板"""
        try:
            print("🚀 启动监控仪表板...")
            time.sleep(1)

            while self.running:
                self.clear_screen()
                self.draw_header()
                self.draw_services()
                self.draw_logs()
                self.draw_metrics()
                self.draw_footer()
                time.sleep(2)

        except KeyboardInterrupt:
            print("\n\n👋 监控仪表板已停止")
            self.running = False


def main():
    """主函数"""
    dashboard = ServiceDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
