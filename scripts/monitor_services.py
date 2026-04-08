#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zhineng-bridge 服务日志监视器
实时监视服务状态和日志
"""

import time
import subprocess
import requests
from datetime import datetime
from typing import Dict, List


class ServiceMonitor:
    """服务监视器"""

    def __init__(self):
        self.network_addresses = ['100.66.1.8', '10.113.22.99', '192.168.2.1']
        self.primary_host = self.network_addresses[0]

        self.services = {
            'websocket': {
                'name': 'WebSocket Server',
                'port': 8765,
                'health_url': f'ws://{self.primary_host}:8765',
                'process_keywords': ['start_server']
            },
            'health_check': {
                'name': 'Health Check Server',
                'port': 8000,
                'health_url': f'http://{self.primary_host}:8000/health',
                'status_url': f'http://{self.primary_host}:8000/status',
                'process_keywords': ['health_check', 'http_server']
            },
            'session_manager': {
                'name': 'Session Manager',
                'port': None,
                'health_url': None,
                'process_keywords': ['start_manager', 'session_manager']
            }
        }

    def get_process_info(self, keywords: List[str]) -> List[Dict]:
        """获取进程信息"""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )

            processes = []
            for line in result.stdout.split('\n'):
                if any(keyword in line for keyword in keywords):
                    parts = line.split()
                    if len(parts) >= 11:
                        processes.append({
                            'pid': parts[1],
                            'user': parts[0],
                            'cpu': parts[2],
                            'mem': parts[3],
                            'cmd': ' '.join(parts[10:15])
                        })
            return processes
        except Exception:
            return []

    def check_port(self, port: int) -> bool:
        """检查端口是否在监听"""
        try:
            result = subprocess.run(
                ['lsof', '-i', f':{port}'],
                capture_output=True,
                text=True
            )
            return 'LISTEN' in result.stdout
        except Exception:
            return False

    def check_http_health(self, url: str) -> bool:
        """检查HTTP健康状态"""
        try:
            response = requests.get(url, timeout=1)
            return response.status_code == 200
        except Exception:
            return False

    def get_service_status(self, service_key: str) -> Dict:
        """获取服务状态"""
        service = self.services[service_key]

        # 检查进程
        processes = self.get_process_info(service['process_keywords'])
        running = len(processes) > 0

        status = {
            'name': service['name'],
            'running': running,
            'processes': processes,
            'port_listening': False,
            'health_ok': False,
            'pid': None,
            'cpu': '0.0%',
            'mem': '0.0%'
        }

        if processes:
            status['pid'] = processes[0]['pid']
            status['cpu'] = processes[0]['cpu']
            status['mem'] = processes[0]['mem']

        # 检查端口
        if service['port']:
            status['port_listening'] = self.check_port(service['port'])

        # 检查健康
        if service['health_url'] and service['health_url'].startswith('http'):
            status['health_ok'] = self.check_http_health(service['health_url'])

        return status

    def get_all_status(self) -> Dict:
        """获取所有服务状态"""
        return {
            key: self.get_service_status(key)
            for key in self.services.keys()
        }

    def print_status(self):
        """打印服务状态"""
        print("\033c", end="")  # 清屏
        print("=" * 100)
        print(f"🔍 zhineng-bridge 服务监视 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        print()

        all_status = self.get_all_status()

        # 服务状态摘要
        running_count = sum(1 for s in all_status.values() if s['running'])
        total_count = len(all_status)

        print(f"📊 服务概览: {running_count}/{total_count} 运行中")
        print("-" * 100)

        # 详细状态
        for key, status in all_status.items():
            status_icon = "✅" if status['running'] else "❌"
            print(f"\n{status_icon} {status['name']}")
            print("  " + "-" * 96)

            if status['running']:
                print("  状态: 🟢 运行中")
                print(f"  PID:  {status['pid']}")
                print(f"  CPU:  {status['cpu']}")
                print(f"  MEM:  {status['mem']}")

                if status['port_listening']:
                    print(f"  端口: 🟢 监听中 (port {self.services[key]['port']})")
                elif self.services[key]['port']:
                    print(f"  端口: 🔴 未监听 (port {self.services[key]['port']})")

                if status['health_ok']:
                    print("  健康: 🟢 正常")
                elif self.services[key]['health_url']:
                    print("  健康: 🔴 异常")
            else:
                print("  状态: 🔴 未运行")

        print()
        print("-" * 100)

        # 快速测试
        print("\n🧪 快速测试:")
        print("-" * 100)

        # Health Check 测试
        try:
            health_response = requests.get('http://localhost:8000/health', timeout=2)
            if health_response.status_code == 200:
                print("  ✅ Health Check: 正常")
                health_data = health_response.json()
                print(f"    状态: {health_data.get('status', 'unknown')}")
                print(f"    服务: {health_data.get('services', {})}")
            else:
                print(f"  ❌ Health Check: HTTP {health_response.status_code}")
        except Exception as e:
            print(f"  ❌ Health Check: {str(e)[:50]}")

        # Status 测试
        try:
            status_response = requests.get('http://localhost:8000/status', timeout=2)
            if status_response.status_code == 200:
                print("  ✅ Status API: 正常")
            else:
                print(f"  ❌ Status API: HTTP {status_response.status_code}")
        except Exception as e:
            print(f"  ❌ Status API: {str(e)[:50]}")

        print()
        print("-" * 100)
        print("💡 按 Ctrl+C 停止监视 | 刷新间隔: 2秒")
        print("=" * 100)

    def run(self):
        """运行监视器"""
        try:
            print("🔍 启动服务监视器...")
            time.sleep(1)

            while True:
                self.print_status()
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n\n👋 监视器已停止")


def main():
    """主函数"""
    monitor = ServiceMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
