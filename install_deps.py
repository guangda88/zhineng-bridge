#!/usr/bin/env python3
"""
依赖安装脚本
自动检测 Python 版本并安装依赖
"""

import subprocess
import sys
from pathlib import Path


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, got {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def upgrade_pip():
    """升级 pip"""
    print("\n📦 Upgrading pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✅ pip upgraded successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to upgrade pip")
        return False


def install_requirements(req_file: str, description: str):
    """安装依赖文件"""
    print(f"\n📦 Installing {description}...")
    req_path = Path(req_file).resolve()

    # 验证路径安全：防止路径遍历
    current_dir = Path.cwd().resolve()
    try:
        req_path.relative_to(current_dir)
    except ValueError:
        print(f"❌ Invalid path (must be within current directory): {req_file}")
        return False

    # 检查文件是否存在且是 .txt 文件
    if not req_path.exists():
        print(f"❌ Requirements file not found: {req_file}")
        return False

    if not req_path.suffix == ".txt":
        print(f"❌ File must be a .txt file: {req_file}")
        return False

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_path)])
        print(f"✅ {description} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {description}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 智桥 (Zhineng-bridge) 依赖安装脚本")
    print("=" * 60)

    # 检查 Python 版本
    if not check_python_version():
        sys.exit(1)

    # 升级 pip
    if not upgrade_pip():
        print("⚠️  Warning: pip upgrade failed, continuing anyway...")

    # 获取安装模式
    print("\n" + "=" * 60)
    print("请选择安装模式:")
    print("=" * 60)
    print("1. 最小安装 (仅核心功能)")
    print("2. 生产安装 (包含监控和日志)")
    print("3. 开发安装 (包含测试和开发工具)")
    print("4. 完整安装 (所有依赖)")
    print("=" * 60)

    choice = input("\n请输入选择 (1-4, 默认: 2): ").strip() or "2"

    # 根据选择安装依赖
    success = True

    if choice == "1":
        # 最小安装
        success = install_requirements("requirements-minimal.txt", "minimal dependencies")
    elif choice == "2":
        # 生产安装
        success &= install_requirements("requirements.txt", "production dependencies")
    elif choice == "3":
        # 开发安装
        success &= install_requirements("requirements.txt", "production dependencies")
        success &= install_requirements("requirements-dev.txt", "development dependencies")
    elif choice == "4":
        # 完整安装
        success &= install_requirements("requirements.txt", "production dependencies")
        success &= install_requirements("requirements-dev.txt", "development dependencies")

        # 额外安装可选依赖
        print("\n📦 Installing optional dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "redis>=5.0,<6.0"])
            print("✅ Redis support installed")
        except subprocess.CalledProcessError:
            print("⚠️  Redis installation failed (optional)")

    else:
        print(f"❌ Invalid choice: {choice}")
        sys.exit(1)

    # 验证安装
    if success:
        print("\n" + "=" * 60)
        print("✅ 依赖安装完成!")
        print("=" * 60)
        print("\n验证安装:")
        try:
            import websockets

            print(f"  ✅ websockets {websockets.__version__}")
        except ImportError:
            print("  ❌ websockets")

        try:
            import pydantic

            print(f"  ✅ pydantic {pydantic.VERSION}")
        except ImportError:
            print("  ❌ pydantic")

        try:
            import psutil

            print(f"  ✅ psutil {psutil.__version__}")
        except ImportError:
            print("  ❌ psutil")

        print("\n下一步:")
        print("  1. 配置环境变量 (复制 .env.example 到 .env)")
        print("  2. 运行服务器: python3 relay-server/start_server.py")
        print("  3. 访问 Web UI: http://192.168.2.1:8000/web/ui/index.html")
    else:
        print("\n" + "=" * 60)
        print("❌ 依赖安装失败")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
