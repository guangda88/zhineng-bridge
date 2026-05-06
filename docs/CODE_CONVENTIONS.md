# Code Conventions

## Python (Backend)

### File Organization
- snake_case for filenames and functions: `session_manager.py`, `create_session()`
- PascalCase for classes: `SessionManager`, `CrushRelayServer`
- UPPER_CASE for constants: `MAX_CONNECTIONS`, `PING_INTERVAL`

### Type Hints
Use type hints consistently for function signatures:
```python
def create_session(self, tool_name: str, args: List[str] = None) -> str:
    """Create a new session for the specified tool."""
```

### Docstrings
Use Google-style or standard Python docstrings. Include Args, Returns, and Raises sections.

### Async/Await
All WebSocket server code uses async/await with `asyncio`. Use `asyncio.run(main())` for entry points.

### Error Handling
```python
try:
    # Operation
except Exception as e:
    print(f"Error: {e}")
```

## JavaScript (Frontend)

### File Organization
- camelCase for filenames and functions: `client.js`, `connectWebSocket()`
- PascalCase for classes: `EncryptionManager`, `PerformanceOptimizer`
- UPPER_CASE or kebab-case for constants/CSS variables

### Modern JavaScript
Use ES6+ features (arrow functions, const/let, template literals). Use classes for modular components. Export to `window` for global access when needed.

### Event Handling
```javascript
element.addEventListener('click', (e) => {
    e.preventDefault();
});
```

## CSS

- CSS custom properties (variables) for theming, defined in `base.css`
- BEM-like naming: `.page-title`, `.btn-primary`
- Mobile-first responsive design
- Load order matters: `base.css` → `components.css` → `layout.css` → `responsive.css` → `mobile.css`

## Session IDs
Use UUID for session IDs. Python: `str(uuid.uuid4())`, JavaScript: `crypto.randomUUID()`.

## Error Logging
Python and JavaScript both use emoji prefixes: success, warning, error. Always include descriptive messages.
