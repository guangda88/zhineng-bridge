# Authentication System Guide

## Overview

zhineng-bridge provides a comprehensive authentication and authorization system that supports multiple authentication methods:

- **Username/Password** - Traditional username and password authentication
- **JWT (JSON Web Tokens)** - Stateless token-based authentication
- **OAuth2** - Third-party authentication via GitHub and Google

## Architecture

### Components

1. **UserDatabase** - SQLite database for user storage (migratable to PostgreSQL)
2. **PasswordHasher** - PBKDF2-HMAC-SHA256 password hashing
3. **JWTAuth** - JWT token generation and validation
4. **AuthenticationManager** - Main authentication and session management
5. **HTTPServer** - REST API for user management and OAuth2 callbacks
6. **WebSocketAuth** - WebSocket connection authentication

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    permissions TEXT DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    oauth_provider TEXT,
    oauth_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OAuth2 tokens table
CREATE TABLE oauth_tokens (
    token_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Sessions table
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
```

## Configuration

### Environment Variables

Enable and configure authentication using environment variables:

```bash
# Enable authentication
ZHINENG_BRIDGE_SECURITY_ENABLE_AUTH=true

# Set secret key (REQUIRED for production)
ZHINENG_BRIDGE_SECURITY_SECRET_KEY=your-secret-key-here

# Enable HTTP server (required for OAuth2)
ZHINENG_BRIDGE_MONITORING_ENABLE_HTTP_SERVER=true

# HTTP server port
ZHINENG_BRIDGE_MONITORING_HTTP_PORT=8000

# GitHub OAuth2 (optional)
ZHINENG_BRIDGE_SECURITY_GITHUB_OAUTH_CLIENT_ID=your-github-client-id
ZHINENG_BRIDGE_SECURITY_GITHUB_OAUTH_CLIENT_SECRET=your-github-client-secret

# Google OAuth2 (optional)
ZHINENG_BRIDGE_SECURITY_GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
ZHINENG_BRIDGE_SECURITY_GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
```

## Quick Start

### 1. Initialize Database

Run the initialization script to create the database and default admin user:

```bash
python3 scripts/init_auth_db.py
```

This creates:
- SQLite database file: `zhineng-bridge.db`
- Default admin user:
  - Username: `admin`
  - Password: `admin123`
  - Email: `admin@zhineng-bridge.local`
  - Role: `admin`

**⚠️ Important:** Change the default admin password immediately after first login!

### 2. Start the Server

```bash
cd relay-server
python3 start_server.py
```

The server will now:
- Start WebSocket server on port 8765 (or configured port)
- Start HTTP server on port 8000 (if enabled)
- Initialize authentication database
- Create default admin user if not exists

## Authentication Methods

### Method 1: Username/Password + JWT

#### Step 1: Register a User

```bash
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepassword123",
    "email": "test@example.com"
  }'
```

**注意**: `test@example.com` 是示例邮箱，实际部署时请使用有效的邮箱地址。
```

Response:
```json
{
  "type": "success",
  "message": "User registered successfully",
  "user": {
    "user_id": "abc-123-def",
    "username": "testuser",
    "email": "test@example.com",
    "role": "user",
    "permissions": ["read", "write"]
  }
}
```

**注意**: `test@example.com` 是示例邮箱，实际部署时请使用有效的邮箱地址。
```

#### Step 2: Login

```bash
curl -X POST http://localhost:8000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Response:
```json
{
  "type": "success",
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_info": {
    "user_id": "2cbd746c-5758-491d-a162-0f23bf0725fe",
    "username": "admin",
    "created_at": "2026-03-25T12:39:25Z",
    "expires_at": "2026-03-26T12:39:25Z",
    "scopes": ["read", "write", "admin", "manage_users", "manage_sessions"]
  }
}
```

#### Step 3: Authenticate WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
  // Send authentication message
  ws.send(JSON.stringify({
    type: 'authenticate',
    token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'auth_success') {
    console.log('Authentication successful!');
    console.log('User ID:', data.user_id);
    console.log('Username:', data.username);
  }
};
```

### Method 2: OAuth2 (GitHub)

#### Step 1: Configure GitHub OAuth2

1. Go to GitHub Developer Settings: https://github.com/settings/developers
2. Click "New OAuth App"
3. Fill in:
   - Application name: `zhineng-bridge`
   - Homepage URL: `http://localhost:8000`
   - Authorization callback URL: `http://localhost:8000/auth/github/callback`
4. Copy Client ID and Client Secret
5. Add to `.env`:
   ```bash
   ZHINENG_BRIDGE_SECURITY_GITHUB_OAUTH_CLIENT_ID=your-client-id
   ZHINENG_BRIDGE_SECURITY_GITHUB_OAUTH_CLIENT_SECRET=your-client-secret
   ```

#### Step 2: Initiate OAuth2 Flow

Open browser to: `http://localhost:8000/auth/github`

This will redirect to GitHub's authorization page.

#### Step 3: Authorize Application

After authorizing, GitHub will redirect back to the callback URL with an authorization code.

The server will:
1. Exchange authorization code for access token
2. Get user info from GitHub
3. Create or link user account
4. Generate JWT token
5. Return success page with token

### Method 3: OAuth2 (Google)

#### Step 1: Configure Google OAuth2

1. Go to Google Cloud Console: https://console.cloud.google.com
2. Create new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
5. Copy Client ID and Client Secret
6. Add to `.env`:
   ```bash
   ZHINENG_BRIDGE_SECURITY_GOOGLE_OAUTH_CLIENT_ID=your-client-id
   ZHINENG_BRIDGE_SECURITY_GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   ```

#### Step 2: Initiate OAuth2 Flow

Open browser to: `http://localhost:8000/auth/google`

This will redirect to Google's authorization page.

#### Step 3: Authorize Application

After authorizing, Google will redirect back to the callback URL with an authorization code.

The server will:
1. Exchange authorization code for access token
2. Get user info from Google
3. Create or link user account
4. Generate JWT token
5. Return success page with token

## User Roles and Permissions

### Roles

| Role | Description |
|------|-------------|
| USER | Standard user with basic permissions |
| MODERATOR | User with moderation privileges |
| ADMIN | Full administrative access |

### Permissions

| Permission | Description |
|------------|-------------|
| read | Read data and view sessions |
| write | Create and modify sessions |
| admin | Administrative operations |
| manage_users | User management (CRUD operations) |
| manage_sessions | Session management (start, stop, delete sessions) |

### Permission Mapping

| Role | Permissions |
|------|-------------|
| USER | read, write |
| MODERATOR | read, write, manage_sessions |
| ADMIN | read, write, admin, manage_users, manage_sessions |

## REST API

### User Registration

**Endpoint:** `POST /api/users/register`

**Request:**
```json
{
  "username": "testuser",
  "password": "securepassword123",
  "email": "test@example.com"
}
```

**Response (200 OK):**
```json
{
  "type": "success",
  "message": "User registered successfully",
  "user": {
    "user_id": "abc-123-def",
    "username": "testuser",
    "email": "test@example.com",
    "role": "user",
    "permissions": ["read", "write"]
  }
}
```

### User Login

**Endpoint:** `POST /api/users/login`

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "type": "success",
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_info": {
    "user_id": "2cbd746c-5758-491d-a162-0f23bf0725fe",
    "username": "admin",
    "created_at": "2026-03-25T12:39:25Z",
    "expires_at": "2026-03-26T12:39:25Z",
    "scopes": ["read", "write", "admin", "manage_users", "manage_sessions"]
  }
}
```

### User Logout

**Endpoint:** `POST /api/users/logout`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "type": "success",
  "message": "Logout successful"
}
```

### Get Current User

**Endpoint:** `GET /api/users/me`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "type": "success",
  "user": {
    "user_id": "2cbd746c-5758-491d-a162-0f23bf0725fe",
    "username": "admin",
    "email": "admin@zhineng-bridge.local",
    "role": "admin",
    "permissions": ["read", "write", "admin", "manage_users", "manage_sessions"],
    "is_active": true,
    "created_at": "2026-03-25T12:39:12Z",
    "updated_at": "2026-03-25T12:39:12Z"
  }
}
```

### Update User

**Endpoint:** `PUT /api/users/{user_id}`

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "email": "newemail@example.com",
  "role": "moderator"
}
```

**Response (200 OK):**
```json
{
  "type": "success",
  "message": "User updated successfully"
}
```

### Delete User

**Endpoint:** `DELETE /api/users/{user_id}`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "type": "success",
  "message": "User deleted successfully"
}
```

### List Users (Admin Only)

**Endpoint:** `GET /api/users`

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `limit`: Number of users to return (default: 100)
- `offset`: Offset for pagination (default: 0)

**Response (200 OK):**
```json
{
  "type": "success",
  "users": [
    {
      "user_id": "2cbd746c-5758-491d-a162-0f23bf0725fe",
      "username": "admin",
      "email": "admin@zhineng-bridge.local",
      "role": "admin",
      "permissions": ["read", "write", "admin", "manage_users", "manage_sessions"],
      "is_active": true,
      "created_at": "2026-03-25T12:39:12Z",
      "updated_at": "2026-03-25T12:39:12Z"
    }
  ],
  "count": 1
}
```

## WebSocket Protocol

### Authentication Message

**Client → Server:**
```json
{
  "type": "authenticate",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Server → Client (Success):**
```json
{
  "type": "auth_success",
  "message": "Authentication successful",
  "user_id": "2cbd746c-5758-491d-a162-0f23bf0725fe",
  "username": "admin"
}
```

**Server → Client (Error):**
```json
{
  "type": "error",
  "message": "Authentication failed: invalid or expired token",
  "code": 401
}
```

## Security Best Practices

### 1. Use Strong Secret Keys

Generate a secure secret key for production:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Set in `.env`:
```bash
ZHINENG_BRIDGE_SECURITY_SECRET_KEY=your-64-character-hex-string
```

### 2. Change Default Passwords

Immediately change the default admin password:

```bash
# Via HTTP API
curl -X PUT http://localhost:8000/api/users/2cbd746c-5758-491d-a162-0f23bf0725fe \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"password": "new-secure-password"}'
```

### 3. Use HTTPS in Production

- Use WSS (WebSocket Secure) for WebSocket connections
- Configure TLS/SSL certificates
- See [WSS_TLS_SETUP.md](./WSS_TLS_SETUP.md) for details

### 4. Implement Rate Limiting

Rate limiting is enabled by default. Configure in `.env`:

```bash
# Enable rate limiting
ZHINENG_BRIDGE_SECURITY_ENABLE_RATE_LIMIT=true

# Requests per minute
ZHINENG_BRIDGE_SECURITY_RATE_LIMIT_PER_MINUTE=60

# Requests per hour
ZHINENG_BRIDGE_SECURITY_RATE_LIMIT_PER_HOUR=1000
```

### 5. Regular Session Cleanup

The system automatically cleans up expired sessions every hour. Ensure the server runs continuously for cleanup to work.

### 6. Secure OAuth2 Credentials

- Never commit OAuth2 client secrets to version control
- Use environment variables or secure secrets management
- Rotate OAuth2 credentials regularly
- Monitor for suspicious OAuth2 activity

### 7. Use IP Whitelisting (Optional)

Restrict access to specific IP addresses:

```bash
# Allow only specific IPs (comma-separated)
ZHINENG_BRIDGE_SECURITY_ALLOWED_IPS=192.168.1.100,10.0.0.50

# Block specific IPs (comma-separated)
ZHINENG_BRIDGE_SECURITY_BLOCKED_IPS=1.2.3.4,5.6.7.8
```

## Troubleshooting

### Issue: "Authentication failed: invalid or expired token"

**Possible causes:**
1. Token has expired (default: 24 hours)
2. Token was revoked (user logged out)
3. Token was tampered with
4. Secret key mismatch

**Solutions:**
1. Re-login to get a fresh token
2. Check token expiration time in token_info
3. Verify secret key is consistent
4. Ensure JWT signing algorithm is HS256

### Issue: "User not found"

**Possible causes:**
1. User was deleted
2. Database was reset
3. Wrong username/email

**Solutions:**
1. Check user exists in database
2. Re-register user if needed
3. Verify username/email is correct

### Issue: OAuth2 callback fails

**Possible causes:**
1. OAuth2 client credentials are incorrect
2. Callback URL doesn't match configuration
3. OAuth2 provider API is down
4. State parameter mismatch

**Solutions:**
1. Verify client ID and secret in `.env`
2. Check callback URL in OAuth2 app settings
3. Check OAuth2 provider status
4. Ensure state parameter is properly generated

### Issue: Database initialization fails

**Possible causes:**
1. Database file permissions
2. SQLite lock (database already in use)
3. Disk full

**Solutions:**
1. Check file permissions: `ls -la zhineng-bridge.db`
2. Kill other processes using database
3. Check disk space: `df -h`

## Examples

### Complete WebSocket Authentication Flow

```javascript
class AuthenticatedWebSocket {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.token = null;
  }

  async authenticate(username, password) {
    // Step 1: Get JWT token via HTTP API
    const response = await fetch('http://localhost:8000/api/users/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();
    if (data.type === 'success') {
      this.token = data.token;
      return true;
    }

    return false;
  }

  connect() {
    if (!this.token) {
      throw new Error('Not authenticated');
    }

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');

      // Step 2: Send authentication message
      this.ws.send(JSON.stringify({
        type: 'authenticate',
        token: this.token
      }));
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'auth_success') {
        console.log('Authentication successful!');
        console.log('User ID:', data.user_id);
        console.log('Username:', data.username);
      } else {
        console.log('Received:', data);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
  }

  send(type, data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }));
    }
  }
}

// Usage
const client = new AuthenticatedWebSocket('ws://localhost:8765');

// Authenticate and connect
await client.authenticate('admin', 'admin123');
client.connect();

// Send authenticated message
client.send('list_sessions', {});
```

## Advanced Topics

### Custom Permission Checks

Implement custom permission checks in your application:

```python
from user_auth import auth_manager, Permission

def check_permission(user_id: str, required_permission: Permission) -> bool:
    """Check if user has required permission"""
    user = auth_manager.db.get_user(user_id=user_id)

    if not user or not user.is_active:
        return False

    if required_permission.value in user.permissions:
        return True

    # Admin role has all permissions
    if user.role.value == 'admin':
        return True

    return False
```

### Database Migration to PostgreSQL

For production deployments, consider migrating to PostgreSQL:

```python
# In config.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# PostgreSQL connection string
DATABASE_URL = "postgresql://user:password@localhost/zhineng_bridge"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```

### Multi-Server Deployment

For horizontal scaling, use Redis for session storage:

```python
import redis

# In user_auth.py
class RedisSessionManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    def store_session(self, token: str, token_info: dict, expires_in: int = 86400):
        """Store session in Redis with expiration"""
        self.redis.setex(
            f"session:{token}",
            expires_in,
            json.dumps(token_info)
        )

    def get_session(self, token: str) -> Optional[dict]:
        """Get session from Redis"""
        data = self.redis.get(f"session:{token}")
        if data:
            return json.loads(data)
        return None
```

## API Reference

See [API.md](./API.md) for complete API documentation.

## Support

For issues or questions:
- GitHub Issues: https://github.com/guangda88/zhineng-bridge/issues
- Documentation: https://github.com/guangda88/zhineng-bridge/docs

---

**Version:** 1.0.0
**Last Updated:** 2026-03-25
