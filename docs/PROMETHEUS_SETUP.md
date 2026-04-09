# Prometheus Monitoring Setup Guide

This guide explains how to set up Prometheus and Grafana monitoring for Zhineng-bridge.

---

## Overview

Zhineng-bridge now supports Prometheus metrics collection. This allows you to:

- Monitor system performance in real-time
- Track WebSocket connections, sessions, and messages
- Set up alerts for error rates and performance issues
- Visualize metrics with Grafana dashboards

---

## Quick Start

### 1. Install Dependencies

The Prometheus client library is already included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Start the Health Check Server

The Prometheus metrics endpoint is available at `/prometheus` on the health check server.

```bash
cd relay-server
python3 health_check.py
```

The metrics endpoint will be available at:
```
http://localhost:8000/prometheus
```

### 3. Test the Metrics Endpoint

Open your browser or use `curl` to verify metrics are being collected:

```bash
curl http://localhost:8000/prometheus
```

You should see Prometheus-formatted metrics like:
```
# HELP zhineng_bridge_websocket_connections_total Total number of WebSocket connections
# TYPE zhineng_bridge_websocket_connections_total counter
zhineng_bridge_websocket_connections_total{status="success"} 0

# HELP zhineng_bridge_active_websocket_connections Current number of active WebSocket connections
# TYPE zhineng_bridge_active_websocket_connections gauge
zhineng_bridge_active_websocket_connections 0
```

---

## Setting Up Prometheus

### Option 1: Using Docker (Recommended)

1. **Create a `docker-compose.yml` file for Prometheus:**

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  prometheus-data:
  grafana-data:
```

2. **Start Prometheus and Grafana:**

```bash
docker-compose up -d
```

3. **Access Prometheus:**

Open your browser to: http://localhost:9090

4. **Access Grafana:**

Open your browser to: http://localhost:3000

Login with:
- Username: `admin`
- Password: `admin`

### Option 2: Manual Installation

#### Install Prometheus

```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz

# Extract
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64

# Copy configuration
cp ../config/prometheus.yml ./prometheus.yml

# Start Prometheus
./prometheus --config.file=prometheus.yml
```

Prometheus web UI will be available at: http://localhost:9090

#### Install Grafana

See: https://grafana.com/docs/grafana/latest/installation/

---

## Configuring Grafana

### 1. Add Prometheus as a Data Source

1. Log in to Grafana
2. Navigate to **Configuration** → **Data Sources**
3. Click **Add data source**
4. Select **Prometheus**
5. Set URL to: `http://localhost:9090`
6. Click **Save & Test**

### 2. Import the Dashboard

1. Navigate to **Create** → **Import**
2. Choose **Upload JSON file**
3. Select `config/grafana-dashboard.json`
4. Click **Import**

Or, create a new dashboard with the following panels:

- **Message Rate**: Track messages sent/received
- **Error Rate**: Monitor error occurrences
- **Active Connections**: Current WebSocket connections
- **Active Sessions**: Current active sessions
- **CPU Usage**: System CPU usage
- **Memory Usage**: Memory consumption
- **Sessions Created**: Total sessions created by tool

---

## Available Metrics

### Counters (Monotonically increasing)

| Metric Name | Description | Labels |
|-------------|-------------|---------|
| `zhineng_bridge_websocket_connections_total` | Total WebSocket connections | `status` (success, error) |
| `zhineng_bridge_messages_received_total` | Total messages received | `message_type` |
| `zhineng_bridge_messages_sent_total` | Total messages sent | `message_type` |
| `zhineng_bridge_sessions_created_total` | Total sessions created | `tool_name`, `status` |
| `zhineng_bridge_errors_total` | Total errors | `error_type`, `severity` |
| `zhineng_bridge_authentication_attempts_total` | Authentication attempts | `status` (success, failed) |
| `zhineng_bridge_rate_limit_violations_total` | Rate limit violations | `client_id` |

### Gauges (Values that can go up and down)

| Metric Name | Description |
|-------------|-------------|
| `zhineng_bridge_active_websocket_connections` | Current active WebSocket connections |
| `zhineng_bridge_active_sessions` | Current active sessions (labeled by `tool_name`) |
| `zhineng_bridge_pending_messages` | Messages pending to be sent |
| `zhineng_bridge_memory_usage_bytes` | Memory usage in bytes |
| `zhineng_bridge_cpu_usage_percent` | CPU usage percentage |
| `zhineng_bridge_uptime_seconds` | Server uptime in seconds |
| `zhineng_bridge_message_queue_depth` | Current message queue depth |
| `zhineng_bridge_session_manager_status` | Session manager status (1=connected, 0=disconnected) |

### Histograms (Track distributions)

| Metric Name | Description | Labels | Buckets |
|-------------|-------------|---------|---------|
| `zhineng_bridge_request_duration_seconds` | Request duration | `request_type` | 1ms, 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s |
| `zhineng_bridge_message_processing_duration_seconds` | Message processing duration | `message_type` | 1ms, 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s |
| `zhineng_bridge_session_creation_duration_seconds` | Session creation duration | `tool_name` | 1ms, 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 2s |
| `zhineng_bridge_websocket_connection_duration_seconds` | WebSocket connection duration | None | 1s, 5s, 10s, 30s, 60s, 300s, 600s, 1800s, 3600s |

---

## Prometheus Queries

### Basic Queries

```
# Current active WebSocket connections
zhineng_bridge_active_websocket_connections

# Current active sessions
sum(zhineng_bridge_active_sessions)

# Message rate (messages per second)
rate(zhineng_bridge_messages_received_total[5m])

# Error rate
rate(zhineng_bridge_errors_total[5m])

# 95th percentile of request duration
histogram_quantile(0.95, rate(zhineng_bridge_request_duration_seconds_bucket[5m]))
```

### Advanced Queries

```
# Error rate by error type
rate(zhineng_bridge_errors_total[5m]) by (error_type, severity)

# Sessions created by tool
rate(zhineng_bridge_sessions_created_total[5m]) by (tool_name)

# Message processing duration by message type
rate(zhineng_bridge_message_processing_duration_seconds_sum[5m]) by (message_type)
/
rate(zhineng_bridge_message_processing_duration_seconds_count[5m]) by (message_type)

# Authentication success rate
rate(zhineng_bridge_authentication_attempts_total[5m]{status="success"})
/
rate(zhineng_bridge_authentication_attempts_total[5m])

# Rate limit violations by client
rate(zhineng_bridge_rate_limit_violations_total[5m]) by (client_id)
```

---

## Setting Up Alerts

Create a file `alert_rules.yml`:

```yaml
groups:
  - name: zhineng_bridge_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(zhineng_bridge_errors_total[5m]) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: HighMemoryUsage
        expr: zhineng_bridge_memory_usage_bytes > 1073741824  # 1GB
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }} bytes"

      - alert: LowActiveConnections
        expr: zhineng_bridge_active_websocket_connections == 0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "No active connections"
          description: "No active WebSocket connections for 10 minutes"

      - alert: HighRateLimitViolations
        expr: rate(zhineng_bridge_rate_limit_violations_total[5m]) > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Excessive rate limit violations"
          description: "Rate limit violation rate is {{ $value }} violations/sec"
```

Add to `prometheus.yml`:

```yaml
rule_files:
  - "alert_rules.yml"
```

---

## Troubleshooting

### Metrics not appearing in Prometheus

1. **Check if health check server is running:**

```bash
curl http://localhost:8000/health
```

2. **Verify metrics endpoint:**

```bash
curl http://localhost:8000/prometheus
```

3. **Check Prometheus configuration:**

- Verify `scrape_configs` in `prometheus.yml`
- Check target status in Prometheus UI: http://localhost:9090/targets

### Grafana showing no data

1. **Verify Prometheus data source:**
   - Go to Configuration → Data Sources
   - Test the connection

2. **Check time range:**
   - Make sure the dashboard time range includes the current time

3. **Verify metric names:**
   - Check Prometheus UI for available metrics

---

## Production Considerations

### Security

1. **Enable authentication for Prometheus:**
   - Add basic auth to `/prometheus` endpoint
   - Configure Prometheus with credentials

2. **Secure Grafana:**
   - Change default admin password
   - Enable HTTPS
   - Use strong authentication

3. **Network security:**
   - Restrict access to monitoring endpoints
   - Use firewall rules
   - Consider VPN for remote access

### Performance

1. **Adjust scrape interval:**
   - Lower interval = more data = more CPU/IO
   - Recommended: 15s-30s

2. **Configure retention:**
   - `--storage.tsdb.retention.time=15d` (default)
   - Adjust based on storage requirements

3. **Use remote write:**
   - For long-term storage
   - Configure remote write to Mimir/Thanos/Cortex

### High Availability

1. **Run multiple Prometheus instances:**
   - Use Thanos for federation
   - Configure Prometheus for HA

2. **Load balance Grafana:**
   - Use multiple instances behind a load balancer
   - Shared database configuration

---

## Further Reading

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Best Practices](https://prometheus.io/docs/practices/)

---

## Support

For issues or questions:
- GitHub: https://github.com/guangda88/zhineng-bridge
- Documentation: /docs
