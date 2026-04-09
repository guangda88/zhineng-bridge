#!/usr/bin/env python3
"""
初始化认证数据库

功能:
- 初始化数据库表
- 创建默认管理员用户（如果不存在）
"""

import secrets
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent / "relay-server"))

from logger import configure_logging, get_logger
from user_auth import UserRole, auth_manager

from config import settings


def init_database():
    """初始化数据库并创建默认管理员用户"""
    # 配置日志
    configure_logging(log_level="INFO", log_format="console", log_file=None)

    logger = get_logger(__name__)
    logger.info("Initializing authentication database")

    # 确保目录存在
    settings.ensure_directories()

    # 数据库已经通过 UserDatabase 自动初始化
    db = auth_manager.db
    logger.info("Database initialized", db_path=db.db_path)

    # 检查是否已存在管理员用户
    admin_user = db.get_user(username="admin")

    if admin_user:
        logger.info(
            "Admin user already exists", user_id=admin_user.user_id, username=admin_user.username
        )
    else:
        # 创建默认管理员用户
        logger.info("Creating default admin user")

        # 生成安全的随机密码
        admin_password = secrets.token_urlsafe(16)

        try:
            admin_user = db.create_user(
                username="admin",
                password=admin_password,  # 使用生成的随机密码
                email="admin@zhineng-bridge.local",
                role=UserRole.ADMIN,
                permissions=["read", "write", "admin", "manage_users", "manage_sessions"],
            )

            logger.info(
                "Admin user created successfully",
                user_id=admin_user.user_id,
                username=admin_user.username,
                email=admin_user.email,
                role=admin_user.role.value,
            )

            print("\n" + "=" * 60)
            print("✅ 认证数据库初始化成功")
            print("=" * 60)
            print(f"📊 数据库路径: {db.db_path}")
            print(f"👤 管理员用户名: {admin_user.username}")
            print(f"🔑 管理员密码: {admin_password}")
            print(f"📧 管理员邮箱: {admin_user.email}")
            print(f"🎭 管理员角色: {admin_user.role.value}")
            print("\n" + "⚠️  重要提示: " + "=" * 46)
            print("1. 请妥善保存上述密码，此密码不会再次显示")
            print("2. 登录后请立即修改密码")
            print("3. 建议启用双因素认证（如支持）")
            print("=" * 60 + "\n")

        except Exception as e:
            logger.error("Failed to create admin user", error=str(e), exc_info=True)
            print(f"\n❌ 创建管理员用户失败: {e}")
            return False

    return True


if __name__ == "__main__":
    try:
        success = init_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  初始化已取消")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
