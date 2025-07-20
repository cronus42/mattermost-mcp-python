# ⚙️ Configuration Guide

Complete guide to configuring Mattermost MCP Python for different environments and use cases.

## Configuration Methods

1. **[Environment Variables](#environment-variables)** - Recommended for most deployments
2. **[Configuration Files](#configuration-files)** - For complex configurations
3. **[Command Line Arguments](#command-line-arguments)** - For development and testing
4. **[Docker Configuration](#docker-configuration)** - For containerized deployments

## Environment Variables

### Core Configuration

```bash
# Required - Mattermost Connection
MATTERMOST_URL=https://your-mattermost-instance.com
MATTERMOST_TOKEN=xoxb-your-bot-token-here
MATTERMOST_TEAM_ID=your-team-id-optional

# MCP Server Settings
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3000
MCP_SERVER_NAME="Mattermost MCP Server"

# Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json                   # json, text
LOG_FILE=/var/log/mcp/server.log  # Optional log file path
```

### Advanced Configuration

```bash
# HTTP Client Settings
HTTP_TIMEOUT=30                   # Request timeout in seconds
HTTP_MAX_RETRIES=3               # Maximum retry attempts
HTTP_RETRY_BACKOFF_FACTOR=2.0    # Exponential backoff multiplier
HTTP_VERIFY_SSL=true             # SSL certificate verification

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_SECOND=10  # Requests per second limit
RATE_LIMIT_BURST_SIZE=20           # Burst capacity
RATE_LIMIT_ENABLE=true             # Enable/disable rate limiting

# WebSocket Configuration
ENABLE_WEBSOCKET=true              # Enable WebSocket streaming
WS_URL=wss://your-mattermost.com/api/v4/websocket  # Custom WebSocket URL
WS_RECONNECT_INTERVAL=5           # Reconnection interval in seconds
WS_MAX_RECONNECT_ATTEMPTS=10      # Maximum reconnection attempts

# Polling Configuration
ENABLE_POLLING=true               # Enable REST API polling fallback
POLLING_INTERVAL=30               # Polling interval in seconds
POLLING_BATCH_SIZE=100           # Number of items per poll

# Resource Configuration
DEFAULT_CHANNEL_ID=your-default-channel-id
ALLOWED_CHANNELS=channel1,channel2,channel3  # Comma-separated channel IDs
ALLOWED_USERS=user1,user2,user3              # Comma-separated user IDs
MONITOR_ALL_CHANNELS=false                    # Monitor all accessible channels

# Caching
ENABLE_CACHING=true              # Enable in-memory caching
CACHE_TTL=300                    # Cache TTL in seconds
CACHE_MAX_SIZE=1000              # Maximum cache entries

# Security
WEBHOOK_SECRET=your-webhook-secret-key        # Webhook signature validation
API_RATE_LIMIT=100               # Global API rate limit per hour
MAX_MESSAGE_LENGTH=4000          # Maximum message length
ENABLE_ADMIN_ENDPOINTS=false     # Enable admin-only endpoints

# Performance
MAX_CONCURRENT_REQUESTS=50       # Maximum concurrent HTTP requests
CONNECTION_POOL_SIZE=20          # HTTP connection pool size
WORKER_THREADS=4                 # Number of worker threads

# Feature Flags
ENABLE_FILE_UPLOADS=true         # Enable file upload functionality
ENABLE_REACTIONS=true            # Enable emoji reactions
ENABLE_THREADS=true              # Enable thread support
ENABLE_SEARCH=true               # Enable search functionality
ENABLE_METRICS=true              # Enable metrics collection
```

### Development Settings

```bash
# Development Mode
DEVELOPMENT_MODE=true            # Enable development features
DEBUG_HTTP_REQUESTS=false       # Log all HTTP requests/responses
MOCK_MATTERMOST=false           # Use mock Mattermost for testing
TEST_CHANNEL_ID=test-channel-id  # Channel for development testing

# Hot Reloading
ENABLE_HOT_RELOAD=true          # Auto-reload on code changes
WATCH_DIRECTORIES=./mcp_mattermost  # Directories to watch for changes

# Debugging
ENABLE_PROFILING=false          # Enable performance profiling
PROFILE_OUTPUT_DIR=./profiles   # Profiling output directory
CORRELATION_ID_HEADER=X-Correlation-ID  # Request correlation header
```

## Configuration Files

### YAML Configuration

Create `config.yaml`:

```yaml
# Core Configuration
mattermost:
  url: "https://your-mattermost.com"
  token: "${MATTERMOST_TOKEN}"  # Environment variable substitution
  team_id: "${MATTERMOST_TEAM_ID}"
  verify_ssl: true

# MCP Server
server:
  host: "0.0.0.0"
  port: 3000
  name: "Mattermost MCP Server"

# HTTP Client
http:
  timeout: 30
  max_retries: 3
  retry_backoff_factor: 2.0
  rate_limit:
    enabled: true
    requests_per_second: 10
    burst_size: 20

# WebSocket
websocket:
  enabled: true
  url: null  # Auto-derive from mattermost.url
  reconnect_interval: 5
  max_reconnect_attempts: 10

# Polling
polling:
  enabled: true
  interval: 30
  batch_size: 100

# Resources
resources:
  default_channel: "${DEFAULT_CHANNEL_ID}"
  allowed_channels: []  # Empty means all accessible channels
  allowed_users: []     # Empty means all users
  monitor_all_channels: false

# Caching
cache:
  enabled: true
  ttl: 300
  max_size: 1000

# Logging
logging:
  level: "INFO"
  format: "json"
  file: "/var/log/mcp/server.log"

# Security
security:
  webhook_secret: "${WEBHOOK_SECRET}"
  api_rate_limit: 100
  max_message_length: 4000
  enable_admin_endpoints: false

# Performance
performance:
  max_concurrent_requests: 50
  connection_pool_size: 20
  worker_threads: 4

# Features
features:
  file_uploads: true
  reactions: true
  threads: true
  search: true
  metrics: true
```

### JSON Configuration

Create `config.json`:

```json
{
  "mattermost": {
    "url": "https://your-mattermost.com",
    "token": "${MATTERMOST_TOKEN}",
    "team_id": "${MATTERMOST_TEAM_ID}",
    "verify_ssl": true
  },
  "server": {
    "host": "0.0.0.0",
    "port": 3000,
    "name": "Mattermost MCP Server"
  },
  "http": {
    "timeout": 30,
    "max_retries": 3,
    "retry_backoff_factor": 2.0,
    "rate_limit": {
      "enabled": true,
      "requests_per_second": 10,
      "burst_size": 20
    }
  },
  "websocket": {
    "enabled": true,
    "reconnect_interval": 5,
    "max_reconnect_attempts": 10
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  },
  "features": {
    "file_uploads": true,
    "reactions": true,
    "threads": true,
    "search": true,
    "metrics": true
  }
}
```

### Using Configuration Files

```bash
# Start with YAML config
python -m mcp_mattermost --config config.yaml

# Start with JSON config
python -m mcp_mattermost --config config.json

# Environment variables override config file values
MATTERMOST_URL=https://different-server.com python -m mcp_mattermost --config config.yaml
```

## Command Line Arguments

```bash
# Core options
python -m mcp_mattermost \
  --mattermost-url https://mattermost.example.com \
  --mattermost-token xoxb-your-token \
  --team-id your-team-id \
  --host 0.0.0.0 \
  --port 3000

# Advanced options
python -m mcp_mattermost \
  --config config.yaml \
  --log-level DEBUG \
  --log-format text \
  --enable-websocket \
  --disable-polling \
  --rate-limit 20 \
  --timeout 45 \
  --max-retries 5

# Development options
python -m mcp_mattermost \
  --development \
  --debug \
  --hot-reload \
  --mock-mattermost \
  --test-channel test-channel-id
```

### Full Command Line Reference

```bash
python -m mcp_mattermost --help

Usage: python -m mcp_mattermost [OPTIONS]

Options:
  --config PATH                   Configuration file path
  --mattermost-url TEXT          Mattermost instance URL
  --mattermost-token TEXT        Mattermost API token
  --team-id TEXT                 Mattermost team ID
  --host TEXT                    Server host [default: localhost]
  --port INTEGER                 Server port [default: 3000]
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
  --log-format [json|text]       Log format [default: json]
  --enable-websocket / --disable-websocket
  --enable-polling / --disable-polling
  --rate-limit INTEGER           Requests per second limit
  --timeout INTEGER              HTTP timeout in seconds
  --max-retries INTEGER          Maximum retry attempts
  --development                  Enable development mode
  --debug                        Enable debug logging
  --hot-reload                   Enable hot reloading
  --help                         Show this message and exit
```

## Docker Configuration

### Environment File

Create `.env` file:

```bash
# Core Configuration
MATTERMOST_URL=https://mattermost.company.com
MATTERMOST_TOKEN=xoxb-your-bot-token
MATTERMOST_TEAM_ID=your-team-id

# Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=3000
LOG_LEVEL=INFO

# Optional Features
ENABLE_WEBSOCKET=true
ENABLE_METRICS=true
ENABLE_FILE_UPLOADS=true
```

### Docker Compose

```yaml
version: '3.8'

services:
  mcp-mattermost:
    image: mattermost-mcp-python:latest
    restart: unless-stopped
    environment:
      # Load from .env file
      - MATTERMOST_URL=${MATTERMOST_URL}
      - MATTERMOST_TOKEN=${MATTERMOST_TOKEN}
      - MATTERMOST_TEAM_ID=${MATTERMOST_TEAM_ID}
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=3000
      - LOG_LEVEL=${LOG_LEVEL:-INFO}

      # Advanced configuration
      - ENABLE_WEBSOCKET=${ENABLE_WEBSOCKET:-true}
      - ENABLE_METRICS=${ENABLE_METRICS:-true}
      - RATE_LIMIT_REQUESTS_PER_SECOND=${RATE_LIMIT:-10}

    ports:
      - "${MCP_SERVER_PORT:-3000}:3000"
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Docker Secrets

For production deployments with Docker Swarm:

```yaml
version: '3.8'

services:
  mcp-mattermost:
    image: mattermost-mcp-python:latest
    environment:
      - MATTERMOST_URL=https://mattermost.company.com
      - MATTERMOST_TOKEN_FILE=/run/secrets/mattermost_token
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=3000
    secrets:
      - mattermost_token
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure

secrets:
  mattermost_token:
    external: true
```

## Environment-Specific Configurations

### Development

```bash
# .env.development
DEVELOPMENT_MODE=true
LOG_LEVEL=DEBUG
LOG_FORMAT=text
ENABLE_HOT_RELOAD=true
DEBUG_HTTP_REQUESTS=true
MOCK_MATTERMOST=false

# Relaxed limits for development
RATE_LIMIT_REQUESTS_PER_SECOND=100
HTTP_TIMEOUT=60
MAX_CONCURRENT_REQUESTS=10

# Test channel for safe development
TEST_CHANNEL_ID=dev-test-channel
DEFAULT_CHANNEL_ID=${TEST_CHANNEL_ID}
```

### Staging

```bash
# .env.staging
MATTERMOST_URL=https://staging-mattermost.company.com
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_METRICS=true

# Moderate limits for staging
RATE_LIMIT_REQUESTS_PER_SECOND=20
HTTP_TIMEOUT=30
CACHE_TTL=300

# Enhanced monitoring
ENABLE_PROFILING=true
CORRELATION_ID_HEADER=X-Request-ID
```

### Production

```bash
# .env.production
MATTERMOST_URL=https://mattermost.company.com
LOG_LEVEL=WARNING
LOG_FORMAT=json
LOG_FILE=/var/log/mcp/server.log

# Strict security
WEBHOOK_SECRET=your-strong-webhook-secret
API_RATE_LIMIT=50
MAX_MESSAGE_LENGTH=2000
ENABLE_ADMIN_ENDPOINTS=false

# Performance optimized
RATE_LIMIT_REQUESTS_PER_SECOND=30
HTTP_TIMEOUT=15
MAX_CONCURRENT_REQUESTS=100
CONNECTION_POOL_SIZE=50
WORKER_THREADS=8

# Caching for performance
ENABLE_CACHING=true
CACHE_TTL=600
CACHE_MAX_SIZE=5000

# All features enabled
ENABLE_WEBSOCKET=true
ENABLE_POLLING=true
ENABLE_METRICS=true
ENABLE_FILE_UPLOADS=true
```

## Kubernetes Configuration

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-mattermost-config
data:
  config.yaml: |
    mattermost:
      url: "https://mattermost.company.com"
      verify_ssl: true
    server:
      host: "0.0.0.0"
      port: 3000
    http:
      timeout: 30
      max_retries: 3
      rate_limit:
        enabled: true
        requests_per_second: 20
    websocket:
      enabled: true
      reconnect_interval: 5
    logging:
      level: "INFO"
      format: "json"
    features:
      file_uploads: true
      reactions: true
      threads: true
      metrics: true
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mcp-mattermost-secrets
type: Opaque
stringData:
  mattermost-token: "xoxb-your-bot-token"
  webhook-secret: "your-webhook-secret"
  team-id: "your-team-id"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-mattermost
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-mattermost
  template:
    metadata:
      labels:
        app: mcp-mattermost
    spec:
      containers:
      - name: mcp-mattermost
        image: mattermost-mcp-python:latest
        ports:
        - containerPort: 3000
        env:
        - name: MATTERMOST_TOKEN
          valueFrom:
            secretKeyRef:
              name: mcp-mattermost-secrets
              key: mattermost-token
        - name: MATTERMOST_TEAM_ID
          valueFrom:
            secretKeyRef:
              name: mcp-mattermost-secrets
              key: team-id
        - name: WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: mcp-mattermost-secrets
              key: webhook-secret
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: mcp-mattermost-config
```

## Configuration Validation

### Startup Validation

The server validates configuration at startup:

```python
# Configuration validation example
from mcp_mattermost.config import validate_config

try:
    config = validate_config()
    print("✅ Configuration is valid")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    exit(1)
```

### Runtime Validation

```bash
# Validate configuration without starting server
python -m mcp_mattermost --validate-config --config config.yaml

# Check configuration and exit
python -m mcp_mattermost --check-config
```

## Configuration Best Practices

### Security

1. **Use environment variables** for sensitive data (tokens, secrets)
2. **Rotate tokens regularly** and use least-privilege principles
3. **Enable SSL/TLS verification** in production
4. **Set strong webhook secrets** for signature validation
5. **Limit API rate limits** to prevent abuse

### Performance

1. **Tune rate limiting** based on your Mattermost instance capacity
2. **Enable caching** for frequently accessed data
3. **Optimize connection pool sizes** for your workload
4. **Use WebSocket streaming** for real-time requirements
5. **Configure appropriate timeouts** for your network latency

### Reliability

1. **Enable both WebSocket and polling** for redundancy
2. **Set reasonable retry limits** with exponential backoff
3. **Configure health checks** for monitoring
4. **Use structured logging** with correlation IDs
5. **Monitor metrics** for performance insights

### Monitoring

```bash
# Essential monitoring configuration
ENABLE_METRICS=true
LOG_LEVEL=INFO
LOG_FORMAT=json
CORRELATION_ID_HEADER=X-Request-ID

# Health check endpoints
curl http://localhost:3000/health      # Overall health
curl http://localhost:3000/ready       # Readiness check
curl http://localhost:3000/metrics     # Prometheus metrics
```

## Troubleshooting Configuration

### Common Issues

1. **Token Authentication Failure**
   ```bash
   # Check token validity
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        https://your-mattermost.com/api/v4/users/me
   ```

2. **WebSocket Connection Issues**
   ```bash
   # Test WebSocket endpoint
   wscat -c wss://your-mattermost.com/api/v4/websocket
   ```

3. **Rate Limiting Problems**
   ```bash
   # Check rate limit configuration
   RATE_LIMIT_REQUESTS_PER_SECOND=5  # Reduce if getting 429 errors
   ```

4. **SSL Certificate Issues**
   ```bash
   # Disable SSL verification for testing (NOT for production)
   HTTP_VERIFY_SSL=false
   ```

### Configuration Debugging

```bash
# Enable debug logging
LOG_LEVEL=DEBUG
DEBUG_HTTP_REQUESTS=true

# Validate configuration
python -m mcp_mattermost --check-config --log-level DEBUG

# Test with minimal configuration
MATTERMOST_URL=https://your-server.com \
MATTERMOST_TOKEN=your-token \
python -m mcp_mattermost --log-level DEBUG
```

For more troubleshooting help, see the [Troubleshooting Guide](troubleshooting.md).
