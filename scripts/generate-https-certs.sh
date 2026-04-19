#!/bin/bash
# 智桥 HTTPS 自签名证书生成脚本
# 用于开发环境

set -e

CERT_DIR="${1:-$HOME/.zhineng-bridge/certs}"
CERT_NAME="${2:-zhineng-bridge}"
DAYS_VALID="${3:-365}"

mkdir -p "$CERT_DIR"

echo "🔐 生成自签名 SSL 证书..."
echo "📁 证书目录: $CERT_DIR"
echo "📜 证书名称: $CERT_NAME"
echo "⏰ 有效期: $DAYS_VALID 天"
echo ""

# 生成私钥和证书
openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/${CERT_NAME}.key" \
    -out "$CERT_DIR/${CERT_NAME}.crt" \
    -days $DAYS_VALID \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=ZhiBridge/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:*.local,IP:127.0.0.1"

# 生成 PKCS#12 格式（某些浏览器需要）
openssl pkcs12 -export -in "$CERT_DIR/${CERT_NAME}.crt" \
    -inkey "$CERT_DIR/${CERT_NAME}.key" \
    -out "$CERT_DIR/${CERT_NAME}.p12" \
    -name "ZhiBridge" \
    -passout pass:zhineng-bridge

echo ""
echo "✅ 证书生成完成！"
echo ""
echo "生成的文件："
echo "  - $CERT_DIR/${CERT_NAME}.key  (私钥)"
echo "  - $CERT_DIR/${CERT_NAME}.crt  (证书)"
echo "  - $CERT_DIR/${CERT_NAME}.p12  (PKCS#12 格式，用于某些浏览器)"
echo ""
echo "📝 使用说明："
echo ""
echo "1. 在 start_server.py 中使用这些证书："
echo "   cert_file = \"$CERT_DIR/${CERT_NAME}.crt\""
echo "   key_file = \"$CERT_DIR/${CERT_NAME}.key\""
echo ""
echo "2. 浏览器中访问时，点击 'Advanced' -> 'Proceed to localhost'"
echo ""
echo "3. 将证书添加到浏览器的受信任证书存储："
echo "   - Chrome: 设置 -> 隐私和安全 -> 安全 -> 管理证书 -> 受信任的根证书颁发机构 -> 导入"
echo "   - Firefox: 设置 -> 隐私与安全 -> 证书 -> 证书颁发机构 -> 导入"
echo "   - 选择: $CERT_DIR/${CERT_NAME}.crt"
echo ""
echo "4. 如果使用 PKCS#12 格式，密码是: zhineng-bridge"
echo ""
echo "⚠️  警告：这是自签名证书，仅用于开发环境！"
echo "   生产环境请使用 Let's Encrypt 或其他 CA 颁发的证书。"
