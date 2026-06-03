# Error Handling Documentation

## Overview

Zhineng-bridge uses a comprehensive error handling system with custom exception classes and structured error responses.

## Architecture

### Exception Hierarchy

All exceptions inherit from `ZhinengBridgeException`, which provides:
- Consistent error messages
- HTTP-style error codes
- Detailed error context in `details` field
- `to_dict()` method for JSON serialization

```
ZhinengBridgeException
├── ValidationError
│   ├── InvalidMessageTypeError
│   ├── InvalidToolNameError
│   ├── InvalidSessionIdError
│   ├── InvalidJSONError
│   └── MissingFieldError
├── AuthenticationError
├── AuthorizationError
├── RateLimitError
├── SessionNotFoundError
├── SessionAlreadyRunningError
├── MaxConnectionsError
├── MaxSessionsError
├── ServerException
│   ├── SessionManagerError
│   ├── ToolExecutionError
│   ├── ConnectionError
│   └── TimeoutError
└── ConfigurationError
```

### Error Response Format

All errors follow this consistent structure:

```json
{
  "type": "error",
  "message": "Human-readable error message",
  "code": 400,
  "field_name": "value",  // Optional: additional context
  ...
}
```

## Exception Classes

### Validation Errors (4xx)

#### `InvalidMessageTypeError`
- **Code**: 400
- **Usage**: Unknown message type from client
- **Example**:
  ```python
  raise InvalidMessageTypeError("unknown_type")
  # Response: {"type": "error", "message": "Unknown message type: unknown_type", "code": 400, "message_type": "unknown_type"}
  ```

#### `InvalidToolNameError`
- **Code**: 400
- **Usage**: Invalid AI tool name
- **Example**:
  ```python
  raise InvalidToolNameError("invalid_tool", ["crush", "claude", "cursor"])
  ```

#### `InvalidSessionIdError`
- **Code**: 400
- **Usage**: Invalid session ID format
- **Example**:
  ```python
  raise InvalidSessionIdError("invalid-uuid")
  ```

#### `InvalidJSONError`
- **Code**: 400
- **Usage**: Malformed JSON in message
- **Example**:
  ```python
  raise InvalidJSONError("Unexpected character")
  ```

#### `MissingFieldError`
- **Code**: 400
- **Usage**: Required field missing
- **Example**:
  ```python
  raise MissingFieldError("session_id")
  ```

### Authentication/Authorization Errors (4xx)

#### `AuthenticationError`
- **Code**: 401
- **Usage**: Authentication failed
- **Example**:
  ```python
  raise AuthenticationError("Invalid token")
  ```

#### `AuthorizationError`
- **Code**: 403
- **Usage**: User not authorized for action
- **Example**:
  ```python
  raise AuthorizationError("Admin privileges required")
  ```

#### `RateLimitError`
- **Code**: 429
- **Usage**: Rate limit exceeded
- **Example**:
  ```python
  raise RateLimitError(limit=100)
  ```

### Resource Errors (4xx/5xx)

#### `SessionNotFoundError`
- **Code**: 404
- **Usage**: Session not found
- **Example**:
  ```python
  raise SessionNotFoundError("abc-123-def")
  ```

#### `SessionAlreadyRunningError`
- **Code**: 409
- **Usage**: Attempt to start already running session
- **Example**:
  ```python
  raise SessionAlreadyRunningError("abc-123-def")
  ```

#### `MaxConnectionsError`
- **Code**: 429
- **Usage**: Maximum connections exceeded
- **Example**:
  ```python
  raise MaxConnectionsError(current=101, max_connections=100)
  ```

#### `MaxSessionsError`
- **Code**: 429
- **Usage**: Maximum sessions exceeded
- **Example**:
  ```python
  raise MaxSessionsError(current=51, max_sessions=50)
  ```

### Server Errors (5xx)

#### `ServerException`
- **Code**: 500
- **Usage**: Generic server error
- **Example**:
  ```python
  raise ServerException("Internal error", details={"context": "additional info"})
  ```

#### `SessionManagerError`
- **Code**: 500
- **Usage**: Session manager error
- **Example**:
  ```python
  raise SessionManagerError("Failed to manage session")
  ```

#### `ToolExecutionError`
- **Code**: 500
- **Usage**: AI tool execution failed
- **Example**:
  ```python
  raise ToolExecutionError(tool_name="crush", error="Command failed", exit_code=1)
  ```

#### `ConnectionError`
- **Code**: 503
- **Usage**: Connection error
- **Example**:
  ```python
  raise ConnectionError("Failed to connect to service")
  ```

#### `TimeoutError`
- **Code**: 504
- **Usage**: Operation timeout
- **Example**:
  ```python
  raise TimeoutError(operation="create_session", timeout=30)
  ```

### Configuration Errors (5xx)

#### `ConfigurationError`
- **Code**: 500
- **Usage**: Invalid configuration
- **Example**:
  ```python
  raise ConfigurationError("Invalid port", config_key="server.port")
  ```

## Usage Patterns

### Raising Exceptions

```python
from exceptions import InvalidToolNameError, SessionNotFoundError

def create_session(tool_name: str):
    if tool_name not in VALID_TOOLS:
        raise InvalidToolNameError(tool_name, list(VALID_TOOLS))
    # ... session creation logic
```

### Catching Exceptions in Server

```python
from exceptions import (
    InvalidToolNameError,
    SessionNotFoundError,
    SessionManagerError,
    exception_to_dict
)

async def handle_start_session(self, message):
    try:
        session_id = self.manager.create_session(tool_name, args)
        return SessionStartedResponse(...).model_dump()
    except (InvalidToolNameError, SessionManagerError) as e:
        track_error("session_creation_error", "error")
        self.logger.error("Failed to create session", error=str(e), exc_info=True)
        return e.to_dict()
```

### Converting Generic Exceptions

```python
from exceptions import exception_to_dict

try:
    # Some operation that might raise generic exceptions
    result = perform_operation()
except Exception as e:
    error_dict = exception_to_dict(e)
    # error_dict is now in the standard format
    await send_error_to_client(error_dict)
```

## Error Handling in Session Manager

The Session Manager has been updated to use custom exceptions:

```python
# Before:
raise ValueError(f"工具不存在: {tool_name}")

# After:
raise InvalidToolNameError(tool_name, list(self.tools.keys()))

# Before:
raise ValueError(f"会话不存在: {session_id}")

# After:
raise SessionNotFoundError(session_id)
```

### Session Manager Methods

| Method | Raises | Description |
|--------|--------|-------------|
| `create_session()` | `InvalidToolNameError` | Tool not in registry |
| `stop_session()` | `SessionNotFoundError`, `ToolExecutionError` | Session not found or process failed |
| `delete_session()` | `SessionNotFoundError`, `ToolExecutionError` | Session not found or stop failed |
| `set_active_session()` | `SessionNotFoundError` | Session not found |

## Error Handling in WebSocket Server

The WebSocket server handles exceptions at multiple levels:

### Connection Level
```python
async def handle_connection(self, websocket):
    try:
        # Authentication
        await authenticate_connection(websocket)
        # Message loop
        async for message in websocket:
            await self.handle_message(client_id, message)
    except websockets.exceptions.ConnectionClosed:
        self.logger.info("Client disconnected")
    except Exception as e:
        self.logger.error("Connection handling error", exc_info=True)
```

### Message Level
```python
async def handle_message(self, client_id, message):
    try:
        validated_message = validate_message(message)
        response = await self.route_message(validated_message)
        await self.send_to_client(client_id, response)
    except json.JSONDecodeError as e:
        error = InvalidJSONError(str(e))
        await self.send_error_dict(client_id, error.to_dict())
    except ValueError as e:
        error = ValidationError(str(e))
        await self.send_error_dict(client_id, error.to_dict())
    except Exception as e:
        await self.send_error_dict(client_id, exception_to_dict(e))
```

### Handler Level
```python
async def handle_start_session(self, message):
    try:
        session_id = self.manager.create_session(tool_name, args)
        return SessionStartedResponse(...).model_dump()
    except (InvalidToolNameError, SessionManagerError) as e:
        track_error("session_creation_error", "error")
        self.logger.error("Failed to create session", error=str(e), exc_info=True)
        return e.to_dict()
```

## Error Metrics

All errors are tracked using Prometheus metrics:

```python
from metrics import track_error

track_error("session_creation_error", "error")
track_error("json_decode_error", "error")
track_error("validation_error", "error")
```

## Error Code Reference

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request from client |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | User not authorized for action |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., already running) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |
| 504 | Gateway Timeout | Operation timeout |

## Best Practices

1. **Use specific exceptions**: Always use the most specific exception class
2. **Include context**: Add relevant details in the `details` field
3. **Log errors**: Always log errors with context and stack trace
4. **Track metrics**: Use `track_error()` for monitoring
5. **Return consistent format**: All errors should return `to_dict()` result
6. **Don't expose sensitive info**: Error messages should be user-friendly, not expose internals

## Testing Error Handling

### Testing Exception Raising
```python
import pytest
from exceptions import InvalidToolNameError

def test_invalid_tool_name():
    with pytest.raises(InvalidToolNameError) as exc_info:
        # Code that raises InvalidToolNameError
        pass
    assert exc_info.value.code == 400
```

### Testing Error Response
```python
async def test_invalid_tool_name_response():
    error = InvalidToolNameError("invalid", ["crush", "claude"])
    response = error.to_dict()
    assert response["type"] == "error"
    assert response["code"] == 400
    assert "tool_name" in response
```

## Migration Guide

If you're updating code that uses generic exceptions:

### Before
```python
try:
    session_id = manager.create_session(tool_name)
except ValueError as e:
    return {"type": "error", "message": str(e), "code": 400}
```

### After
```python
try:
    session_id = manager.create_session(tool_name)
except InvalidToolNameError as e:
    track_error("invalid_tool", "error")
    return e.to_dict()
```

## Future Enhancements

Potential improvements to the error handling system:

1. **Error categories**: Group related errors for better organization
2. **Internationalization**: Support for multiple languages in error messages
3. **Error recovery**: Automatic retry logic for transient errors
4. **Error aggregations**: Group related errors for analysis
5. **Custom error handlers**: Allow clients to register custom error handlers

## Related Files

- `relay-server/exceptions.py`: Exception definitions
- `relay-server/server.py`: WebSocket server error handling
- `phase1/session_manager/session_manager.py`: Session manager error handling
- `relay-server/metrics.py`: Error tracking metrics
- `relay-server/logger.py`: Error logging

---

**Last Updated**: 2026-03-25
**Version**: 1.0.0
