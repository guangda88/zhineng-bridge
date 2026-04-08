#!/usr/bin/env python3
"""
VAPID Key Generator

生成用于Web Push通知的VAPID密钥对
VAPID (Voluntary Application Server Identification)
使用ECDSA P-256曲线
"""

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64


def generate_vapid_keys():
    """生成VAPID密钥对"""
    # 生成P-256椭圆曲线密钥对
    private_key = ec.generate_private_key(ec.SECP256R1())

    # 序列化私钥 (PKCS8格式)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # 获取公钥
    public_key = private_key.public_key()

    # 序列化公钥 (SubjectPublicKeyInfo格式)
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # 生成URL安全的Base64编码的公钥（用于前端配置）
    # VAPID需要去掉PEM格式中的头尾和换行符，然后Base64编码
    public_key_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # 生成适合Web Push的Base64URL编码
    # Web Push需要去掉65字节的DER编码中的前两个字节（算法标识符）
    public_key_bytes = public_key_der
    if len(public_key_bytes) == 65 and public_key_bytes[0] == 0x04:
        public_key_bytes = public_key_bytes[1:]

    public_key_base64url = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')

    # 同样处理私钥
    private_key_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # 私钥DER编码通常是32字节，但可能带有其他信息
    # 提取实际的私钥字节（通常在DER结构的最后32字节）
    if len(private_key_der) > 32:
        private_key_bytes = private_key_der[-32:]
    else:
        private_key_bytes = private_key_der

    private_key_base64url = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8').rstrip('=')

    return {
        'private_key_pem': private_pem.decode('utf-8'),
        'public_key_pem': public_pem.decode('utf-8'),
        'public_key_base64url': public_key_base64url,
        'private_key_base64url': private_key_base64url
    }


def main():
    """主函数"""
    print("=" * 60)
    print("VAPID密钥生成器")
    print("=" * 60)
    print()

    keys = generate_vapid_keys()

    print("✅ VAPID密钥对生成成功！")
    print()
    print("-" * 60)
    print("📋 PEM格式 (用于服务器端存储)")
    print("-" * 60)
    print()
    print("私钥:")
    print(keys['private_key_pem'])
    print("公钥:")
    print(keys['public_key_pem'])
    print()

    print("-" * 60)
    print("🔑 Base64URL格式 (用于配置)")
    print("-" * 60)
    print()
    print(f"VAPID_PUBLIC_KEY (前端配置): {keys['public_key_base64url']}")
    print(f"VAPID_PRIVATE_KEY (服务器配置): {keys['private_key_base64url']}")
    print()

    print("-" * 60)
    print("📝 配置说明")
    print("-" * 60)
    print()
    print("1. 将 VAPID_PUBLIC_KEY 添加到 web/ui/js/push.js 第55行:")
    print("   applicationServerKey: this.urlBase64ToUint8Array(")
    print(f"       '{keys['public_key_base64url']}'")
    print("   )")
    print()
    print("2. 将 VAPID_PRIVATE_KEY 添加到服务器配置文件:")
    print("   VAPID_PRIVATE_KEY={}" + keys['private_key_base64url'])
    print()
    print("3. 保存私钥PEM格式到文件 (可选):")
    print("   echo '{}' > vapid_private_key.pem".format(keys['private_key_pem'].strip().replace('\n', '\\n')))
    print()
    print("=" * 60)
    print("✅ 完成！请按照上述说明配置VAPID密钥")
    print("=" * 60)

    return keys


if __name__ == '__main__':
    main()
