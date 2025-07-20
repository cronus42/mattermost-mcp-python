# Error Handling, Logging, and Metrics

This document describes the comprehensive error handling, structured logging, and optional Prometheus metrics features implemented in the Mattermost MCP server.

## Overview

The server provides three key operational features:

1. **Standardized Exception Handling** - Consistent error types with structured context
2. **Structured Logging** - JSON-formatted logs with rich context information  
3. **Optional Prometheus Metrics** - API latency, error rates, and operational metrics

## Error Handling

### Exception Hierarchy

All HTTP-related errors inherit from a common base class with structured error context:

```python
from mcp_mattermost.api.exceptions import (
    HTTPError,           # Base class for all HTTP errors
    AuthenticationError, # 401 Unauthorized
    AuthorizationError,  # 403 Forbidden
    ValidationError,     # 400 Bad Request
    NotFoundError,       # 404 Not Found
    ConflictError,       # 409 Conflict
    RateLimitError,      # 429 Too Many Requests
    ServerError,         # 5xx Server Errors
    TimeoutError,        # Request timeouts
    ConnectionError,     # Network connectivity issues
)
```

### Structured Error Context

Every exception includes comprehensive context for debugging and monitoring:

```python
try:
    await client.get("/api/v4/posts")
except HTTPError as e:
    # Access structured error context
    context = e.get_error_context()
    print(f"Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"URL: {context.get('url')}")
    print(f"Method: {context.get('method')}")
    print(f"Response Headers: {context.get('headers')}")
```

### Error Context Fields

Each exception automatically captures:

- `error_type`: Exception class name
- `message`: Human-readable error message
- `status_code`: HTTP status code (when available)
- `url`: Request URL
- `method`: HTTP method
- `headers`: Response headers
- `response_size`: Response content size
- Custom context from the calling code

## Structured Logging

### Configuration

The server uses [structlog](https://structlog.readthedocs.io/) for structured logging:

```python
import structlog

# Configure for development (pretty console output)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Configure for production (JSON output)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),  # JSON for production
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

### Logging Best Practices

The server follows structured logging best practices:

```python
import structlog

logger = structlog.get_logger(__name__)

# Good: Rich context with structured fields
logger.info(
    "HTTP request completed successfully",
    method="GET",
    url="/api/v4/posts",
    status_code=200,
    duration_ms=45.2,
    response_size=1024,
    user_id="abc123",
)

# Good: Error logging with full context
logger.error(
    "Database connection failed",
    error=str(e),
    error_type=type(e).__name__,
    database_host="postgres.example.com",
    retry_count=3,
    exc_info=True,  # Include stack trace
)
```

### Environment-Based Configuration

Set the `LOG_FORMAT` environment variable to control output format:

```bash
# Pretty console output for development
export LOG_FORMAT=console

# JSON output for production
export LOG_FORMAT=json
```

## Prometheus Metrics

### Overview

The server provides optional Prometheus metrics integration for monitoring:

- **Request Latency**: HTTP request duration histograms
- **Request Count**: Total HTTP requests by method, endpoint, and status
- **Error Count**: Error occurrences by type and endpoint  
- **Active Connections**: Current WebSocket connection count
- **Resource Updates**: Resource update events by type

### Installation

Install the optional metrics dependency:

```bash
# Install with metrics support
pip install mcp-mattermost[metrics]

# Or install prometheus-client directly
pip install prometheus-client>=0.19.0
```

### Enabling Metrics

Metrics are automatically enabled when `prometheus-client` is installed:

```python
from mcp_mattermost.metrics import metrics

# Check if metrics are enabled
if metrics.enabled:
    print("Prometheus metrics are available")
else:
    print("Metrics disabled (prometheus-client not installed)")
```

### Available Metrics

#### Request Latency Histogram
```prometheus
mattermost_mcp_request_duration_seconds{method, endpoint, status_code}
```
Tracks HTTP request duration with configurable buckets.

#### Request Counter
```prometheus  
mattermost_mcp_requests_total{method, endpoint, status_code}
```
Total number of HTTP requests made to the Mattermost API.

#### Error Counter
```prometheus
mattermost_mcp_errors_total{error_type, endpoint}
```
Total errors by exception type and endpoint.

#### Active Connections Gauge
```prometheus
mattermost_mcp_active_connections
```
Number of active WebSocket connections.

#### Resource Updates Counter
```prometheus
mattermost_mcp_resource_updates_total{resource_type, update_type}
```
Resource update events (posts created, reactions added, etc.).

### Collecting Metrics

#### Manual Collection

```python
from mcp_mattermost.metrics import metrics

# Record request metrics
metrics.record_request_latency("GET", "/api/v4/posts", 200, 0.045)
metrics.record_request_count("GET", "/api/v4/posts", 200)

# Record errors
metrics.record_error("AuthenticationError", "/api/v4/posts")

# Update connection count
metrics.set_active_connections(5)

# Record resource updates
metrics.record_resource_update("posts", "created")
```

#### Automatic Collection

Metrics are automatically collected by the HTTP client and server components.

### Exposing Metrics

#### Get Metrics Programmatically

```python
from mcp_mattermost.server import MattermostMCPServer

server = MattermostMCPServer(...)

# Get Prometheus metrics text
metrics_text = server.get_metrics()
content_type = server.get_metrics_content_type()

if metrics_text:
    print(f"Content-Type: {content_type}")
    print(metrics_text)
```

#### HTTP Metrics Endpoint

```python
import http.server
import socketserver

class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            metrics_data = server.get_metrics()
            if metrics_data:
                self.send_response(200)
                self.send_header('Content-Type', server.get_metrics_content_type())
                self.end_headers()
                self.wfile.write(metrics_data.encode('utf-8'))

# Start metrics server
with socketserver.TCPServer(("", 8080), MetricsHandler) as httpd:
    httpd.serve_forever()
```

#### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'mattermost-mcp'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## Usage Examples

### Basic Error Handling

```python
import asyncio
from mcp_mattermost.server import MattermostMCPServer
from mcp_mattermost.api.exceptions import AuthenticationError, HTTPError

async def example():
    server = MattermostMCPServer(
        mattermost_url="https://mattermost.example.com",
        mattermost_token="your-token",
    )
    
    try:
        await server.start()
        print("Server started successfully")
        
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
        print(f"Status code: {e.status_code}")
        print(f"Error context: {e.get_error_context()}")
        
    except HTTPError as e:
        print(f"HTTP error: {e}")
        print(f"Error context: {e.get_error_context()}")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        
    finally:
        await server.stop()
```

### Metrics with Context Managers

```python
from mcp_mattermost.metrics import measure_async_duration, metrics

async def example_with_metrics():
    # Measure operation duration
    async with measure_async_duration("user_operation", {"user_id": "123"}):
        await perform_user_operation()
    
    # Record custom metrics
    metrics.record_resource_update("posts", "updated")
    metrics.record_error("ValidationError", "/api/v4/posts")
```

### Complete Example

See [`examples/metrics_and_error_handling_example.py`](../examples/metrics_and_error_handling_example.py) for a comprehensive demonstration.

## Performance Considerations

### Logging Performance

- Structured logging adds minimal overhead in production
- Use appropriate log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- Consider log sampling for high-frequency operations

### Metrics Performance

- Metrics collection adds ~1-5µs per operation
- Histogram buckets should be carefully configured for your use case
- Consider metric cardinality (labels create new time series)

### Memory Usage

- Metrics are stored in memory until scraped by Prometheus
- Error context is bounded in size
- Log rotation prevents unbounded disk usage

## Configuration

### Environment Variables

```bash
# Logging
export LOG_FORMAT=json          # json|console
export LOG_LEVEL=INFO           # DEBUG|INFO|WARNING|ERROR

# Server configuration
export MATTERMOST_URL=https://your-mattermost.example.com
export MATTERMOST_TOKEN=your-token-here
export MATTERMOST_TEAM_ID=optional-team-id
```

### Programmatic Configuration

```python
from mcp_mattermost.metrics import MetricsCollector

# Create custom metrics collector
metrics_collector = MetricsCollector(enable_prometheus=True)

# Configure server with custom settings
server = MattermostMCPServer(
    mattermost_url=url,
    mattermost_token=token,
    enable_streaming=True,
    enable_polling=True,
    polling_interval=30.0,
)
```

## Best Practices

### Error Handling

1. **Catch Specific Exceptions**: Handle `AuthenticationError`, `RateLimitError`, etc. specifically
2. **Use Error Context**: Access `get_error_context()` for debugging information
3. **Log Errors Appropriately**: Use structured logging with full context
4. **Fail Gracefully**: Provide fallback behavior when possible
5. **Don't Ignore Errors**: Always log or handle exceptions appropriately

### Logging

1. **Use Structured Fields**: Provide context as keyword arguments
2. **Include Correlation IDs**: Help trace requests across components
3. **Log at Appropriate Levels**: Don't overload INFO with DEBUG information
4. **Include Timing Information**: Log operation durations
5. **Sanitize Sensitive Data**: Don't log tokens, passwords, or personal data

### Metrics

1. **Monitor Key Operations**: Focus on user-impacting functionality
2. **Use Appropriate Labels**: Keep cardinality reasonable
3. **Set Up Alerts**: Define SLIs/SLOs and alert on violations
4. **Regular Review**: Periodically review and optimize metrics collection
5. **Dashboard Creation**: Build monitoring dashboards for operational visibility

## Troubleshooting

### Common Issues

#### Metrics Not Working
- Check if `prometheus-client` is installed: `pip install prometheus-client`
- Verify metrics are enabled: `metrics.enabled` should be `True`
- Check for import errors in logs

#### High Memory Usage
- Review metric cardinality (too many label combinations)
- Check log retention settings
- Monitor for memory leaks in error context

#### Performance Issues
- Reduce logging verbosity in production
- Optimize metrics collection frequency
- Use async/await properly in error handlers

### Debugging

Enable debug logging to troubleshoot issues:

```python
import structlog
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = structlog.get_logger(__name__)
logger.debug("Debug information", extra_field="value")
```

## Integration Examples

### Grafana Dashboard

Create monitoring dashboards using the collected metrics:

```json
{
  "dashboard": {
    "title": "Mattermost MCP Server",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mattermost_mcp_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph", 
        "targets": [
          {
            "expr": "rate(mattermost_mcp_errors_total[5m])",
            "legendFormat": "{{error_type}}"
          }
        ]
      }
    ]
  }
}
```

### ELK Stack Integration

Ship structured logs to Elasticsearch:

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/mattermost-mcp/*.json
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "mattermost-mcp-%{+yyyy.MM.dd}"
```

This comprehensive error handling, logging, and metrics system provides the operational visibility needed to run the Mattermost MCP server reliably in production environments.
