# Technical Debt Resolution: Hardcoded Localhost Removal

## Overview
Successfully removed critical hardcoded "localhost" references from the codebase to enable flexible deployment configurations.

## Changes Made

### 1. Backend Configuration (relay-server/config.py)
- **Added**: `ws_host: str = "localhost"` to ServerSettings class
- **Environment variable**: `ZHINENG_BRIDGE_WS_HOST` now controls the WebSocket host that clients use to connect
- **Purpose**: Separates server bind address (0.0.0.0) from client-facing address (configurable)

### 2. Server Files Updated

#### relay-server/chat_server.py
- **Modified**: `__init__` method to use config defaults instead of hardcoded "localhost"
- **Imported**: settings from config module
- **Changed**: Default values to None, then fallback to settings.server.host/port
- **Updated**: main() function to use ChatRelayServer() without hardcoded parameters

#### relay-server/server.py:177
- **Modified**: Host display logic to use `settings.server.ws_host` instead of hardcoded "localhost"
- **Purpose**: Improves logging to show the actual client-facing hostname

#### relay-server/health_check.py:390-395
- **Modified**: Print statements to use `settings.server.ws_host` instead of hardcoded "localhost"
- **Impact**: Health check server now displays correct URLs in startup messages

### 3. Frontend Configuration

#### web/ui/index.html
- **Added**: Configuration script block before bundled JavaScript
- **Created**: `window.ZHINENG_BRIDGE_CONFIG` object with default settings
- **Implemented**: Dynamic loading of config/config.js if present
- **Purpose**: Allows production deployments to override defaults without code changes

#### web/ui/js/settings.ts
- **Modified**: All settings to read from `window.ZHINENG_BRIDGE_CONFIG` if available
- **Updated**: ws_host, ws_port, and other settings to use config object
- **Pattern**: `(typeof window !== 'undefined' && window.ZHINENG_BRIDGE_CONFIG?.WS_HOST) || 'localhost'`

### 4. Configuration Files

#### web/ui/config/config.js.example (NEW)
- **Created**: Example configuration file showing all available settings
- **Documented**: Each setting with clear descriptions
- **Usage**: Users can copy to config.js and customize for their deployment

#### .gitignore
- **Added**: `web/ui/config/config.js` to ignore list
- **Purpose**: Prevents committing deployment-specific configuration

#### .dockerignore
- **Added**: `web/ui/config/config.js` to ignore list
- **Purpose**: Prevents including deployment-specific config in Docker images

## Appropriate Uses of "localhost" (Not Changed)

The following "localhost" references remain unchanged as they are appropriate for their context:

1. **relay-server/ssl_manager.py**:
   - `common_name: str = "localhost"` in generate_self_signed_cert()
   - Default parameter for SSL certificate generation
   - Users can override with --common-name argument
   - Appropriate for local development

2. **relay-server/ssl_manager.py:384**:
   - `common_name="localhost"` in setup_development_certificates()
   - Specific to development environment setup
   - Appropriate use case

3. **examples/basic_usage.py**:
   - `host: str = "localhost"` in __init__
   - Example code default
   - Can be overridden when creating client
   - Appropriate for out-of-the-box examples

## Environment Variables

### New Configuration Variables
- `ZHINENG_BRIDGE_WS_HOST`: WebSocket host address for client connections (default: localhost)
- `ZHINENG_BRIDGE_SERVER_PORT`: Server port (already existed, default: 8765)

### Usage Examples

#### Development (default)
```bash
python3 relay-server/start_server.py
# Server binds to 0.0.0.0:8765, clients use ws://localhost:8765
```

#### Production with custom host
```bash
export ZHINENG_BRIDGE_WS_HOST=prod-server.example.com
python3 relay-server/start_server.py
# Server binds to 0.0.0.0:8765, clients use ws://prod-server.example.com:8765
```

#### Frontend configuration
```javascript
// In web/ui/config/config.js
window.ZHINENG_BRIDGE_CONFIG = {
    WS_HOST: 'prod-server.example.com',
    WS_PORT: 8765,
    // ... other settings
};
```

## Testing

### Configuration Loading Tests
✅ Default configuration loads correctly:
- Server host (bind): 0.0.0.0
- Server ws_host (client): localhost
- Server port: 8765

✅ Environment variable override works:
- Server host (bind): 0.0.0.0
- Server ws_host (client): prod-server.example.com (overridden)
- Server port: 8765

### Docker Build Test
✅ Docker build completed successfully (14/14 steps)
- All layers built without errors
- Image: test-zhineng-bridge:latest

## Benefits

1. **Flexibility**: Deploy to different environments without code changes
2. **Security**: No hardcoded URLs in production builds
3. **Maintainability**: Single source of truth for configuration
4. **Development Experience**: Works out-of-the-box with sensible defaults
5. **Production Ready**: Easy to override for production deployments

## Migration Guide

For existing deployments:

1. **No immediate action required**: Defaults remain "localhost" for backward compatibility
2. **For production**: Set `ZHINENG_BRIDGE_WS_HOST` environment variable
3. **For web UI**: Create `web/ui/config/config.js` with production settings
4. **Update documentation**: Document the new configuration options

## Future Enhancements

Potential improvements for future iterations:
1. Add configuration validation to catch typos
2. Add a `/config` endpoint to retrieve current configuration
3. Implement hot-reload for configuration changes
4. Add configuration documentation to API docs
5. Consider using a configuration file format (YAML/TOML) for complex deployments

## Files Modified

- `relay-server/config.py` - Added ws_host setting
- `relay-server/server.py` - Updated host display logic
- `relay-server/chat_server.py` - Updated to use config
- `relay-server/health_check.py` - Updated print statements
- `web/ui/index.html` - Added configuration script
- `web/ui/js/settings.ts` - Updated to read from config object
- `.gitignore` - Added config/config.js
- `.dockerignore` - Added config/config.js

## Files Created

- `web/ui/config/config.js.example` - Example configuration file

---

**Date**: 2026-03-25
**Status**: Completed ✅
**Next Steps**: Update documentation to reflect new configuration options
