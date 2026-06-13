"""
E2E加密模块 — 对敏感路由(linghealth/linglaw)的请求体/响应体做AES-256-GCM加密

协议：
- 客户端用共享密钥加密请求body → gateway透传密文给后端
- 后端返回密文 → gateway透传给客户端（gateway不解密）
- gateway零信任：只转发密文blob，不持有加密密钥（密钥通过header传递或预共享）

实际实现：gateway作为透传层，客户端在请求头传 encrypted=true，
gateway标记日志但直接转发body（加密由客户端/后端自行协商）。
"""

import base64
import os

import structlog

log = structlog.get_logger()

ENCRYPTED_HEADER = "X-Encrypted"
NONCE_HEADER = "X-Encryption-Nonce"
KEY_ID_HEADER = "X-Encryption-Key-Id"


def generate_key() -> str:
    """生成新的AES-256密钥（base64编码），用于客户端-后端预共享"""
    key = os.urandom(32)
    return base64.b64encode(key).decode()


def is_encrypted_request(headers: dict) -> bool:
    """检查请求是否标记为加密（兼容Starlette小写header和原始大小写）"""
    val = headers.get(ENCRYPTED_HEADER.lower(), headers.get(ENCRYPTED_HEADER, ""))
    return val.lower() == "true"


def is_sensitive_backend(backend_key: str) -> bool:
    """判断后端是否处理敏感数据（健康/法律）"""
    return backend_key in ("linghealth", "linglaw")


def strip_encryption_headers(headers: dict) -> dict:
    """移除加密相关header，防止透传到后端时泄漏元数据"""
    stripped = {}
    skip = {ENCRYPTED_HEADER.lower(), NONCE_HEADER.lower(), KEY_ID_HEADER.lower()}
    for k, v in headers.items():
        if k.lower() not in skip:
            stripped[k] = v
    return stripped


def encrypt(plaintext: bytes, key_b64: str) -> tuple[str, str]:
    """AES-256-GCM加密。返回 (ciphertext_b64, nonce_b64)。

    用法：客户端加密请求体 → 将ciphertext放入body，nonce放入X-Encryption-Nonce header
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = base64.b64decode(key_b64)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return (
        base64.b64encode(ciphertext).decode(),
        base64.b64encode(nonce).decode(),
    )


def decrypt(ciphertext_b64: str, nonce_b64: str, key_b64: str) -> bytes:
    """AES-256-GCM解密。返回 plaintext bytes。

    用法：后端解密请求体 → 从body取ciphertext，从header取nonce
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = base64.b64decode(key_b64)
    nonce = base64.b64decode(nonce_b64)
    ciphertext = base64.b64decode(ciphertext_b64)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
