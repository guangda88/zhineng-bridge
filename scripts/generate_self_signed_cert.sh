#!/bin/bash
# 生成自签名SSL证书（用于开发测试）

set -e

CERT_DIR="/home/ai/zhineng-bridge/nginx/ssl"
CERT_FILE="${CERT_DIR}/cert.pem"
KEY_FILE="${CERT_DIR}/key.pem"

echo "🔐 生成自签名SSL证书..."
echo ""

# 创建证书目录
mkdir -p "${CERT_DIR}"

# 生成证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "${KEY_FILE}" \
  -out "${CERT_FILE}" \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=ZhinengBridge/OU=Development/CN=*.zhineng-bridge.local" \
  -addext "subjectAltName=DNS:*.zhineng-bridge.local,DNS:localhost,IP:127.0.0.1,IP:10.113.22.99,IP:100.66.1.8,IP:192.168.2.1"

# 设置权限
chmod 644 "${CERT_FILE}"
chmod 600 "${KEY_FILE}"

echo "✅ 证书生成成功！"
echo ""
echo "证书文件: ${CERT_FILE}"
echo "私钥文件: ${KEY_FILE}"
echo ""
echo "⚠️  注意: 这是自签名证书，仅用于开发测试"
echo "   生产环境请使用 Let's Encrypt 或商业证书"
echo ""
echo "有效期: 365 天"
echo ""
