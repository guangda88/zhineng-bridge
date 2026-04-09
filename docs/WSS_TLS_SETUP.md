# Production WSS/TLS Configuration Guide

## Overview

This guide provides comprehensive instructions for configuring WebSocket Secure (WSS) and TLS/SSL certificates for zhineng-bridge in production environments.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Setup](#development-setup)
3. [Production Setup](#production-setup)
   - [Let's Encrypt (Recommended)](#lets-encrypt-recommended)
   - [Commercial Certificates](#commercial-certificates)
4. [Reverse Proxy Configuration](#reverse-proxy-configuration)
5. [Configuration Options](#configuration-options)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Certificate Renewal](#certificate-renewal)

## Quick Start

### For Development (Self-Signed Certificates)

```bash
# 1. Generate self-signed certificates
python3 -c "from relay-server.ssl_manager import setup_development_certificates; setup_development_certificates()"

# 2. Configure environment
export ZHINENG_BRIDGE_ENABLE_WSS=true
export ZHINENG_BRIDGE_CERT_FILE=$HOME/.zhineng-bridge/certs/cert.pem
export ZHINENG_BRIDGE_KEY_FILE=$HOME/.zhineng-bridge/certs/key.pem

# 3. Start server
python3 relay-server/start_server.py
```

### For Production (Let's Encrypt)

```bash
# 1. Install certbot
sudo apt update
sudo apt install certbot

# 2. Generate certificate (standalone mode)
sudo certbot certonly --standalone -d yourdomain.com

# 3. Configure environment
export ZHINENG_BRIDGE_ENABLE_WSS=true
export ZHINENG_BRIDGE_CERT_FILE=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
export ZHINENG_BRIDGE_KEY_FILE=/etc/letsencrypt/live/yourdomain.com/privkey.pem

# 4. Start server
python3 relay-server/start_server.py
```

## Development Setup

### Self-Signed Certificates

Self-signed certificates are suitable for development and testing but will trigger security warnings in browsers.

#### Method 1: Using SSL Manager (Recommended)

```bash
# Generate certificates in default location
python3 -c "from relay-server.ssl_manager import setup_development_certificates; setup_development_certificates()"

# Generate with custom options
python3 -c "
from relay-server.ssl_manager import generate_self_signed_cert
generate_self_signed_cert(
    output_dir='/path/to/certs',
    cert_filename='cert.pem',
    key_filename='key.pem',
    common_name='localhost',
    days_valid=365,
    force=True
)
"
```

#### Method 2: Using OpenSSL Directly

```bash
# Create directory
mkdir -p ~/.zhineng-bridge/certs
cd ~/.zhineng-bridge/certs

# Generate private key
openssl genrsa -out key.pem 2048

# Generate certificate
openssl req -new -x509 -key key.pem -out cert.pem -days 365 \
  -subj "/C=CN/ST=State/L=City/O=ZhinengBridge/CN=localhost"

# Set permissions
chmod 600 key.pem
chmod 644 cert.pem
```

#### Method 3: Using manage_ssl.py Script

```bash
cd scripts
python3 manage_ssl.py generate --domain localhost --days 365
```

### Configure Development Environment

Create or update `.env` file:

```bash
# .env
ZHINENG_BRIDGE_ENABLE_WSS=true
ZHINENG_BRIDGE_CERT_FILE=$HOME/.zhineng-bridge/certs/cert.pem
ZHINENG_BRIDGE_KEY_FILE=$HOME/.zhineng-bridge/certs/key.pem
```

Or set environment variables:

```bash
export ZHINENG_BRIDGE_ENABLE_WSS=true
export ZHINENG_BRIDGE_CERT_FILE=$HOME/.zhineng-bridge/certs/cert.pem
export ZHINENG_BRIDGE_KEY_FILE=$HOME/.zhineng-bridge/certs/key.pem
```

### Browser Trust (Self-Signed)

For development with self-signed certificates, you'll need to explicitly trust the certificate:

1. **Chrome/Edge:**
   - Navigate to `https://localhost:8765`
   - Click "Advanced" → "Proceed to localhost (unsafe)"
   - Or import certificate via Settings → Privacy → Manage certificates

2. **Firefox:**
   - Navigate to `https://localhost:8765`
   - Click "Advanced" → "Accept the Risk and Continue"
   - Or import certificate via Settings → Certificates

3. **Safari:**
   - Navigate to `wss://localhost:8765`
   - Click "Show Details" → "Visit this website"
   - Or import certificate via Keychain Access

## Production Setup

### Let's Encrypt (Recommended)

Let's Encrypt provides free, automated, and trusted SSL certificates.

#### Prerequisites

- Domain name pointing to your server
- Port 80 and 443 open on firewall
- Root or sudo access

#### Installation

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install certbot

# CentOS/RHEL
sudo yum install certbot

# macOS
brew install certbot
```

#### Generating Certificates

**Option 1: Standalone Mode (Recommended for Direct WSS)**

```bash
# Stop any web server on port 80
sudo certbot certonly --standalone -d api.yourdomain.com -d ws.yourdomain.com

# Certificates will be saved to:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

**Option 2: Webroot Mode (With Existing Web Server)**

```bash
# If you have nginx/apache running on port 80
sudo certbot certonly --webroot -w /var/www/html -d api.yourdomain.com
```

**Option 3: DNS Challenge (Wildcard Certificates)**

```bash
# For wildcard certificates (*.yourdomain.com)
sudo certbot certonly --manual --preferred-challenges dns -d "*.yourdomain.com"
# Follow the instructions to add DNS TXT records
```

#### Configuration

```bash
# .env or environment variables
ZHINENG_BRIDGE_ENABLE_WSS=true
ZHINENG_BRIDGE_HOST=0.0.0.0
ZHINENG_BRIDGE_PORT=8765
ZHINENG_BRIDGE_CERT_FILE=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
ZHINENG_BRIDGE_KEY_FILE=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

#### Permissions

```bash
# Ensure the application user can read the certificates
sudo chgrp www-data /etc/letsencrypt/live/yourdomain.com/privkey.pem
sudo chmod 640 /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Commercial Certificates

For production environments requiring higher assurance or specific features.

#### Purchase and Generate CSR

```bash
# Generate private key
openssl genrsa -out yourdomain.com.key 2048

# Generate Certificate Signing Request (CSR)
openssl req -new -key yourdomain.com.key -out yourdomain.com.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"

# Submit CSR to your certificate authority (CA)
# After approval, download the certificate and CA bundle
```

#### Install Certificates

```bash
# Copy certificates to secure location
sudo mkdir -p /etc/ssl/zhineng-bridge
sudo cp yourdomain.com.crt /etc/ssl/zhineng-bridge/cert.pem
sudo cp ca-bundle.crt /etc/ssl/zhineng-bridge/chain.pem
sudo cat /etc/ssl/zhineng-bridge/cert.pem /etc/ssl/zhineng-bridge/chain.pem \
  > /etc/ssl/zhineng-bridge/fullchain.pem
sudo cp yourdomain.com.key /etc/ssl/zhineng-bridge/privkey.pem

# Set permissions
sudo chmod 644 /etc/ssl/zhineng-bridge/fullchain.pem
sudo chmod 600 /etc/ssl/zhineng-bridge/privkey.pem
```

#### Configuration

```bash
# .env or environment variables
ZHINENG_BRIDGE_ENABLE_WSS=true
ZHINENG_BRIDGE_CERT_FILE=/etc/ssl/zhineng-bridge/fullchain.pem
ZHINENG_BRIDGE_KEY_FILE=/etc/ssl/zhineng-bridge/privkey.pem
```

## Reverse Proxy Configuration

Using a reverse proxy (nginx) provides additional security, load balancing, and SSL termination.

### Nginx Configuration

#### Basic Configuration

```nginx
# /etc/nginx/sites-available/zhineng-bridge
upstream zhineng_bridge {
    server 127.0.0.1:8765;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # WebSocket upgrade headers
    location / {
        proxy_pass http://zhineng_bridge;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-lived WebSocket connections
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
}
```

#### Advanced Configuration with Security

```nginx
# /etc/nginx/sites-available/zhineng-bridge
upstream zhineng_bridge {
    server 127.0.0.1:8765;
    keepalive 64;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL configuration (Mozilla Intermediate)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # SSL session cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=websocket_limit:10m rate=10r/s;

    # WebSocket upgrade headers
    location / {
        limit_req zone=websocket_limit burst=20 nodelay;

        proxy_pass http://zhineng_bridge;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable buffering for WebSocket
        proxy_buffering off;

        # Timeouts for long-lived WebSocket connections
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
}
```

#### Enable Configuration

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/zhineng-bridge /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Server Configuration (Behind Proxy)

When using a reverse proxy, configure the server to listen locally only:

```bash
# .env or environment variables
ZHINENG_BRIDGE_HOST=127.0.0.1  # Only accept local connections
ZHINENG_BRIDGE_PORT=8765
ZHINENG_BRIDGE_ENABLE_WSS=false  # Let nginx handle SSL
```

## Configuration Options

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ZHINENG_BRIDGE_ENABLE_WSS` | bool | `false` | Enable WSS (WebSocket Secure) |
| `ZHINENG_BRIDGE_CERT_FILE` | string | `null` | Path to SSL certificate file |
| `ZHINENG_BRIDGE_KEY_FILE` | string | `null` | Path to SSL private key file |
| `ZHINENG_BRIDGE_HOST` | string | `0.0.0.0` | Server host address |
| `ZHINENG_BRIDGE_PORT` | int | `8765` | Server port |

### Configuration File (.env)

```bash
# Server Configuration
ZHINENG_BRIDGE_HOST=0.0.0.0
ZHINENG_BRIDGE_PORT=8765
ZHINENG_BRIDGE_MAX_CONNECTIONS=100

# WSS/TLS Configuration
ZHINENG_BRIDGE_ENABLE_WSS=true
ZHINENG_BRIDGE_CERT_FILE=/path/to/cert.pem
ZHINENG_BRIDGE_KEY_FILE=/path/to/key.pem

# Security Configuration
ZHINENG_BRIDGE_SECURITY_ENABLE_AUTH=true
ZHINENG_BRIDGE_SECURITY_ENABLE_RATE_LIMIT=true

# Monitoring Configuration
ZHINENG_BRIDGE_MONITORING_ENABLE_PROMETHEUS=true
ZHINENG_BRIDGE_MONITORING_ENABLE_HEALTH_CHECK=true
```

### Programmatic Configuration

```python
# relay-server/config.py
from config import settings

# Update settings programmatically
settings.server.enable_wss = True
settings.server.cert_file = "/path/to/cert.pem"
settings.server.key_file = "/path/to/key.pem"
```

## Best Practices

### 1. Certificate Management

- ✅ **Use trusted CAs for production** (Let's Encrypt, DigiCert, etc.)
- ✅ **Set appropriate validity periods** (90 days for Let's Encrypt, 1 year for commercial)
- ✅ **Secure private keys** with proper permissions (600 or 400)
- ✅ **Use separate certificates** for development and production
- ❌ **Never commit certificates** to version control
- ❌ **Don't use self-signed certificates** in production

### 2. SSL/TLS Configuration

- ✅ **Use modern TLS versions** (TLS 1.2, TLS 1.3)
- ✅ **Disable weak ciphers** and protocols (SSLv2, SSLv3, TLS 1.0, TLS 1.1)
- ✅ **Enable HSTS** (HTTP Strict Transport Security)
- ✅ **Use strong cipher suites** (recommended by Mozilla SSL Config Generator)
- ✅ **Enable OCSP stapling** for performance
- ❌ **Don't use SHA-1** certificates
- ❌ **Don't use default self-signed certificates** in production

### 3. Key Security

- ✅ **Generate strong private keys** (2048-bit RSA or 256-bit ECC)
- ✅ **Protect private keys** with restricted permissions
- ✅ **Store keys securely** (encrypted storage, hardware security modules)
- ✅ **Rotate keys regularly** (at least annually)
- ❌ **Never share private keys**
- ❌ **Don't store keys** in application directories

### 4. Reverse Proxy Configuration

- ✅ **Use nginx or Apache** as reverse proxy for production
- ✅ **Implement rate limiting** to prevent abuse
- ✅ **Add security headers** (HSTS, X-Frame-Options, CSP)
- ✅ **Configure proper timeouts** for long-lived WebSocket connections
- ✅ **Enable SSL session caching** for performance
- ❌ **Don't expose WebSocket server** directly to internet
- ❌ **Don't use default nginx configurations**

### 5. Monitoring and Logging

- ✅ **Monitor certificate expiry** and set up alerts
- ✅ **Log SSL/TLS errors** and connection issues
- ✅ **Track certificate renewal** status
- ✅ **Monitor WSS connection metrics**
- ❌ **Don't ignore certificate warnings** in logs

### 6. Backup and Recovery

- ✅ **Backup certificates** in secure, encrypted storage
- ✅ **Document certificate renewal** procedures
- ✅ **Test certificate restoration** process
- ✅ **Have rollback plan** for certificate updates
- ❌ **Don't store backups** in same location as active certificates

## Troubleshooting

### Certificate Not Found

**Error:** `Certificate file not found: /path/to/cert.pem`

**Solutions:**
1. Verify certificate file exists: `ls -la /path/to/cert.pem`
2. Check file permissions: `chmod 644 /path/to/cert.pem`
3. Verify environment variables: `echo $ZHINENG_BRIDGE_CERT_FILE`
4. Check .env file syntax

### Private Key Mismatch

**Error:** `Certificate and private key do not match`

**Solutions:**
1. Verify certificate and key modulus match:
   ```bash
   openssl x509 -noout -modulus -in cert.pem | openssl md5
   openssl rsa -noout -modulus -in key.pem | openssl md5
   ```
2. Regenerate certificates
3. Verify you're using the correct certificate/key pair

### Browser Trust Issues (Self-Signed)

**Error:** `NET::ERR_CERT_AUTHORITY_INVALID`

**Solutions:**
1. This is expected for self-signed certificates in production
2. Use Let's Encrypt or commercial certificates for production
3. For development, manually trust the certificate in browser

### WebSocket Connection Failed

**Error:** `WebSocket connection failed: ssl.SSLCertVerificationError`

**Solutions:**
1. Verify certificate chain is complete
2. Check intermediate certificates are included
3. Verify certificate validity dates
4. Check certificate hostname matches server

### Port Already in Use

**Error:** `Address already in use: 8765`

**Solutions:**
1. Find process using port: `sudo lsof -i :8765`
2. Kill conflicting process or use different port
3. Check if nginx/apache is already using the port

### Certificate Expired

**Error:** `Certificate has expired`

**Solutions:**
1. Renew certificate (Let's Encrypt): `sudo certbot renew`
2. Regenerate certificate if self-signed
3. Update system time if incorrect

### Permission Denied

**Error:** `Permission denied: /path/to/key.pem`

**Solutions:**
1. Check file permissions: `ls -la /path/to/key.pem`
2. Fix permissions: `sudo chmod 600 /path/to/key.pem`
3. Verify file ownership: `sudo chown user:group /path/to/key.pem`

### Verification Commands

```bash
# Check certificate info
openssl x509 -in cert.pem -text -noout

# Check certificate validity
openssl x509 -in cert.pem -noout -dates

# Verify certificate and key match
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa -noout -modulus -in key.pem | openssl md5

# Test SSL connection
openssl s_client -connect localhost:8765 -servername localhost

# Check certificate chain
openssl s_client -connect localhost:8765 -showcerts
```

## Certificate Renewal

### Let's Encrypt (Automated)

```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Renew certificates
sudo certbot renew

# Renew and restart service
sudo certbot renew --post-hook "systemctl restart zhineng-bridge"

# Renew all certificates and reload nginx
sudo certbot renew --post-hook "systemctl reload nginx"
```

### Automatic Renewal (Cron)

```bash
# Edit crontab
sudo crontab -e

# Add renewal job (runs twice daily)
0 0,12 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

### Self-Signed Certificates

```bash
# Regenerate with ssl_manager
python3 -c "
from relay_server.ssl_manager import generate_self_signed_cert
generate_self_signed_cert(force=True)
"

# Or with OpenSSL
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
```

### Commercial Certificates

Follow your CA's renewal process, typically:
1. Generate new CSR
2. Submit to CA
3. Download new certificate
4. Install and restart service

### Renewal Monitoring

```python
# monitor_certificates.py
import ssl
import socket
from datetime import datetime

def check_certificate_expiry(hostname, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            expiry = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            days_left = (expiry - datetime.now()).days
            return days_left

if __name__ == "__main__":
    days = check_certificate_expiry("api.yourdomain.com", 8765)
    if days < 30:
        print(f"⚠️  Certificate expires in {days} days!")
    else:
        print(f"✅ Certificate expires in {days} days")
```

## Security Checklist

- [ ] Using trusted CA certificates in production
- [ ] TLS 1.2+ enabled, older protocols disabled
- [ ] Strong cipher suites configured
- [ ] Private keys have restricted permissions (600)
- [ ] HSTS enabled with appropriate max-age
- [ ] Certificate expiry monitoring in place
- [ ] Automatic renewal configured for Let's Encrypt
- [ ] Reverse proxy configured for production
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] OCSP stapling enabled
- [ ] SSL session caching enabled
- [ ] Regular backups of certificates
- [ ] Certificate restoration process tested
- [ ] SSL/TLS errors monitored and logged

## Related Documentation

- [SSL Manager Documentation](relay-server/ssl_manager.py)
- [Configuration Guide](config.py)
- [Nginx WebSocket Guide](https://nginx.org/en/docs/http/websocket.html)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Mozilla SSL Config Generator](https://ssl-config.mozilla.org/)

---

**Last Updated:** 2026-03-25
**Version:** 1.0.0
