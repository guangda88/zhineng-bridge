#!/usr/bin/env python3
"""
智桥网络访问诊断工具

用于诊断为什么某些网络接口无法访问服务
"""

import socket
import subprocess
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'relay-server'))

def test_port_access(host, port, timeout=2):
    """测试端口访问"""
    try:
        s = socket.socket()
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except Exception as e:
        print(f"  错误: {e}")
        return False

def get_network_interfaces():
    """获取所有网络接口"""
    try:
        import netifaces
        interfaces = {}
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    interfaces[iface] = addr['addr']
        return interfaces
    except ImportError:
        print("警告: netifaces 未安装，使用备用方法")
        return {}

def check_firewall():
    """检查防火墙状态"""
    print("\n" + "="*60)
    print("防火墙状态检查")
    print("="*60)

    # 检查 UFW
    try:
        result = subprocess.run(['sudo', 'ufw', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("UFW 防火墙状态:")
            print(result.stdout)
    except Exception as e:
        print(f"无法检查 UFW: {e}")

    # 检查 iptables
    try:
        result = subprocess.run(['sudo', 'iptables', '-L', '-n'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # 显示包含目标端口的规则
            print("\niptables 规则 (包含 8080 或 8765):")
            for line in result.stdout.split('\n'):
                if '8080' in line or '8765' in line or 'Chain' in line:
                    print(line)
    except Exception as e:
        print(f"无法检查 iptables: {e}")

def diagnose_network_interfaces():
    """诊断网络接口"""
    print("\n网络接口:")
    interfaces = get_network_interfaces()
    if interfaces:
        for name, ip in interfaces.items():
            print(f"  {name}: {ip}")
    else:
        print("  无法获取网络接口信息")
        print("\n尝试获取主机 IP:")
        hostname = socket.gethostname()
        print(f"  主机名: {hostname}")
        try:
            hostname_ip = socket.gethostbyname(hostname)
            print(f"  主机IP: {hostname_ip}")
        except:
            pass


def diagnose_port_access():
    """诊断端口访问"""
    print("\n" + "="*60)
    print("端口访问测试")
    print("="*60)

    test_hosts = ['127.0.0.1', '0.0.0.0', '192.168.2.1', '192.168.31.99', '10.113.22.99', '100.66.1.8']
    ports = [8080, 8765]

    for host in test_hosts:
        print(f"\n主机: {host}")
        for port in ports:
            accessible = test_port_access(host, port)
            status = "✅ 可访问" if accessible else "❌ 不可访问"
            print(f"  端口 {port}: {status}")


def diagnose_server_status():
    """诊断服务器状态"""
    print("\n" + "="*60)
    print("服务器监听状态")
    print("="*60)

    try:
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n监听的端口:")
            for line in result.stdout.split('\n'):
                if 'LISTEN' in line:
                    print(f"  {line}")
    except Exception as e:
        print(f"无法检查监听端口: {e}")


def generate_diagnostic_suggestions():
    """生成诊断建议"""
    suggestions = []

    if test_port_access('127.0.0.1', 8080) and not test_port_access('10.113.22.99', 8080):
        suggestions.append("1. 服务器在本地运行正常，但从 10.113.22.99 无法访问")
        suggestions.append("2. 可能原因：防火墙阻止了该接口的访问")

    if test_port_access('127.0.0.1', 8080) and not test_port_access('100.66.1.8', 8080):
        suggestions.append("3. 服务器在本地运行正常，但从 100.66.1.8 无法访问")
        suggestions.append("4. 可能原因：防火墙阻止了该接口的访问")

    listen_all = False
    try:
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
        if '0.0.0.0:8080' in result.stdout:
            listen_all = True
            suggestions.append("5. ✅ 服务器监听在 0.0.0.0:8080，应该可以从所有接口访问")
    except:
        pass

    if listen_all:
        suggestions.append("6. 如果仍然无法访问，可能是以下原因：")
        suggestions.append("   - 防火墙规则阻止了外部访问")
        suggestions.append("   - 网络接口配置问题")
        suggestions.append("   - 路由器/网关配置问题")

    return suggestions


def print_solutions():
    """打印解决方案"""
    print("\n建议的解决方案:")
    print("\n选项 1: 开放防火墙端口 (推荐)")
    print("  sudo ufw allow 8080/tcp")
    print("  sudo ufw allow 8765/tcp")
    print("  sudo ufw reload")

    print("\n选项 2: 使用 iptables 开放端口")
    print("  sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT")
    print("  sudo iptables -A INPUT -p tcp --dport 8765 -j ACCEPT")
    print("  sudo iptables-save | sudo tee /etc/iptables/rules.v4")

    print("\n选项 3: 临时关闭防火墙 (不推荐，仅用于测试)")
    print("  sudo ufw disable")


def diagnose():
    """执行诊断"""
    print("\n" + "="*60)
    print("智桥网络访问诊断工具")
    print("="*60)

    diagnose_network_interfaces()
    diagnose_port_access()
    check_firewall()
    diagnose_server_status()

    print("\n" + "="*60)
    print("诊断建议")
    print("="*60)

    suggestions = generate_diagnostic_suggestions()
    for suggestion in suggestions:
        print(suggestion)

    print_solutions()
    print("\n" + "="*60)

if __name__ == "__main__":
    diagnose()
