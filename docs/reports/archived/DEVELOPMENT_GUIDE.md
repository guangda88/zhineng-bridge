# Development Guide

## Adding a New AI Tool

### Backend (SessionManager)
1. Add tool entry to `self.tools` in `session_manager.py`
2. Include: name, description, executable path, icon, color

### Frontend (app.js)
1. Add tool to `TOOLS` array
2. Include: id, name, icon, description, status, color

### Test
1. Start session manager and relay server
2. Verify tool appears in Web UI
3. Test session creation and commands

## Adding WebSocket Message Type

### Server
1. Add handler in `handle_message()` method in `server.py`
2. Implement handler function
3. Return appropriate JSON response

### Client
1. Add sender function in `client.js` if needed
2. Add handler in `handleMessage()` switch statement
3. Update `docs/API.md`

## Frontend Page Development

1. Add page `<section>` to `web/ui/index.html`
2. Add navigation link in header/footer
3. Create JavaScript file in `web/ui/js/` or add to existing files
4. Script reference in `index.html` at bottom of body
5. Add styles in appropriate CSS file (`components.css` for reusable components)

## Start Development Environment

```bash
# Terminal 1: Start relay server
cd relay-server && python3 start_server.py

# Terminal 2: Start session manager
cd phase1/session_manager && python3 start_manager.py

# Terminal 3: Run tests (optional)
python3 e2e_test.py

# Open browser: http://localhost:8000/web/ui/index.html
```

## Debug WebSocket Issues

1. Check server running on port 8765
2. Check browser console for WebSocket errors
3. Verify `client.js` settings match server config
4. Check auto-reconnect (5-second delay)
5. Monitor ping/pong in console

## Performance Investigation

1. Check `phase4/monitoring/dashboard.js` for metrics
2. Review `phase4/optimization/performance_optimization.js`
3. Check lingminopt parameters in `optimization/evaluator.py`
4. Run `e2e_test.py` for baseline
5. Use browser DevTools for frontend profiling
