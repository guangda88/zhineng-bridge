#!/usr/bin/env python3
"""
持续监控 zhineng-bridge 服务器日志
Monitor zhineng-bridge server logs continuously
"""
import subprocess
import json
import time
from datetime import datetime

# Configuration
LOG_FILE = "/tmp/relay_server.log"
CHECK_INTERVAL = 10  # seconds
HISTORY_SIZE = 100  # lines to keep in history

# Statistics
stats = {
    'errors': 0,
    'warnings': 0,
    'sessions_created': 0,
    'sessions_stopped': 0,
    'clients_connected': 0,
    'clients_disconnected': 0,
    'messages_processed': 0,
    'outputs_sent': 0
}

# Track unique client IDs
active_clients = set()
total_clients = set()

def parse_log_line(line):
    """Parse a JSON log line"""
    try:
        return json.loads(line)
    except:
        return None

def process_log_line(data, stats):
    """Process a single log line and update statistics"""
    event = data.get('event', '')
    level = data.get('level', 'info')

    # Track errors and warnings
    if level == 'error':
        stats['errors'] += 1
        print(f"❌ ERROR: {data.get('message', 'Unknown error')}")
        if 'exception' in data:
            print(f"   Exception: {data['exception'][:200]}")
    elif level == 'warning':
        stats['warnings'] += 1
        print(f"⚠️  WARNING: {data.get('message', 'Unknown warning')}")

    # Track events
    if event == 'Client connected':
        client_id = data.get('client_id')
        active_clients.add(client_id)
        total_clients.add(client_id)
        stats['clients_connected'] += 1
        print(f"🔗 Client connected: {client_id[:8]}...")

    elif event == 'Client removed':
        client_id = data.get('client_id')
        if client_id in active_clients:
            active_clients.remove(client_id)
        stats['clients_disconnected'] += 1
        print(f"🔌 Client disconnected: {client_id[:8]}...")

    elif event == 'Session created':
        stats['sessions_created'] += 1
        session_id = data.get('session_id', '')[:8]
        tool_name = data.get('tool_name', 'unknown')
        print(f"✅ Session created: {session_id}... ({tool_name})")

    elif event == 'Session stopped':
        stats['sessions_stopped'] += 1
        session_id = data.get('session_id', '')[:8]
        print(f"⏹️  Session stopped: {session_id}...")

    elif event == 'Output sent' or 'output' in event.lower():
        stats['outputs_sent'] += 1

    elif 'handle_message' in event:
        stats['messages_processed'] += 1

def print_summary(stats):
    """Print current statistics summary"""
    print("\n" + "="*60)
    print("📊 MONITORING SUMMARY")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📈 Statistics:")
    print(f"  Errors:        {stats['errors']}")
    print(f"  Warnings:      {stats['warnings']}")
    print(f"  Sessions:      {stats['sessions_created']} created, {stats['sessions_stopped']} stopped")
    print(f"  Clients:       {stats['clients_connected']} total, {len(active_clients)} active")
    print(f"  Messages:      {stats['messages_processed']}")
    print(f"  Outputs sent:  {stats['outputs_sent']}")
    print("="*60 + "\n")

def monitor_logs():
    """Main monitoring loop"""
    print("🚀 Starting zhineng-bridge log monitor")
    print(f"📁 Monitoring: {LOG_FILE}")
    print(f"⏱️  Check interval: {CHECK_INTERVAL} seconds\n")

    # Use tail -f to monitor logs
    process = subprocess.Popen(
        ['tail', '-n', '0', '-f', LOG_FILE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    last_summary = time.time()
    line_count = 0

    try:
        while True:
            line = process.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue

            line = line.strip()
            if not line:
                continue

            data = parse_log_line(line)
            if data:
                process_log_line(data, stats)
                line_count += 1

            # Print summary periodically
            if time.time() - last_summary >= CHECK_INTERVAL:
                print_summary(stats)
                last_summary = time.time()

    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
    finally:
        process.terminate()
        print_summary(stats)

if __name__ == "__main__":
    try:
        monitor_logs()
    except Exception as e:
        print(f"Failed to start monitor: {e}")
        import traceback
        traceback.print_exc()
