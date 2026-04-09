#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zhineng-bridge 实时日志查看器
"""

import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List


class LogViewer:
    """日志查看器"""

    def __init__(self):
        self.log_files = {
            "session_manager": "/tmp/session_manager.log",
            "websocket": "/tmp/websocket_server.log",
            "health_check": "/tmp/health_check.log",
        }
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = True

    def setup_logging(self):
        """设置日志记录"""
        # 重定向WebSocket服务器输出
        ws_pid = subprocess.run(
            ["pgrep", "-f", "python.*start_server.py"], capture_output=True, text=True
        ).stdout.strip()

        if ws_pid:
            print(f"📡 找到WebSocket服务器进程 (PID: {ws_pid})")
            # 注意：已运行的进程无法直接重定向输出
            # 需要在启动时就重定向
        else:
            print("⚠️  未找到WebSocket服务器进程")

        # 检查Session Manager日志
        if os.path.exists(self.log_files["session_manager"]):
            print(f"✅ Session Manager日志: {self.log_files['session_manager']}")
        else:
            print("⚠️  Session Manager日志文件不存在")

    def get_log_tail(self, log_file: str, lines: int = 20) -> List[str]:
        """获取日志文件末尾"""
        if not os.path.exists(log_file):
            return []

        try:
            result = subprocess.run(
                ["tail", "-n", str(lines), log_file], capture_output=True, text=True
            )
            return result.stdout.split("\n")
        except Exception as e:
            return [f"Error reading log: {e}"]

    def follow_log(self, log_file: str, prefix: str = ""):
        """实时跟踪日志文件"""
        if not os.path.exists(log_file):
            return

        try:
            # 使用tail -f来实时跟踪
            process = subprocess.Popen(
                ["tail", "-f", log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.processes[log_file] = process

            for line in iter(process.stdout.readline, ""):
                if not self.running:
                    break
                if line.strip():
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] {prefix} {line.rstrip()}")

        except Exception as e:
            print(f"Error following {log_file}: {e}")

    def print_initial_logs(self):
        """打印初始日志"""
        print("\n" + "=" * 100)
        print("📝 初始日志内容")
        print("=" * 100)
        print()

        for name, log_file in self.log_files.items():
            if os.path.exists(log_file):
                print(f"\n📄 {name.upper()} 日志:")
                print("-" * 100)
                lines = self.get_log_tail(log_file, 10)
                for line in lines:
                    if line.strip():
                        print(f"  {line}")
            else:
                print(f"\n⚠️  {name.upper()} 日志文件不存在")

        print()
        print("=" * 100)

    def start_monitoring(self):
        """开始实时监控"""
        self.setup_logging()
        self.print_initial_logs()

        print("\n" + "=" * 100)
        print("👀 开始实时日志监控 (按 Ctrl+C 停止)")
        print("=" * 100)
        print()

        # 监控多个日志文件
        import threading

        threads = []

        for name, log_file in self.log_files.items():
            if os.path.exists(log_file):
                thread = threading.Thread(
                    target=self.follow_log, args=(log_file, f"[{name.upper()}]"), daemon=True
                )
                thread.start()
                threads.append(thread)

        try:
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n👋 日志监控已停止")
            self.running = False

        # 清理进程
        for process in self.processes.values():
            try:
                process.terminate()
            except:
                pass


def main():
    """主函数"""
    print("🚀 启动日志查看器...")
    viewer = LogViewer()
    viewer.start_monitoring()


if __name__ == "__main__":
    main()
