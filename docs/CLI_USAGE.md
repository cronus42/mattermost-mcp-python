# CLI Usage Guide

This document describes the command-line interface for the Mattermost MCP Server.

## Basic Usage

The server can be started using Python's module execution:

```bash
python -m mcp_mattermost
```

## Configuration

The server supports configuration through both environment variables and command-line arguments. Command-line arguments take precedence over environment variables.

### Required Configuration

Two configuration values are required:

- **Mattermost URL**: The base URL of your Mattermost instance
- **API Token**: A valid Mattermost API token for authentication

These can be provided via:
- Environment variables: `MATTERMOST_URL` and `MATTERMOST_TOKEN`
- Command-line arguments: `--mattermost-url` and `--mattermost-token`

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MATTERMOST_URL` | Mattermost server URL | *Required* |
| `MATTERMOST_TOKEN` | API authentication token | *Required* |
| `MATTERMOST_TEAM_ID` | Team ID (optional) | None |
| `WEBHOOK_SECRET` | Webhook validation secret | None |
| `WS_URL` | Custom WebSocket URL | None |
| `DEFAULT_CHANNEL` | Default channel ID | None |
| `MCP_SERVER_HOST` | Server host | `localhost` |
| `MCP_SERVER_PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Logging format (`console` or `json`) | `console` |

### Command-Line Arguments

```
usage: __main__.py [-h] [--mattermost-url MATTERMOST_URL]
                   [--mattermost-token MATTERMOST_TOKEN] [--team-id TEAM_ID]
                   [--webhook-secret WEBHOOK_SECRET] [--ws-url WS_URL]
                   [--default-channel DEFAULT_CHANNEL] [--host HOST] [--port PORT]
                   [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                   [--log-format {console,json}] [--no-streaming] [--no-polling]
                   [--polling-interval POLLING_INTERVAL]

Mattermost MCP Server

options:
  -h, --help            show this help message and exit
  --mattermost-url MATTERMOST_URL
                        Mattermost server URL (overrides MATTERMOST_URL env var)
  --mattermost-token MATTERMOST_TOKEN
                        Mattermost API token (overrides MATTERMOST_TOKEN env var)
  --team-id TEAM_ID     Mattermost team ID (overrides MATTERMOST_TEAM_ID env var)
  --webhook-secret WEBHOOK_SECRET
                        Webhook secret for validation (overrides WEBHOOK_SECRET env var)
  --ws-url WS_URL       WebSocket URL (overrides WS_URL env var)
  --default-channel DEFAULT_CHANNEL
                        Default channel ID (overrides DEFAULT_CHANNEL env var)
  --host HOST           Server host (overrides MCP_SERVER_HOST env var)
  --port PORT           Server port (overrides MCP_SERVER_PORT env var)
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (overrides LOG_LEVEL env var)
  --log-format {console,json}
                        Logging format (overrides LOG_FORMAT env var)
  --no-streaming        Disable WebSocket streaming
  --no-polling          Disable REST API polling
  --polling-interval POLLING_INTERVAL
                        Polling interval in seconds (default: 30.0)
```

## Usage Examples

### Basic Usage with Environment Variables

Set up your environment:

```bash
export MATTERMOST_URL="https://mattermost.example.com"
export MATTERMOST_TOKEN="your-api-token"
```

Start the server:

```bash
python -m mcp_mattermost
```

### Override Configuration with CLI Arguments

```bash
python -m mcp_mattermost \
  --mattermost-url "https://chat.company.com" \
  --mattermost-token "your-token" \
  --team-id "engineering-team" \
  --default-channel "general"
```

### Configure Webhook Settings

```bash
python -m mcp_mattermost \
  --webhook-secret "your-webhook-secret" \
  --ws-url "wss://custom-websocket.example.com/api/v4/websocket"
```

### Adjust Server and Logging Configuration

```bash
python -m mcp_mattermost \
  --host "0.0.0.0" \
  --port 3000 \
  --log-level DEBUG \
  --log-format json
```

### Streaming and Polling Configuration

Disable WebSocket streaming, use only REST polling:

```bash
python -m mcp_mattermost \
  --no-streaming \
  --polling-interval 60.0
```

Use only WebSocket streaming, disable REST polling:

```bash
python -m mcp_mattermost --no-polling
```

### Complete Configuration Example

```bash
python -m mcp_mattermost \
  --mattermost-url "https://chat.company.com" \
  --mattermost-token "your-api-token" \
  --team-id "engineering-team" \
  --webhook-secret "webhook-validation-secret" \
  --ws-url "wss://chat.company.com/api/v4/websocket" \
  --default-channel "alerts" \
  --host "127.0.0.1" \
  --port 8080 \
  --log-level INFO \
  --log-format console \
  --polling-interval 45.0
```

## New Configuration Features

### Webhook Secret (`WEBHOOK_SECRET`)

The webhook secret is used for validating incoming webhook requests. When set, the server will validate the webhook signature to ensure requests are authentic.

**Usage:**
- Environment: `WEBHOOK_SECRET=your-secret-key`
- CLI: `--webhook-secret your-secret-key`

### Custom WebSocket URL (`WS_URL`)

By default, the WebSocket URL is derived from the Mattermost URL. This option allows you to specify a custom WebSocket endpoint.

**Usage:**
- Environment: `WS_URL=wss://custom-websocket.example.com/api/v4/websocket`
- CLI: `--ws-url wss://custom-websocket.example.com/api/v4/websocket`

### Default Channel (`DEFAULT_CHANNEL`)

Specifies a default channel ID to use when no specific channel is provided for operations.

**Usage:**
- Environment: `DEFAULT_CHANNEL=channel-id-here`
- CLI: `--default-channel channel-id-here`

## Configuration Priority

Configuration values are resolved in the following order (highest to lowest priority):

1. Command-line arguments
2. Environment variables
3. Default values

## Error Handling

The server will exit with an error if:
- Required configuration (`MATTERMOST_URL` and `MATTERMOST_TOKEN`) is missing
- Invalid argument values are provided
- The server fails to start due to configuration issues

## Logging

The server uses structured logging with two formats:

- **Console format** (default): Human-readable output for development
- **JSON format**: Machine-readable output for production logging systems

Log levels available: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## Signal Handling

The server gracefully handles shutdown signals:
- **Ctrl+C (SIGINT)**: Graceful shutdown
- The server will clean up resources and close connections before exiting

## Examples Script

For more examples, see the included examples script:

```bash
python examples/cli_usage_example.py
```

This script demonstrates various configuration patterns and use cases without actually starting the server.
