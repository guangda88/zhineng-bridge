#!/usr/bin/env python3
"""
智桥仪表盘HTTP服务器

提供可视化监控仪表盘的Web界面
"""

import http.server
import socketserver
import os
import json
from pathlib import Path

# 颜色输出
class Colors:
    OKGREEN = '\033[92m'
    OKCYAN = '\033[96m'
    ENDC = '\033[0m'

class DashboardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义请求处理器"""

    def do_GET(self):
        # 处理仪表盘数据请求
        if self.path == '/api/dashboard':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            try:
                with open('/tmp/zhineng-bridge-dashboard.json', 'r', encoding='utf-8') as f:
                    data = f.read()
                self.wfile.write(data.encode('utf-8'))
            except FileNotFoundError:
                error_data = json.dumps({"error": "Dashboard data not found. Please run monitor_ai_processes.py first."})
                self.wfile.write(error_data.encode('utf-8'))
            return

        # 处理静态文件请求
        if self.path == '/dashboard.html' or self.path == '/':
            self.path = '/dashboard.html'

        return super().do_GET()

def start_server(port=8888):
    """启动HTTP服务器"""
    # 切换到web目录
    os.chdir('/home/ai/zhineng-bridge/web')

    handler = DashboardHTTPRequestHandler

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"{Colors.OKCYAN}🚀 智桥仪表盘服务器启动...{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✅ 访问地址: http://localhost:{port}/dashboard.html{Colors.ENDC}")
        print(f"{Colors.OKCYAN}ℹ️  按 Ctrl+C 停止服务器{Colors.ENDC}\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n{Colors.OKCYAN}⏹️  服务器已停止{Colors.ENDC}")

if __name__ == "__main__":
    start_server()
