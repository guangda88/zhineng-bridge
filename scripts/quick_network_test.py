#!/usr/bin/env python3
"""
智桥快速网络测试工具

快速测试网络访问并提供修复建议
"""

import socket

def test_port(host, port, timeout=2):
    """测试端口是否可访问"""
    try:
        s = socket.socket()
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except Exception:
        return False

def main():
    print("\n" + "="*60)
    print("智桥网络访问快速测试")
    print("="*60)

    # 测试常用地址
    test_addresses = [
        ('127.0.0.1', '本地回环'),
        ('10.113.22.99', 'ZeroTier'),
        ('100.66.1.8', 'NodeBabyLink'),
        ('192.168.2.1', '本地网络 1'),
        ('192.168.31.99', '本地网络 2'),
    ]


    # 测试表格
    print("\n端口访问测试:")
    print("-" * 60)
    print(f"{'地址':<20} {'描述':<15} {'8080':<8} {'8765':<8}")
    print("-" * 60)

    all_ok = True

    for ip, desc in test_addresses:
        port_8080_ok = test_port(ip, 8080)
        port_8765_ok = test_port(ip, 8765)

        status_8080 = "✅" if port_8080_ok else "❌"
        status_8765 = "✅" if port_8765_ok else "❌"

        print(f"{ip:<20} {desc:<15} {status_8080:<8} {status_8765:<8}")

        if ip != '127.0.0.1':
            if not port_8080_ok or not port_8765_ok:
                all_ok = False

    print("-" * 60)

    # 分析结果
    print("\n" + "="*60)
    print("诊断结果")
    print("="*60)

    if all_ok:
        print("\n✅ 所有地址都可以访问！")
        print("\n如果仍然无法从外部访问，请检查：")
        print("1. 外部机器的网络连接")
        print("2. 外部机器的防火墙设置")
        print("3. 路由器/网关配置")
    else:
        print("\n❌ 某些地址无法访问")
        print("\n可能的原因：")
        print("1. 防火墙阻止了外部访问")
        print("2. 网络接口配置问题")
        print("3. 路由器/网关配置问题")

        print("\n建议的解决方案：")
        print("\n【选项 1】开放防火墙端口 (推荐)")
        print("  sudo ufw allow 8080/tcp")
        print("  sudo ufw allow 8765/tcp")
        print("  sudo ufw reload")

        print("\n【选项 2】临时关闭防火墙 (测试用)")
        print("  sudo ufw disable")

        print("\n【选项 3】查看详细诊断")
        print("  python3 scripts/diagnose_network.py")

        print("\n【选项 4】查看故障排查文档")
        print("  docs/NETWORK_ACCESS_TROUBLESHOOTING.md")

    # 提供可用地址
    print("\n" + "="*60)
    print("可用访问地址")
    print("="*60)

    available = []
    for ip, desc in test_addresses:
        if test_port(ip, 8080) and test_port(ip, 8765):
            available.append((ip, desc))

    if available:
        print("\n可以使用以下地址访问服务：\n")
        for ip, desc in available:
            print(f"  {desc} ({ip}):")
            print(f"    - Web UI: http://{ip}:8080/web/ui/index.html")
            print(f"    - API 文档: http://{ip}:8080/docs")
            print(f"    - WebSocket: ws://{ip}:8765")
            print()
    else:
        print("\n没有找到可用的访问地址！")

    print("="*60 + "\n")

if __name__ == "__main__":
    main()
