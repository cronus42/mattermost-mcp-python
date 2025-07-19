# AsyncHTTPClient Documentation

The AsyncHTTPClient is a comprehensive HTTP client wrapper built on top of httpx.AsyncClient, specifically designed for robust API interactions with features like authentication, retry logic, rate limiting, and JSON parsing.

## Features

- **Token Authentication**: Automatic Bearer token authentication
- **Retry Mechanism**: Configurable retry logic with exponential backoff
- **Rate Limiting**: Token bucket rate limiting to prevent API abuse
- **JSON Parsing**: Automatic JSON serialization/deserialization
- **Error Handling**: Comprehensive exception hierarchy for different error types
- **Async Context Manager**: Proper resource management with async context managers
- **SSL Verification**: Configurable SSL verification
- **Request Logging**: Structured logging for all HTTP requests

## Quick Start

### Basic Usage

```python
import asyncio
from mcp_mattermost.api import AsyncHTTPClient

async def main():
    async with AsyncHTTPClient(
        base_url="https://your-mattermost-server.com/api/v4",
        token="your-api-token"
    ) as client:
        # GET request
        user_info = await client.get("/users/me")
        print(f"User: {user_info['username']}")
        
        # POST request with JSON
        new_post = await client.post("/posts", json={
            "channel_id": "channel-id",
            "message": "Hello World!"
        })
        print(f"Created post: {new_post['id']}")

asyncio.run(main())
```

### Convenience Context Manager

```python
from mcp_mattermost.api import create_http_client

async with create_http_client("https://api.example.com", "token") as client:
    response = await client.get("/data")
```

## Configuration Options

### AsyncHTTPClient Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | Required | Base URL for all requests |
| `token` | `str` | `None` | Authentication token |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `max_retries` | `int` | `3` | Maximum retry attempts |
| `retry_backoff_factor` | `float` | `1.0` | Exponential backoff multiplier |
| `retry_on_status` | `List[int]` | `[429, 500, 502, 503, 504]` | HTTP status codes to retry |
| `rate_limit_requests_per_second` | `float` | `10.0` | Rate limit threshold |
| `rate_limit_burst` | `int` | `20` | Maximum burst requests |
| `headers` | `Dict[str, str]` | `None` | Additional default headers |
| `verify_ssl` | `bool` | `True` | Enable SSL verification |

### Example with Custom Configuration

```python
client = AsyncHTTPClient(
    base_url="https://api.example.com",
    token="your-token",
    timeout=60.0,                    # 60-second timeout
    max_retries=5,                   # Retry up to 5 times
    retry_backoff_factor=2.0,        # Double delay each retry
    rate_limit_requests_per_second=5, # 5 requests per second
    rate_limit_burst=15,             # Allow burst of 15 requests
    verify_ssl=True,
    headers={"User-Agent": "MyApp/1.0"}
)
```

## HTTP Methods

All standard HTTP methods are supported:

```python
# GET request
data = await client.get("/endpoint", params={"key": "value"})

# POST request
result = await client.post("/endpoint", json={"data": "value"})

# PUT request
updated = await client.put("/endpoint/123", json={"data": "new_value"})

# PATCH request
patched = await client.patch("/endpoint/123", json={"field": "value"})

# DELETE request
await client.delete("/endpoint/123")

# HEAD request
await client.head("/endpoint")

# OPTIONS request
await client.options("/endpoint")
```

## Error Handling

The client provides a comprehensive exception hierarchy:

```python
from mcp_mattermost.api.exceptions import (
    HTTPError,                # Base HTTP exception
    AuthenticationError,      # 401 Unauthorized
    AuthorizationError,       # 403 Forbidden
    ValidationError,          # 400 Bad Request
    NotFoundError,           # 404 Not Found
    ConflictError,           # 409 Conflict
    RateLimitError,          # 429 Too Many Requests
    ServerError,             # 5xx Server Errors
    TimeoutError,            # Request timeouts
    ConnectionError,         # Connection issues
)

async with client:
    try:
        response = await client.get("/protected-resource")
    except AuthenticationError:
        print("Invalid token or authentication required")
    except RateLimitError as e:
        print(f"Rate limited. Retry after: {e.retry_after} seconds")
    except NotFoundError:
        print("Resource not found")
    except HTTPError as e:
        print(f"HTTP error {e.status_code}: {e}")
```

### Exception Properties

All HTTP exceptions provide:
- `status_code`: HTTP status code (if available)
- `response`: Original httpx.Response object (if available)
- `message`: Error description

`RateLimitError` additionally provides:
- `retry_after`: Seconds to wait before retrying (from Retry-After header)

## Rate Limiting

The client includes built-in rate limiting using a token bucket algorithm:

```python
from mcp_mattermost.api.client import RateLimiter

# Manual rate limiter usage
limiter = RateLimiter(requests_per_second=5.0, burst=10)

async def make_request():
    await limiter.acquire()  # Wait for token
    # Make your request here
```

### Rate Limiting Behavior

- **Burst Capacity**: Allows immediate requests up to the burst limit
- **Steady Rate**: After burst, requests are limited to the specified rate
- **Automatic Blocking**: Client automatically waits when rate limit is exceeded
- **Thread Safe**: Safe to use across multiple concurrent requests

## Retry Logic

The client automatically retries failed requests with configurable behavior:

### Retry Conditions

Requests are retried for:
- HTTP status codes in `retry_on_status` (default: 429, 500, 502, 503, 504)
- Network errors (connection timeouts, DNS failures, etc.)
- Request timeouts

### Backoff Strategy

Uses exponential backoff: `wait_time = retry_backoff_factor * (2 ** attempt)`

Example with `retry_backoff_factor=1.0`:
- 1st retry: wait 1 second
- 2nd retry: wait 2 seconds  
- 3rd retry: wait 4 seconds

### Retry Headers

The client respects `Retry-After` headers in 429 responses.

## Authentication

### Bearer Token Authentication

```python
client = AsyncHTTPClient(
    base_url="https://api.example.com",
    token="your-bearer-token"
)
# Automatically adds: Authorization: Bearer your-bearer-token
```

### Custom Authentication

```python
client = AsyncHTTPClient(
    base_url="https://api.example.com",
    headers={"Authorization": "Custom your-custom-auth"}
)
```

## Logging

The client uses structured logging via `structlog`:

```python
import structlog

# Configure logging
structlog.configure(
    processors=[structlog.stdlib.filter_by_level],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

# Logs will include:
# - Request method and URL
# - Response status codes
# - Retry attempts
# - Rate limiting events
# - Error details
```

## Advanced Usage

### Custom Headers per Request

```python
response = await client.get(
    "/endpoint",
    headers={"X-Custom-Header": "value"}
)
```

### Query Parameters

```python
response = await client.get(
    "/search",
    params={"q": "search term", "limit": 10}
)
```

### Raw Data Requests

```python
# Send raw string data
await client.post("/webhook", data="raw string data")

# Send with custom content type
await client.post(
    "/upload",
    data=binary_data,
    headers={"Content-Type": "application/octet-stream"}
)
```

### JSON vs Data Parameters

```python
# These are equivalent:
await client.post("/endpoint", json={"key": "value"})
await client.post("/endpoint", data={"key": "value"})

# Use json parameter for explicit JSON serialization
# Use data parameter for more control over serialization
```

## Best Practices

### 1. Always Use Context Managers

```python
# Good
async with AsyncHTTPClient(url, token) as client:
    await client.get("/data")

# Bad
client = AsyncHTTPClient(url, token)
await client.get("/data")  # Resources may not be cleaned up
```

### 2. Handle Specific Exceptions

```python
# Good - specific error handling
try:
    await client.get("/data")
except AuthenticationError:
    # Refresh token
    pass
except RateLimitError as e:
    # Wait and retry
    await asyncio.sleep(e.retry_after or 60)
except HTTPError as e:
    # Log unexpected errors
    logger.error("API error", status=e.status_code)

# Avoid catching all exceptions as HTTPError
```

### 3. Configure Appropriate Timeouts

```python
# For real-time APIs
client = AsyncHTTPClient(url, token, timeout=10.0)

# For batch/report APIs  
client = AsyncHTTPClient(url, token, timeout=300.0)
```

### 4. Set Reasonable Rate Limits

```python
# For production APIs
client = AsyncHTTPClient(
    url, token,
    rate_limit_requests_per_second=10.0,
    rate_limit_burst=20
)

# For development/testing
client = AsyncHTTPClient(
    url, token,
    rate_limit_requests_per_second=1.0,
    rate_limit_burst=5
)
```

## Testing

The client is designed to be testable with standard mocking:

```python
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_api_call():
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_client.return_value.request.return_value = mock_response
        
        async with AsyncHTTPClient("https://api.test", "token") as client:
            result = await client.get("/test")
            assert result == {"result": "success"}
```

## Migration Guide

### From requests

```python
# Old (requests)
import requests
response = requests.get("https://api.example.com/data", 
                       headers={"Authorization": "Bearer token"})
data = response.json()

# New (AsyncHTTPClient)
async with AsyncHTTPClient("https://api.example.com", "token") as client:
    data = await client.get("/data")
```

### From httpx directly

```python
# Old (raw httpx)
async with httpx.AsyncClient() as client:
    response = await client.get(
        "https://api.example.com/data",
        headers={"Authorization": "Bearer token"}
    )
    data = response.json()

# New (AsyncHTTPClient)
async with AsyncHTTPClient("https://api.example.com", "token") as client:
    data = await client.get("/data")
```

## Performance Considerations

- **Connection Pooling**: httpx automatically pools connections
- **Keep-Alive**: Connections are reused for multiple requests
- **Rate Limiting**: Prevents overwhelming target servers
- **Async/Await**: Non-blocking I/O for better concurrency
- **Structured Logging**: Minimal performance impact with proper configuration

## Troubleshooting

### Common Issues

1. **"externally-managed-environment" error**: Install in virtual environment
2. **Rate limiting too aggressive**: Adjust `rate_limit_requests_per_second`
3. **Timeout errors**: Increase `timeout` parameter
4. **SSL errors**: Set `verify_ssl=False` (not recommended for production)
5. **Token auth not working**: Ensure token format matches API requirements

### Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed httpx logs including request/response details
```

## Examples

See `examples/http_client_example.py` for comprehensive usage examples.

## API Reference

For detailed API documentation, see the docstrings in:
- `mcp_mattermost.api.client.AsyncHTTPClient`
- `mcp_mattermost.api.exceptions`
