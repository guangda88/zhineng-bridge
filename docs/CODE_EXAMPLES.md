# Zhineng-bridge API Code Examples

This document provides code examples in various programming languages for using the Zhineng-bridge WebSocket API.

## Table of Contents

- [JavaScript/TypeScript](#javascripttypescript)
- [Python](#python)
- [Go](#go)
- [Java](#java)
- [C#](#c)
- [Rust](#rust)

---

## JavaScript/TypeScript

### Basic WebSocket Connection

```javascript
// Basic connection
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    console.log('Connected to Zhineng-bridge');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('Disconnected from Zhineng-bridge');
};
```

### With Authentication

```javascript
const ws = new WebSocket('wss://your-domain.com:8765');

ws.onopen = () => {
    // Send authentication as first message
    const authMessage = {
        type: 'authenticate',
        token: 'your-jwt-token-here'
    };
    ws.send(JSON.stringify(authMessage));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'auth_success') {
        console.log('Authentication successful');
        // Now you can send other messages
    } else if (message.type === 'error' && message.code === 401) {
        console.error('Authentication failed');
    }
};
```

### List Available Sessions

```javascript
function listSessions() {
    const message = {
        type: 'list_sessions',
        data: {}
    };
    ws.send(JSON.stringify(message));
}

// Handle response
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'sessions_list') {
        console.log('Active sessions:', message.sessions);
        console.log('Total count:', message.count);
    }
};
```

### Start a New Session

```javascript
function startSession(toolName, args = []) {
    const message = {
        type: 'start_session',
        tool_name: toolName,
        args: args
    };
    ws.send(JSON.stringify(message));
}

// Example: Start Crush session with --help
startSession('crush', ['--help']);

// Handle response
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'session_started') {
        console.log('Session started:', message.session_id);
        console.log('Tool:', message.tool_name);
        console.log('Status:', message.status);
    }
};
```

### Send Command to Session

```javascript
function sendCommand(sessionId, command) {
    const message = {
        type: 'send_command',
        session_id: sessionId,
        command: command
    };
    ws.send(JSON.stringify(message));
}

// Example
sendCommand('session-uuid-here', 'npm install');

// Handle output
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'output') {
        console.log(`[${message.session_id}] Output:`, message.output);
    }
};
```

### Stop a Session

```javascript
function stopSession(sessionId) {
    const message = {
        type: 'stop_session',
        session_id: sessionId
    };
    ws.send(JSON.stringify(message));
}

// Handle response
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'session_stopped') {
        console.log('Session stopped:', message.session_id);
        console.log('Status:', message.status);
    }
};
```

### Delete a Session

```javascript
function deleteSession(sessionId) {
    const message = {
        type: 'delete_session',
        session_id: sessionId
    };
    ws.send(JSON.stringify(message));
}

// Handle response
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'session_deleted') {
        console.log('Session deleted:', message.session_id);
    }
};
```

### TypeScript Example (with Types)

```typescript
interface WebSocketMessage {
    type: string;
    data?: any;
    session_id?: string;
    tool_name?: string;
    args?: string[];
    command?: string;
    output?: string;
    timestamp?: string;
}

class ZhinengBridgeClient {
    private ws: WebSocket;

    constructor(url: string) {
        this.ws = new WebSocket(url);
        this.setupEventHandlers();
    }

    private setupEventHandlers(): void {
        this.ws.onopen = () => {
            console.log('Connected to Zhineng-bridge');
        };

        this.ws.onmessage = (event: MessageEvent) => {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onerror = (error: Event) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('Disconnected from Zhineng-bridge');
        };
    }

    private handleMessage(message: WebSocketMessage): void {
        switch (message.type) {
            case 'sessions_list':
                console.log('Sessions:', message.sessions);
                break;
            case 'session_started':
                console.log('Session started:', message.session_id);
                break;
            case 'output':
                console.log('Output:', message.output);
                break;
            case 'error':
                console.error('Error:', message.message);
                break;
        }
    }

    public listSessions(): void {
        this.send({ type: 'list_sessions', data: {} });
    }

    public startSession(toolName: string, args: string[] = []): void {
        this.send({ type: 'start_session', tool_name: toolName, args });
    }

    public sendCommand(sessionId: string, command: string): void {
        this.send({ type: 'send_command', session_id: sessionId, command });
    }

    public stopSession(sessionId: string): void {
        this.send({ type: 'stop_session', session_id: sessionId });
    }

    public deleteSession(sessionId: string): void {
        this.send({ type: 'delete_session', session_id: sessionId });
    }

    private send(message: WebSocketMessage): void {
        this.ws.send(JSON.stringify(message));
    }
}

// Usage
const client = new ZhinengBridgeClient('ws://localhost:8765');
client.listSessions();
```

---

## Python

### Basic WebSocket Connection

```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print("Connected to Zhineng-bridge")

        # Send message
        message = {
            "type": "list_sessions",
            "data": {}
        }
        await websocket.send(json.dumps(message))

        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        print("Received:", data)

# Run
asyncio.run(connect())
```

### With Authentication

```python
import asyncio
import websockets
import json

async def connect_with_auth():
    uri = "wss://your-domain.com:8765"
    async with websockets.connect(uri) as websocket:
        print("Connected to Zhineng-bridge")

        # Send authentication
        auth_message = {
            "type": "authenticate",
            "token": "your-jwt-token-here"
        }
        await websocket.send(json.dumps(auth_message))

        # Receive auth response
        response = await websocket.recv()
        data = json.loads(response)

        if data.get("type") == "auth_success":
            print("Authentication successful")
            # Now you can send other messages
        else:
            print("Authentication failed")
            return

        # Send other messages
        message = {"type": "list_sessions", "data": {}}
        await websocket.send(json.dumps(message))

        response = await websocket.recv()
        print("Sessions:", json.loads(response))

asyncio.run(connect_with_auth())
```

### Complete Session Management Example

```python
import asyncio
import websockets
import json

class ZhinengBridgeClient:
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket = None

    async def connect(self):
        """Connect to the WebSocket server"""
        self.websocket = await websockets.connect(self.uri)
        print(f"✅ Connected to {self.uri}")

    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            print("❌ Disconnected")

    async def send_message(self, message: dict) -> dict:
        """Send a message and return the response"""
        if not self.websocket:
            raise Exception("Not connected")

        await self.websocket.send(json.dumps(message))
        response = await self.websocket.recv()
        return json.loads(response)

    async def list_sessions(self) -> dict:
        """List all active sessions"""
        message = {"type": "list_sessions", "data": {}}
        return await self.send_message(message)

    async def start_session(self, tool_name: str, args: list = None) -> dict:
        """Start a new session"""
        message = {
            "type": "start_session",
            "tool_name": tool_name,
            "args": args or []
        }
        return await self.send_message(message)

    async def send_command(self, session_id: str, command: str) -> dict:
        """Send a command to a session"""
        message = {
            "type": "send_command",
            "session_id": session_id,
            "command": command
        }
        return await self.send_message(message)

    async def stop_session(self, session_id: str) -> dict:
        """Stop a running session"""
        message = {
            "type": "stop_session",
            "session_id": session_id
        }
        return await self.send_message(message)

    async def delete_session(self, session_id: str) -> dict:
        """Delete a session"""
        message = {
            "type": "delete_session",
            "session_id": session_id
        }
        return await self.send_message(message)

    async def listen(self):
        """Listen for incoming messages"""
        if not self.websocket:
            raise Exception("Not connected")

        async for message in self.websocket:
            data = json.loads(message)
            print(f"📨 Received: {data}")

# Usage
async def main():
    client = ZhinengBridgeClient()
    await client.connect()

    try:
        # List sessions
        sessions = await client.list_sessions()
        print(f"Active sessions: {sessions.get('count', 0)}")

        # Start a session
        session = await client.start_session('crush', ['--help'])
        print(f"Session started: {session.get('session_id')}")

        # Listen for output
        await asyncio.sleep(1)
        await client.listen()

    finally:
        await client.disconnect()

asyncio.run(main())
```

### HTTP Endpoints Example

```python
import requests

def get_health():
    """Get health status"""
    response = requests.get('http://localhost:8000/health')
    return response.json()

def get_metrics():
    """Get service metrics"""
    response = requests.get('http://localhost:8000/metrics')
    return response.json()

def get_status():
    """Get service status"""
    response = requests.get('http://localhost:8000/status')
    return response.json()

# Usage
health = get_health()
print(f"Health status: {health['status']}")

metrics = get_metrics()
print(f"Rate limiting enabled: {metrics['rate_limiting']['enabled']}")

status = get_status()
print(f"WSS enabled: {status['features']['wss_enabled']}")
```

---

## Go

### Basic WebSocket Connection

```go
package main

import (
    "encoding/json"
    "fmt"
    "log"

    "github.com/gorilla/websocket"
)

type Message struct {
    Type      string                 `json:"type"`
    Data      map[string]interface{} `json:"data,omitempty"`
    SessionID string                 `json:"session_id,omitempty"`
    ToolName  string                 `json:"tool_name,omitempty"`
    Args      []string               `json:"args,omitempty"`
    Command   string                 `json:"command,omitempty"`
    Output    string                 `json:"output,omitempty"`
    Timestamp string                 `json:"timestamp,omitempty"`
}

func main() {
    uri := "ws://localhost:8765"

    conn, _, err := websocket.DefaultDialer.Dial(uri, nil)
    if err != nil {
        log.Fatal("Dial error:", err)
    }
    defer conn.Close()

    fmt.Println("Connected to Zhineng-bridge")

    // Send message
    message := Message{
        Type: "list_sessions",
        Data: map[string]interface{}{},
    }
    err = conn.WriteJSON(message)
    if err != nil {
        log.Fatal("Write error:", err)
    }

    // Receive response
    var response Message
    err = conn.ReadJSON(&response)
    if err != nil {
        log.Fatal("Read error:", err)
    }

    fmt.Printf("Received: %+v\n", response)
}
```

### With Authentication

```go
package main

import (
    "encoding/json"
    "fmt"
    "log"

    "github.com/gorilla/websocket"
)

type AuthMessage struct {
    Type  string `json:"type"`
    Token string `json:"token"`
}

func main() {
    uri := "wss://your-domain.com:8765"

    conn, _, err := websocket.DefaultDialer.Dial(uri, nil)
    if err != nil {
        log.Fatal("Dial error:", err)
    }
    defer conn.Close()

    fmt.Println("Connected to Zhineng-bridge")

    // Send authentication
    authMessage := AuthMessage{
        Type:  "authenticate",
        Token: "your-jwt-token-here",
    }
    err = conn.WriteJSON(authMessage)
    if err != nil {
        log.Fatal("Write error:", err)
    }

    // Receive auth response
    var response map[string]interface{}
    err = conn.ReadJSON(&response)
    if err != nil {
        log.Fatal("Read error:", err)
    }

    if response["type"] == "auth_success" {
        fmt.Println("Authentication successful")
    } else {
        fmt.Println("Authentication failed")
        return
    }

    // Send other messages
    message := map[string]interface{}{
        "type": "list_sessions",
        "data": map[string]interface{}{},
    }
    err = conn.WriteJSON(message)
    if err != nil {
        log.Fatal("Write error:", err)
    }

    // Receive sessions
    err = conn.ReadJSON(&response)
    if err != nil {
        log.Fatal("Read error:", err)
    }

    fmt.Printf("Sessions: %+v\n", response)
}
```

### Complete Client Example

```go
package main

import (
    "encoding/json"
    "fmt"
    "log"

    "github.com/gorilla/websocket"
)

type ZhinengBridgeClient struct {
    conn *websocket.Conn
    uri  string
}

func NewZhinengBridgeClient(uri string) *ZhinengBridgeClient {
    return &ZhinengBridgeClient{uri: uri}
}

func (c *ZhinengBridgeClient) Connect() error {
    conn, _, err := websocket.DefaultDialer.Dial(c.uri, nil)
    if err != nil {
        return err
    }
    c.conn = conn
    fmt.Printf("✅ Connected to %s\n", c.uri)
    return nil
}

func (c *ZhinengBridgeClient) Disconnect() error {
    if c.conn != nil {
        err := c.conn.Close()
        c.conn = nil
        fmt.Println("❌ Disconnected")
        return err
    }
    return nil
}

func (c *ZhinengBridgeClient) SendMessage(message interface{}) (map[string]interface{}, error) {
    if c.conn == nil {
        return nil, fmt.Errorf("not connected")
    }

    err := c.conn.WriteJSON(message)
    if err != nil {
        return nil, err
    }

    var response map[string]interface{}
    err = c.conn.ReadJSON(&response)
    if err != nil {
        return nil, err
    }

    return response, nil
}

func (c *ZhinengBridgeClient) ListSessions() (map[string]interface{}, error) {
    message := map[string]interface{}{
        "type": "list_sessions",
        "data": map[string]interface{}{},
    }
    return c.SendMessage(message)
}

func (c *ZhinengBridgeClient) StartSession(toolName string, args []string) (map[string]interface{}, error) {
    message := map[string]interface{}{
        "type":      "start_session",
        "tool_name": toolName,
        "args":      args,
    }
    return c.SendMessage(message)
}

func (c *ZhinengBridgeClient) SendCommand(sessionID, command string) (map[string]interface{}, error) {
    message := map[string]interface{}{
        "type":       "send_command",
        "session_id": sessionID,
        "command":    command,
    }
    return c.SendMessage(message)
}

func (c *ZhinengBridgeClient) StopSession(sessionID string) (map[string]interface{}, error) {
    message := map[string]interface{}{
        "type":       "stop_session",
        "session_id": sessionID,
    }
    return c.SendMessage(message)
}

func (c *ZhinengBridgeClient) DeleteSession(sessionID string) (map[string]interface{}, error) {
    message := map[string]interface{}{
        "type":       "delete_session",
        "session_id": sessionID,
    }
    return c.SendMessage(message)
}

func (c *ZhinengBridgeClient) Listen() error {
    for {
        var response map[string]interface{}
        err := c.conn.ReadJSON(&response)
        if err != nil {
            return err
        }
        fmt.Printf("📨 Received: %+v\n", response)
    }
}

func main() {
    client := NewZhinengBridgeClient("ws://localhost:8765")

    err := client.Connect()
    if err != nil {
        log.Fatal("Connection error:", err)
    }
    defer client.Disconnect()

    // List sessions
    sessions, err := client.ListSessions()
    if err != nil {
        log.Fatal("Error listing sessions:", err)
    }
    fmt.Printf("Sessions: %+v\n", sessions)

    // Start a session
    session, err := client.StartSession("crush", []string{"--help"})
    if err != nil {
        log.Fatal("Error starting session:", err)
    }
    fmt.Printf("Session started: %+v\n", session)
}
```

---

## Java

### Basic WebSocket Connection

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import org.json.JSONObject;

public class ZhinengBridgeClient {
    private WebSocket webSocket;
    private final HttpClient httpClient;

    public ZhinengBridgeClient() {
        this.httpClient = HttpClient.newHttpClient();
    }

    public void connect(String uri) throws InterruptedException, ExecutionException {
        CompletableFuture<Void> connectFuture = new CompletableFuture<>();

        webSocket = httpClient.newWebSocketBuilder()
            .buildAsync(URI.create(uri), new WebSocket.Listener() {
                @Override
                public void onOpen(WebSocket ws) {
                    System.out.println("Connected to Zhineng-bridge");
                    connectFuture.complete(null);
                }

                @Override
                public void onMessage(WebSocket ws, CharSequence data) {
                    JSONObject message = new JSONObject(data.toString());
                    System.out.println("Received: " + message);
                }

                @Override
                public void onError(WebSocket ws, Throwable error) {
                    System.err.println("WebSocket error: " + error.getMessage());
                    connectFuture.completeExceptionally(error);
                }
            })
            .join();

        connectFuture.get();
    }

    public void sendMessage(JSONObject message) {
        webSocket.sendText(message.toString(), true);
    }

    public JSONObject listSessions() {
        JSONObject message = new JSONObject();
        message.put("type", "list_sessions");
        message.put("data", new JSONObject());
        sendMessage(message);
        return message;
    }

    public void disconnect() {
        webSocket.sendClose(WebSocket.NORMAL_CLOSURE, "Client closing", true);
        System.out.println("Disconnected");
    }

    public static void main(String[] args) throws InterruptedException, ExecutionException {
        ZhinengBridgeClient client = new ZhinengBridgeClient();
        client.connect("ws://localhost:8765");

        client.listSessions();

        // Keep connection open
        Thread.sleep(5000);
        client.disconnect();
    }
}
```

### With Authentication

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import org.json.JSONObject;

public class ZhinengBridgeClient {
    private WebSocket webSocket;
    private final HttpClient httpClient;
    private boolean authenticated = false;

    public ZhinengBridgeClient() {
        this.httpClient = HttpClient.newHttpClient();
    }

    public void connect(String uri, String token) throws InterruptedException, ExecutionException {
        CompletableFuture<Void> connectFuture = new CompletableFuture<>();

        webSocket = httpClient.newWebSocketBuilder()
            .buildAsync(URI.create(uri), new WebSocket.Listener() {
                @Override
                public void onOpen(WebSocket ws) {
                    System.out.println("Connected to Zhineng-bridge");
                    authenticate(token);
                }

                @Override
                public void onMessage(WebSocket ws, CharSequence data) {
                    JSONObject message = new JSONObject(data.toString());

                    if (message.getString("type").equals("auth_success")) {
                        System.out.println("Authentication successful");
                        authenticated = true;
                        connectFuture.complete(null);
                    } else {
                        System.out.println("Received: " + message);
                    }
                }

                @Override
                public void onError(WebSocket ws, Throwable error) {
                    System.err.println("WebSocket error: " + error.getMessage());
                    connectFuture.completeExceptionally(error);
                }
            })
            .join();

        connectFuture.get();
    }

    private void authenticate(String token) {
        JSONObject authMessage = new JSONObject();
        authMessage.put("type", "authenticate");
        authMessage.put("token", token);
        webSocket.sendText(authMessage.toString(), true);
    }

    public void sendMessage(JSONObject message) {
        if (!authenticated) {
            System.err.println("Not authenticated");
            return;
        }
        webSocket.sendText(message.toString(), true);
    }

    public void disconnect() {
        webSocket.sendClose(WebSocket.NORMAL_CLOSURE, "Client closing", true);
        System.out.println("Disconnected");
    }

    public static void main(String[] args) throws InterruptedException, ExecutionException {
        ZhinengBridgeClient client = new ZhinengBridgeClient();
        client.connect("wss://your-domain.com:8765", "your-jwt-token-here");

        // Keep connection open
        Thread.sleep(5000);
        client.disconnect();
    }
}
```

---

## C#

### Basic WebSocket Connection

```csharp
using System;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;

public class ZhinengBridgeClient : IDisposable
{
    private ClientWebSocket _webSocket;
    private readonly Uri _uri;

    public ZhinengBridgeClient(string uri)
    {
        _uri = new Uri(uri);
    }

    public async Task ConnectAsync()
    {
        _webSocket = new ClientWebSocket();
        await _webSocket.ConnectAsync(_uri, CancellationToken.None);
        Console.WriteLine($"✅ Connected to {_uri}");
    }

    public async Task SendMessageAsync(object message)
    {
        var json = JsonConvert.SerializeObject(message);
        var buffer = Encoding.UTF8.GetBytes(json);
        await _webSocket.SendAsync(new ArraySegment<byte>(buffer),
            WebSocketMessageType.Text, true, CancellationToken.None);
    }

    public async Task<string> ReceiveMessageAsync()
    {
        var buffer = new byte[4096];
        var result = await _webSocket.ReceiveAsync(new ArraySegment<byte>(buffer),
            CancellationToken.None);
        return Encoding.UTF8.GetString(buffer, 0, result.Count);
    }

    public async Task<dynamic> ListSessionsAsync()
    {
        var message = new { type = "list_sessions", data = new { } };
        await SendMessageAsync(message);
        var response = await ReceiveMessageAsync();
        return JsonConvert.DeserializeObject<dynamic>(response);
    }

    public async Task DisconnectAsync()
    {
        if (_webSocket != null)
        {
            await _webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure,
                "Client closing", CancellationToken.None);
            Console.WriteLine("❌ Disconnected");
        }
    }

    public void Dispose()
    {
        _webSocket?.Dispose();
    }

    public static async Task Main(string[] args)
    {
        using var client = new ZhinengBridgeClient("ws://localhost:8765");

        await client.ConnectAsync();

        var sessions = await client.ListSessionsAsync();
        Console.WriteLine($"Sessions: {sessions}");

        await Task.Delay(5000);
        await client.DisconnectAsync();
    }
}
```

---

## Rust

### Basic WebSocket Connection

```rust
use serde_json::json;
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let uri = "ws://localhost:8765";

    let (ws_stream, _) = connect_async(uri).await?;
    println!("✅ Connected to {}", uri);

    let (mut write, mut read) = ws_stream.split();

    // Send message
    let message = json!({
        "type": "list_sessions",
        "data": {}
    });
    write.send(Message::Text(message.to_string())).await?;

    // Receive response
    if let Some(msg) = read.next().await {
        let msg = msg?;
        if msg.is_text() {
            let text = msg.to_text()?;
            let response: serde_json::Value = serde_json::from_str(text)?;
            println!("Received: {}", response);
        }
    }

    Ok(())
}
```

### With Authentication

```rust
use serde_json::json;
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let uri = "wss://your-domain.com:8765";
    let token = "your-jwt-token-here";

    let (ws_stream, _) = connect_async(uri).await?;
    println!("✅ Connected to {}", uri);

    let (mut write, mut read) = ws_stream.split();

    // Send authentication
    let auth_message = json!({
        "type": "authenticate",
        "token": token
    });
    write.send(Message::Text(auth_message.to_string())).await?;

    // Receive auth response
    if let Some(msg) = read.next().await {
        let msg = msg?;
        if msg.is_text() {
            let text = msg.to_text()?;
            let response: serde_json::Value = serde_json::from_str(text)?;

            if response["type"] == "auth_success" {
                println!("Authentication successful");
            } else {
                println!("Authentication failed");
                return Ok(());
            }
        }
    }

    // Send other messages
    let message = json!({
        "type": "list_sessions",
        "data": {}
    });
    write.send(Message::Text(message.to_string())).await?;

    // Receive sessions
    if let Some(msg) = read.next().await {
        let msg = msg?;
        if msg.is_text() {
            let text = msg.to_text()?;
            let response: serde_json::Value = serde_json::from_str(text)?;
            println!("Sessions: {}", response);
        }
    }

    Ok(())
}
```

---

## Error Handling

All clients should handle the following error codes:

- **400**: Bad Request - Invalid message format
- **401**: Unauthorized - Authentication required or failed
- **403**: Forbidden - Insufficient permissions
- **404**: Not Found - Resource not found
- **409**: Conflict - Resource already exists
- **422**: Unprocessable Entity - Validation error
- **429**: Too Many Requests - Rate limit exceeded
- **500**: Internal Server Error - Server error
- **503**: Service Unavailable - Service temporarily unavailable
- **504**: Gateway Timeout - Request timeout

Example error response:

```json
{
  "type": "error",
  "code": 401,
  "message": "Unauthorized: Authentication required"
}
```

---

## Best Practices

1. **Connection Management**
   - Implement auto-reconnection logic
   - Handle connection errors gracefully
   - Use heartbeats to keep connections alive

2. **Message Handling**
   - Always validate message structure
   - Handle errors appropriately
   - Implement message queuing for reliability

3. **Security**
   - Use WSS (WebSocket Secure) in production
   - Store tokens securely
   - Implement rate limiting on the client side

4. **Performance**
   - Batch messages when possible
   - Use compression for large payloads
   - Implement message deduplication

---

## Support

For more information, visit:
- [OpenAPI Documentation](/docs)
- [OpenAPI Specification](/openapi.yaml)
- [GitHub Repository](https://github.com/guangda88/zhineng-bridge)
