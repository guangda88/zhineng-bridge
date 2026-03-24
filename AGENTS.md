# AGENTS.md

Agent guide for working in the zhineng-bridge codebase.

## Project Overview

**zhineng-bridge** is a cross-platform real-time synchronization and communication SDK that connects multiple AI coding tools and IDEs.

### Key Information
- **Version:** 1.0.0 (as of 2026-03-24)
- **Languages:** Python 3.8+ (backend), JavaScript (frontend)
- **Architecture:** Client-server with WebSocket communication
- **License:** MIT

### Supported AI Tools
1. Crush (Charmbracelet)
2. Claude Code (Anthropic)
3. iFlow CLI (Alibaba)
4. Cursor (Anysphere)
5. Trae (ByteDance)
6. Droid (Factory)
7. OpenClaw
8. GitHub Copilot

## Essential Commands

### Starting the System

```bash
# Start the WebSocket relay server
cd relay-server
python3 start_server.py

# Start the Session Manager
cd phase1/session_manager
python3 start_manager.py

# Access the Web UI
# Open browser to: http://localhost:8000/web/ui/index.html
```

### Testing

```bash
# Run end-to-end tests (from project root)
python3 e2e_test.py

# Run unit tests (if available)
cd tests
pytest

# Current test status: Test directories exist (unit/, integration/, performance/) but appear empty
```

### WebSocket Connection
- **Default URL:** `ws://localhost:8765`
- **Host:** Configured via settings or defaults to `localhost`
- **Port:** Configurable via settings, defaults to 8765

## Project Structure

```
zhineng-bridge/
├── relay-server/              # WebSocket relay server
│   ├── server.py             # Main server implementation
│   ├── start_server.py       # Server entry point
│   └── chat_server.py        # Chat-specific server
├── phase1/                   # Phase 1: Session Management
│   └── session_manager/      # AI tool session management
│       ├── session_manager.py # SessionManager class
│       └── start_manager.py  # Manager entry point
├── phase3/                   # Phase 3: Security features
│   ├── encryption/           # End-to-end encryption
│   │   ├── encryption.js     # Web Crypto API wrapper
│   │   └── qrcode.js         # QR code generation
│   └── storage/              # IndexedDB offline storage
│       ├── storage.js        # StorageManager class
│       └── db_optimization.py # Database optimization
├── phase4/                   # Phase 4: Optimization & Release
│   ├── optimization/         # Performance optimization
│   │   ├── performance_optimization.js
│   │   ├── sw.js            # Service Worker
│   │   └── worker.js        # Web Worker
│   ├── security/             # Security hardening
│   │   └── security.js
│   └── monitoring/           # Performance monitoring
│       ├── dashboard.html
│       └── dashboard.js
├── web/ui/                   # Web frontend (main UI)
│   ├── index.html            # Main entry point
│   ├── css/                  # Stylesheets
│   │   ├── base.css          # Base styles, CSS variables
│   │   ├── components.css    # UI components
│   │   ├── layout.css        # Layout structure
│   │   ├── responsive.css    # Responsive design
│   │   └── mobile.css        # Mobile-specific styles
│   └── js/                   # JavaScript modules
│       ├── app.js            # Main application logic
│       ├── client.js         # WebSocket client
│       ├── tools.js          # Tool selection logic
│       ├── sessions.js       # Session management UI
│       ├── settings.js       # Settings management
│       ├── cache.js          # Caching logic
│       ├── preload.js        # Preloading strategy
│       ├── dynamic_imports.js # Dynamic module loading
│       ├── network_optimization.js # Network optimizations
│       └── webpack.config.js # Webpack configuration
├── optimization/              # Performance evaluation tools
│   ├── evaluator.py          # Parameter evaluation
│   └── variable.py           # Variable optimization
├── tests/                    # Test suites
│   ├── unit/                 # Unit tests (empty)
│   ├── integration/          # Integration tests (empty)
│   └── performance/          # Performance tests (empty)
├── docs/                     # Documentation
│   ├── README.md             # User documentation
│   ├── API.md                # API reference
│   └── CHANGELOG.md          # Change history
├── e2e_test.py              # End-to-end test suite
├── VERSION                  # Current version (1.0.0)
└── COMPREHENSIVE_DEVELOPMENT_PLAN.md  # Development roadmap
```

## Code Conventions

### Python (Backend)

**File Organization:**
- Use snake_case for filenames and functions: `session_manager.py`, `create_session()`
- Classes use PascalCase: `SessionManager`, `CrushRelayServer`
- Constants use UPPER_CASE: `MAX_CONNECTIONS`, `PING_INTERVAL`

**Type Hints:**
- Use type hints consistently for function signatures:
```python
def create_session(self, tool_name: str, args: List[str] = None) -> str:
    """Create a new session for the specified tool."""
```

**Docstrings:**
- Use Google-style or standard Python docstrings
- Include Args, Returns, and Raises sections

**Async/Await:**
- All WebSocket server code uses async/await with `asyncio`
- Use `asyncio.run(main())` for entry points

**Error Handling:**
```python
try:
    # Operation
except Exception as e:
    print(f"❌ Error description: {e}")
    # Handle or re-raise
```

### JavaScript (Frontend)

**File Organization:**
- Use camelCase for filenames and functions: `client.js`, `connectWebSocket()`
- Classes use PascalCase: `EncryptionManager`, `PerformanceOptimizer`
- Constants use UPPER_CASE or kebab-case for CSS variables

**Modern JavaScript:**
- Use ES6+ features (arrow functions, const/let, template literals)
- Use classes for modular components
- Export to window for global access when needed: `window.EncryptionManager = EncryptionManager`

**Logging Pattern:**
```javascript
console.log('✅ Success message');
console.warn('⚠️  Warning message');
console.error('❌ Error message');
```

**Event Handling:**
```javascript
// Use addEventListener consistently
element.addEventListener('click', (e) => {
    e.preventDefault();
    // Handler code
});
```

### CSS

**Organization:**
- Use CSS custom properties (variables) for theming
- BEM-like naming convention for classes: `.page-title`, `.btn-primary`
- Mobile-first responsive design

**Variables (defined in base.css):**
```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #48bb78;
    --danger-color: #f56565;
    /* ... more variables */
}
```

**Responsive Design:**
- Use media queries in `responsive.css` and `mobile.css`
- Breakpoints and mobile optimizations are handled in separate files

## Communication Patterns

### WebSocket Message Format

All WebSocket messages follow this JSON structure:

```json
{
  "type": "message_type",
  "data": { ... }
}
```

### Message Types (Client → Server)

**list_sessions**
```json
{
  "type": "list_sessions",
  "data": {}
}
```

**start_session**
```json
{
  "type": "start_session",
  "tool_name": "crush",
  "args": ["--help"]
}
```

**stop_session**
```json
{
  "type": "stop_session",
  "session_id": "xxx-xxx-xxx"
}
```

**delete_session**
```json
{
  "type": "delete_session",
  "session_id": "xxx-xxx-xxx"
}
```

**ping**
```json
{
  "type": "ping"
}
```

### Message Types (Server → Client)

**sessions_list**
```json
{
  "type": "sessions_list",
  "sessions": [...],
  "count": 0
}
```

**session_started**
```json
{
  "type": "session_started",
  "session_id": "xxx-xxx-xxx",
  "tool_name": "crush",
  "status": "running"
}
```

**session_stopped**
```json
{
  "type": "session_stopped",
  "session_id": "xxx-xxx-xxx",
  "status": "stopped"
}
```

**session_deleted**
```json
{
  "type": "session_deleted",
  "session_id": "xxx-xxx-xxx"
}
```

**output**
```json
{
  "type": "output",
  "session_id": "xxx-xxx-xxx",
  "output": "Output text...",
  "timestamp": "2026-03-24T02:00:00Z"
}
```

**pong**
```json
{
  "type": "pong",
  "timestamp": "2026-03-24T02:00:00Z"
}
```

**error**
```json
{
  "type": "error",
  "message": "Error description"
}
```

## Key Components

### SessionManager (Python)
Location: `phase1/session_manager/session_manager.py`

Manages AI tool sessions including:
- Tool registry (8 supported tools)
- Session creation and lifecycle management
- Session state tracking

Key methods:
- `list_tools()`: Returns available tools
- `create_session(tool_name, args)`: Creates new session
- `get_session(session_id)`: Retrieves session info
- `list_sessions()`: Lists all sessions

### CrushRelayServer (Python)
Location: `relay-server/server.py`

WebSocket relay server that:
- Handles client connections
- Routes messages to appropriate handlers
- Manages WebSocket lifecycle

Key methods:
- `start()`: Starts the server
- `handle_connection()`: Manages client connections
- `handle_message()`: Routes incoming messages

### WebSocket Client (JavaScript)
Location: `web/ui/js/client.js`

Client-side WebSocket management:
- Auto-reconnection logic
- Heartbeat/ping-pong mechanism
- Message sending and receiving

Key functions:
- `connectWebSocket()`: Establishes connection
- `sendMessage(message)`: Sends messages
- `handleMessage(data)`: Routes responses

### EncryptionManager (JavaScript)
Location: `phase3/encryption/encryption.js`

End-to-end encryption using Web Crypto API:
- RSA-OAEP for key exchange
- AES-GCM for message encryption
- Session key management

Key methods:
- `generateKeyPair()`: Creates RSA key pair
- `encryptMessage(message, publicKey)`: Encrypts with public key
- `decryptMessage(encryptedBase64)`: Decrypts with private key

### PerformanceOptimizer (JavaScript)
Location: `phase4/optimization/performance_optimization.js`

Performance monitoring and optimization:
- Tracks page load time, render time, memory, FPS
- Implements debouncing and throttling
- Web Worker and Service Worker integration

## Performance Targets

Current optimization goals:
- Session creation: < 50ms
- WebSocket connection: < 20ms
- Page load time: < 1s
- Memory usage: < 50MB

Current achieved metrics (from README):
- Session creation: < 100ms
- WebSocket connection: < 50ms
- Page load time: < 2s
- Memory usage: < 100MB

## Configuration

### WebSocket Configuration
The WebSocket client uses these settings (from `client.js`):
- `ws_host`: Server host (default: "localhost")
- `ws_port`: Server port (default: 8765)
- `auto_reconnect`: Auto-reconnect on disconnect (default: true)
- `reconnect_interval`: Reconnect delay in seconds (default: 5)
- `ping_interval`: Heartbeat interval in seconds (default: 10)

### Session Configuration
(from README):
- `max_sessions`: Maximum concurrent sessions (default: 100)
- `session_timeout`: Session timeout in seconds (default: 3600)
- `output_buffer_size`: Output buffer size (default: 100000)

## Development Workflow

### Adding a New AI Tool

1. **Backend (SessionManager)**:
   - Add tool entry to `self.tools` in `session_manager.py`
   - Include: name, description, executable path, icon, color

2. **Frontend (app.js)**:
   - Add tool to `TOOLS` array
   - Include: id, name, icon, description, status, color

3. **Test**:
   - Start session manager and relay server
   - Verify tool appears in Web UI
   - Test session creation and commands

### Adding WebSocket Message Type

1. **Server**:
   - Add handler in `handle_message()` method in `server.py`
   - Implement handler function (e.g., `handle_new_message_type()`)
   - Return appropriate JSON response

2. **Client**:
   - Add sender function in `client.js` if needed
   - Add handler in `handleMessage()` switch statement
   - Implement handler function (e.g., `handleNewMessageType()`)

3. **Update Documentation**:
   - Document in `docs/API.md`
   - Update this AGENTS.md if appropriate

### Frontend Page Development

1. Add page `<section>` to `web/ui/index.html`
2. Add navigation link in header/footer
3. Create JavaScript file in `web/ui/js/` or add to existing files
4. Script reference in `index.html` at bottom of body
5. Add styles in appropriate CSS file (`components.css` for reusable components)

## Important Gotchas

### WebSocket Connection
- The server binds to `0.0.0.0` but client connects to `localhost` by default
- Auto-reconnect is enabled with 5-second delay
- Heartbeat sends ping every 10 seconds

### Async/Await in Python
- All server operations must be async
- Use `async with websockets.connect()` for connections
- Server entry point must use `asyncio.run(main())`

### JavaScript Module Loading
- Scripts are loaded in order in `index.html`
- Some modules depend on others (e.g., `app.js` depends on `client.js`)
- Global state is managed via `window` object (e.g., `window.ws`, `window.APP_STATE`)

### CSS Specificity
- Base styles in `base.css` define CSS variables
- Component styles in `components.css`
- Layout in `layout.css`
- Responsive overrides in `responsive.css` and `mobile.css`
- Order matters: load stylesheets in HTML order

### Session IDs
- Use UUID for session IDs (both Python and JavaScript)
- Python: `str(uuid.uuid4())`
- JavaScript: Custom UUID generation or `crypto.randomUUID()`

### Error Handling
- Python: Use emoji prefixes in log messages (✅, ❌, ⚠️)
- JavaScript: Similar emoji pattern in console.log
- Always include descriptive error messages

### Testing Status
- **Important:** Test directories (`tests/unit/`, `tests/integration/`, `tests/performance/`) currently exist but are empty
- Only `e2e_test.py` at project root contains functional tests
- Test framework is `pytest` (referenced in README but needs verification)

### Performance Optimization
- Uses LingMinOpt framework for parameter optimization
- Current optimization parameters defined in `optimization/evaluator.py`
- Web Workers and Service Workers are integrated in phase4

## Documentation References

- **User Guide:** `docs/README.md`
- **API Reference:** `docs/API.md`
- **Change Log:** `docs/CHANGELOG.md`
- **Development Plan:** `COMPREHENSIVE_DEVELOPMENT_PLAN.md`
- **Release Notes:** `ZHINENGBRIDGE_V1.0.0_RELEASE.md`

## Dependencies

### Python
- `asyncio`: Standard library for async I/O
- `websockets`: WebSocket server implementation
- `json`: JSON encoding/decoding
- `uuid`: UUID generation
- `datetime`: Date/time handling

**Note:** No `requirements.txt` file found in the repository. Dependencies are from Python standard library except `websockets`.

### JavaScript
- **Browser APIs:**
  - WebSocket API
  - Web Crypto API
  - IndexedDB API
  - Service Worker API
  - Performance API
  - Worker API

**Note:** No `package.json` file found. Uses vanilla JavaScript with no external frameworks.

## Common Tasks

### Start Development Environment

```bash
# Terminal 1: Start relay server
cd relay-server
python3 start_server.py

# Terminal 2: Start session manager
cd phase1/session_manager
python3 start_manager.py

# Terminal 3: Run tests (optional)
python3 e2e_test.py

# Then open browser to http://localhost:8000/web/ui/index.html
```

### Debug WebSocket Issues

1. Check server is running on port 8765
2. Check browser console for WebSocket errors
3. Verify `client.js` settings match server configuration
4. Check auto-reconnect is working (5-second delay)
5. Monitor ping/pong messages in console

### Add New Feature

1. Determine if backend or frontend or both
2. Update relevant documentation (`docs/API.md`)
3. Add tests if applicable
4. Test thoroughly with both server and client running
5. Update this AGENTS.md if workflow or patterns change

### Performance Investigation

1. Check `phase4/monitoring/dashboard.js` for performance metrics
2. Review `phase4/optimization/performance_optimization.js` for optimization strategies
3. Check LingMinOpt parameters in `optimization/evaluator.py`
4. Run `e2e_test.py` for baseline performance
5. Use browser DevTools for frontend performance profiling

## Contact & Repository

- **GitHub:** https://github.com/guangda88/zhineng-bridge
- **Gitea:** http://zhinenggitea.iepose.cn/guangda/zhineng-bridge
- **License:** MIT

---

**Last Updated:** 2026-03-24
**Version:** 1.0.0
