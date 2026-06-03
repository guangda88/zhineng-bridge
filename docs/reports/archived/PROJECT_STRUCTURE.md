# Project Structure

```
zhineng-bridge/
├── relay-server/              # WebSocket relay server
│   ├── server.py             # Main server implementation
│   ├── start_server.py       # Server entry point
│   └── chat_server.py        # Chat-specific server
├── session_protocol/          # Session protocol with auth (Layer 1 hardening)
│   ├── manager.py            # FamilySessionManager with caller_id auth
│   ├── auth.py               # AuthorizationManager (default-deny + explicit-allow)
│   ├── __init__.py            # Exports
│   └── ...
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
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── performance/          # Performance tests
│   └── e2e/                  # E2E tests
├── docs/                     # Documentation
│   ├── README.md             # User documentation
│   ├── API.md                # API reference (WebSocket + internal APIs)
│   ├── PROJECT_STRUCTURE.md  # This file
│   ├── CODE_CONVENTIONS.md   # Code style guide
│   ├── DEVELOPMENT_GUIDE.md  # Development workflows
│   └── CHANGELOG.md          # Change history
├── e2e_test.py              # End-to-end test suite
├── WAKE_UP.md               # 6-step startup verification ritual
├── VERSION                  # Current version (1.0.0)
└── COMPREHENSIVE_DEVELOPMENT_PLAN.md  # Development roadmap
```
