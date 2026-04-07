#!/usr/bin/env python3
"""
智桥配置管理

使用 pydantic-settings 进行配置管理
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, field_validator
from typing import Optional, List
from pathlib import Path
import os
import secrets


class ServerSettings(BaseSettings):
    """服务器配置"""

    model_config = SettingsConfigDict(
        env_prefix="ZHINENG_BRIDGE_",
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8765
    ws_host: str = "localhost"
    ws_hosts: List[str] = []
    max_connections: int = 100

    # 会话配置
    session_timeout: int = 3600  # 秒
    max_sessions: int = 100

    # 心跳配置
    ping_interval: int = 10  # 秒
    ping_timeout: int = 5  # 秒

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"  # json 或 console
    log_file: Optional[str] = None

    # 安全配置
    enable_wss: bool = False
    cert_file: Optional[str] = None
    key_file: Optional[str] = None

    # CORS 配置
    enable_cors: bool = False
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["GET", "POST", "OPTIONS"]

    # 工作目录
    base_dir: str = str(Path.home() / ".zhineng-bridge")
    temp_dir: str = str(Path.home() / ".zhineng-bridge" / "tmp")

    # 性能配置
    enable_compression: bool = True
    buffer_size: int = 100000

    @field_validator('base_dir', 'temp_dir')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """验证路径安全，防止路径遍历攻击"""
        # 解析为绝对路径
        path = Path(v).resolve()

        # 检查路径是否在用户主目录下（防止系统目录访问）
        home_dir = Path.home().resolve()
        try:
            path.relative_to(home_dir)
        except ValueError:
            raise ValueError(f"Path must be within home directory: {v}")

        # 检查路径是否包含 .. 或可疑字符
        if ".." in str(path) or "://" in str(path):
            raise ValueError(f"Invalid path characters detected: {v}")

        return str(path)

    @model_validator(mode='after')
    def validate_cert_paths(self) -> 'ServerSettings':
        """验证证书文件路径（仅在启用 WSS 时）"""
        # 只有在启用 WSS 时才验证证书文件
        if self.enable_wss:
            for field_name, value in [('cert_file', self.cert_file), ('key_file', self.key_file)]:
                if value is None:
                    raise ValueError(f"{field_name} is required when WSS is enabled")

                path = Path(value).resolve()

                # 确保文件存在
                if not path.exists():
                    raise ValueError(f"{field_name} does not exist: {value}")

                # 检查路径是否在项目目录下或用户主目录下
                project_root = Path(__file__).parent.parent.resolve()
                home_dir = Path.home().resolve()
                try:
                    path.relative_to(project_root)
                except ValueError:
                    try:
                        path.relative_to(home_dir)
                    except ValueError:
                        raise ValueError(f"{field_name} must be within project or home directory: {value}")

        return self


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    model_config = SettingsConfigDict(
        env_prefix="ZHINENG_BRIDGE_DB_",
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # SQLite 配置
    db_path: str = "zhineng-bridge.db"
    enable_sqlite: bool = True

    # PostgreSQL 配置（可选）
    pg_host: Optional[str] = None
    pg_port: Optional[int] = 5432
    pg_database: Optional[str] = None
    pg_user: Optional[str] = None
    pg_password: Optional[str] = None


class SecuritySettings(BaseSettings):
    """安全配置"""

    model_config = SettingsConfigDict(
        env_prefix="ZHINENG_BRIDGE_SECURITY_",
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 认证配置
    enable_auth: bool = False
    auth_type: str = "token"  # token 或 oauth2

    # CSRF 保护
    enable_csrf_protection: bool = True  # 启用CSRF保护（建议与认证一起使用）

    # 速率限制
    enable_rate_limit: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # 密钥配置
    secret_key: Optional[str] = None
    encryption_key: Optional[str] = None

    @model_validator(mode='after')
    def validate_secret_key(self) -> 'SecuritySettings':
        """验证 secret_key 配置"""
        if self.enable_auth and not self.secret_key:
            # 如果启用了认证但没有提供 secret_key，生成一个警告
            # 实际值将在运行时由 TokenAuth/JWTAuth 生成
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "Authentication enabled but no secret_key provided. "
                "A random key will be generated. "
                "Set ZHINENG_BRIDGE_SECURITY_SECRET_KEY for production use."
            )
        return self

    # IP 白名单
    allowed_ips: List[str] = []
    blocked_ips: List[str] = []

    # OAuth2 配置
    github_oauth_client_id: Optional[str] = None
    github_oauth_client_secret: Optional[str] = None
    google_oauth_client_id: Optional[str] = None
    google_oauth_client_secret: Optional[str] = None


class MonitoringSettings(BaseSettings):
    """监控配置"""

    model_config = SettingsConfigDict(
        env_prefix="ZHINENG_BRIDGE_MONITORING_",
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Prometheus 配置
    enable_prometheus: bool = False
    prometheus_port: int = 9090

    # 健康检查
    enable_health_check: bool = True
    health_check_path: str = "/health"

    # 性能监控
    enable_performance_monitoring: bool = True
    performance_report_interval: int = 60  # 秒

    # HTTP 服务器配置（用于 OAuth2 回调和健康检查）
    enable_http_server: bool = True
    http_port: int = 8000


class Settings:
    """配置聚合"""

    def __init__(self):
        self.server = ServerSettings()
        self.database = DatabaseSettings()
        self.security = SecuritySettings()
        self.monitoring = MonitoringSettings()

    def ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.server.base_dir,
            self.server.temp_dir,
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    SENSITIVE_FIELDS = {
        "secret_key", "encryption_key",
        "github_oauth_client_secret", "google_oauth_client_secret",
        "pg_password",
    }

    def to_dict(self, redact_secrets: bool = True) -> dict:
        """转换为字典"""
        result = {
            "server": self.server.model_dump(),
            "database": self.database.model_dump(),
            "security": self.security.model_dump(),
            "monitoring": self.monitoring.model_dump(),
        }
        if redact_secrets:
            for section_name, section_data in result.items():
                if isinstance(section_data, dict):
                    for key in section_data:
                        if key in self.SENSITIVE_FIELDS and section_data[key]:
                            section_data[key] = "***REDACTED***"
        return result

    def log_config(self):
        """记录配置信息（自动脱敏）"""
        import structlog

        logger = structlog.get_logger()
        logger.info("Configuration loaded", **self.to_dict(redact_secrets=True))


# ============================================================================
# 全局配置实例
# ============================================================================

settings = Settings()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "ServerSettings",
    "DatabaseSettings",
    "SecuritySettings",
    "MonitoringSettings",
    "Settings",
    "settings",
]
