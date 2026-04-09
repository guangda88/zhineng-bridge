#!/usr/bin/env python3
"""
智桥 SSL/TLS 证书管理

生成自签名证书用于开发和测试
"""

import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from logger import get_logger

from config import settings

logger = get_logger(__name__)


def validate_path_safety(path: str, param_name: str = "path") -> str:
    """
    验证路径是否安全，防止路径遍历攻击

    Args:
        path: 要验证的路径
        param_name: 参数名称（用于错误消息）

    Returns:
        安全的路径字符串

    Raises:
        ValueError: 如果路径不安全
    """
    # 解析路径
    resolved_path = Path(path).resolve()

    # 检查是否包含路径遍历（.. 或 ~）
    path_str = str(path)
    if ".." in path_str or "~" in path_str:
        raise ValueError(f"Invalid {param_name}: path traversal not allowed. " f"Received: {path}")

    # 检查是否为绝对路径且在预期目录下（可选，根据需求）
    # 对于本用例，我们允许相对路径，但会解析为绝对路径

    # 检查文件名是否只包含安全字符
    filename = Path(path).name
    if not re.match(r"^[a-zA-Z0-9._-]+$", filename):
        raise ValueError(
            f"Invalid {param_name}: filename contains invalid characters. "
            f"Only alphanumeric, dot, underscore, and hyphen are allowed. "
            f"Received: {filename}"
        )

    return str(resolved_path)


def generate_self_signed_cert(
    output_dir: str = None,
    cert_filename: str = "cert.pem",
    key_filename: str = "key.pem",
    common_name: str = "localhost",
    days_valid: int = 365,
    force: bool = False,
) -> Tuple[str, str]:
    """
    生成自签名 SSL/TLS 证书

    Args:
        output_dir: 输出目录（默认：~/.zhineng-bridge/certs）
        cert_filename: 证书文件名
        key_filename: 私钥文件名
        common_name: 通用名称（CN）
        days_valid: 有效天数
        force: 是否强制覆盖已存在的证书

    Returns:
        (证书路径, 私钥路径)

    Raises:
        FileNotFoundError: 如果 openssl 命令不可用
        RuntimeError: 如果证书生成失败
    """
    logger = get_logger(__name__)

    # 验证文件名是否安全
    try:
        validated_cert_filename = validate_path_safety(cert_filename, "cert_filename")
        validated_key_filename = validate_path_safety(key_filename, "key_filename")
    except ValueError as e:
        raise ValueError(f"Invalid filename: {e}")

    # 设置输出目录
    if output_dir is None:
        output_dir = str(Path.home() / ".zhineng-bridge" / "certs")

    cert_dir = Path(output_dir)
    cert_dir.mkdir(parents=True, exist_ok=True)

    cert_path = cert_dir / validated_cert_filename
    key_path = cert_dir / validated_key_filename

    # 检查证书是否已存在
    if cert_path.exists() and key_path.exists() and not force:
        logger.info(
            "SSL certificates already exist",
            cert_path=str(cert_path),
            key_path=str(key_path),
        )
        return str(cert_path), str(key_path)

    logger.info(
        "Generating self-signed SSL certificates",
        output_dir=output_dir,
        common_name=common_name,
        days_valid=days_valid,
    )

    # 检查 openssl 是否可用
    try:
        subprocess.run(
            ["openssl", "version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise FileNotFoundError(
            "openssl command not found. "
            "Please install OpenSSL: apt install openssl (Debian/Ubuntu) "
            "or brew install openssl (macOS)"
        )

    # 生成私钥和证书

    try:
        # 生成配置文件
        config_path = cert_dir / "openssl.cnf"
        config_content = f"""[req]
default_bits = 2048
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = CN
ST = State
L = City
O = ZhinengBridge
CN = {common_name}

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = {common_name}
DNS.2 = *.{common_name}
DNS.3 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
"""

        config_path.write_text(config_content)

        # 生成私钥
        logger.debug("Generating private key")
        subprocess.run(
            [
                "openssl",
                "genrsa",
                "-out",
                str(key_path),
                "2048",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # 生成证书
        logger.debug("Generating certificate")
        expiry_date = datetime.now() + timedelta(days=days_valid)

        subprocess.run(
            [
                "openssl",
                "req",
                "-new",
                "-x509",
                "-key",
                str(key_path),
                "-out",
                str(cert_path),
                "-days",
                str(days_valid),
                "-config",
                str(config_path),
                "-extensions",
                "v3_req",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # 设置适当的权限
        key_path.chmod(0o600)
        cert_path.chmod(0o644)

        logger.info(
            "SSL certificates generated successfully",
            cert_path=str(cert_path),
            key_path=str(key_path),
            expiry_date=expiry_date.isoformat(),
        )

        return str(cert_path), str(key_path)

    except subprocess.CalledProcessError as e:
        logger.error("Failed to generate SSL certificates", stderr=e.stderr)
        raise RuntimeError(f"Failed to generate SSL certificates: {e.stderr}")
    finally:
        # 清理配置文件
        if config_path.exists():
            config_path.unlink()


def validate_certificates(cert_path: str, key_path: str) -> Tuple[bool, Optional[str]]:
    """
    验证 SSL 证书和私钥是否匹配

    Args:
        cert_path: 证书文件路径
        key_path: 私钥文件路径

    Returns:
        (是否有效, 错误消息)
    """
    logger = get_logger(__name__)

    # 验证路径安全性
    try:
        cert_path = validate_path_safety(cert_path, "cert_path")
        key_path = validate_path_safety(key_path, "key_path")
    except ValueError as e:
        return False, f"Path validation failed: {e}"

    # 检查文件是否存在
    if not Path(cert_path).exists():
        return False, f"Certificate file not found: {cert_path}"
    if not Path(key_path).exists():
        return False, f"Private key file not found: {key_path}"

    try:
        # 提取证书模数
        cert_modulus = subprocess.run(
            [
                "openssl",
                "x509",
                "-noout",
                "-modulus",
                "-in",
                cert_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        # 提取私钥模数
        key_modulus = subprocess.run(
            [
                "openssl",
                "rsa",
                "-noout",
                "-modulus",
                "-in",
                key_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        # 比较模数
        if cert_modulus == key_modulus:
            logger.info("SSL certificates validated", cert_path=cert_path)
            return True, None
        else:
            error_msg = "Certificate and private key do not match"
            logger.error(error_msg, cert_path=cert_path, key_path=key_path)
            return False, error_msg

    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to validate certificates: {e.stderr}"
        logger.error(error_msg)
        return False, error_msg


def get_certificate_info(cert_path: str) -> dict:
    """
    获取 SSL 证书信息

    Args:
        cert_path: 证书文件路径

    Returns:
        证书信息字典
    """
    logger = get_logger(__name__)

    # 验证路径安全性
    try:
        cert_path = validate_path_safety(cert_path, "cert_path")
    except ValueError as e:
        logger.error("Certificate path validation failed", error=str(e))
        return {}

    try:
        # 获取证书文本
        cert_text = subprocess.run(
            [
                "openssl",
                "x509",
                "-in",
                cert_path,
                "-noout",
                "-text",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        # 解析关键信息
        info = {}

        for line in cert_text.split("\n"):
            line = line.strip()

            if "Subject:" in line:
                info["subject"] = line.split("Subject:")[1].strip()
            elif "Issuer:" in line:
                info["issuer"] = line.split("Issuer:")[1].strip()
            elif "Not Before:" in line:
                info["not_before"] = line.split("Not Before:")[1].strip()
            elif "Not After" in line:
                info["not_after"] = line.split("Not After:")[1].strip()
            elif "DNS:" in line or "IP Address:" in line:
                if "sans" not in info:
                    info["sans"] = []
                if "DNS:" in line:
                    sans = line.split("DNS:")[-1].strip()
                    info["sans"].extend(sans.split(", "))

        logger.debug("Certificate info retrieved", cert_path=cert_path)
        return info

    except subprocess.CalledProcessError as e:
        logger.error("Failed to get certificate info", error=e.stderr)
        return {}


def setup_development_certificates() -> Tuple[str, str]:
    """
    设置开发环境的 SSL 证书

    Returns:
        (证书路径, 私钥路径)
    """
    logger = get_logger(__name__)

    logger.info("Setting up development SSL certificates")

    # 生成证书
    cert_path, key_path = generate_self_signed_cert(
        common_name="localhost",
        days_valid=365,
        force=False,
    )

    # 验证证书
    is_valid, error_msg = validate_certificates(cert_path, key_path)
    if not is_valid:
        raise RuntimeError(f"Certificate validation failed: {error_msg}")

    logger.info(
        "Development SSL certificates ready",
        cert_path=cert_path,
        key_path=key_path,
    )

    return cert_path, key_path


def check_wss_requirements() -> Tuple[bool, list]:
    """
    检查 WSS 配置要求

    Returns:
        (是否满足要求, 缺失的配置项列表)
    """
    missing = []

    if settings.server.enable_wss:
        if not settings.server.cert_file:
            missing.append("ZHINENG_BRIDGE_CERT_FILE")
        if not settings.server.key_file:
            missing.append("ZHINENG_BRIDGE_KEY_FILE")

        # 如果配置了路径，检查文件是否存在
        if settings.server.cert_file and not Path(settings.server.cert_file).exists():
            missing.append(f"Certificate file not found: {settings.server.cert_file}")
        if settings.server.key_file and not Path(settings.server.key_file).exists():
            missing.append(f"Private key file not found: {settings.server.key_file}")

    return len(missing) == 0, missing


def print_wss_setup_instructions():
    """打印 WSS 设置说明"""
    print("\n" + "=" * 70)
    print("🔒 WSS (WebSocket Secure) Setup Instructions")
    print("=" * 70)
    print()
    print("To enable WSS (WebSocket Secure), you need to:")
    print()
    print("1. Generate SSL certificates (for development):")
    print(
        '   python3 -c "from relay-server.ssl_manager import setup_development_certificates; setup_development_certificates()"'
    )
    print()
    print("2. Set environment variables:")
    print("   export ZHINENG_BRIDGE_ENABLE_WSS=true")
    print("   export ZHINENG_BRIDGE_CERT_FILE=$HOME/.zhineng-bridge/certs/cert.pem")
    print("   export ZHINENG_BRIDGE_KEY_FILE=$HOME/.zhineng-bridge/certs/key.pem")
    print()
    print("3. Or add to .env file:")
    print("   ZHINENG_BRIDGE_ENABLE_WSS=true")
    print("   ZHINENG_BRIDGE_CERT_FILE=$HOME/.zhineng-bridge/certs/cert.pem")
    print("   ZHINENG_BRIDGE_KEY_FILE=$HOME/.zhineng-bridge/certs/key.pem")
    print()
    print("For production:")
    print("   Use certificates from a trusted CA (e.g., Let's Encrypt)")
    print("   Use a reverse proxy (nginx) with SSL termination")
    print()
    print("=" * 70 + "\n")


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "generate_self_signed_cert",
    "validate_certificates",
    "get_certificate_info",
    "setup_development_certificates",
    "check_wss_requirements",
    "print_wss_setup_instructions",
]
