# Streaming/Polling MCP Resources

This document describes the streaming and polling capabilities of the Mattermost MCP Python implementation.

## Overview

The Mattermost MCP server provides real-time resource providers that can emit updates through two mechanisms:

1. **WebSocket Streaming**: Real-time events via Mattermost's WebSocket API
2. **REST Polling**: Periodic polling of REST APIs as a fallback mechanism

## Supported Resources

### 1. New Channel Posts (`mattermost://new_channel_posts`)

Provides real-time updates for new posts in Mattermost channels.

**Features:**
- ✅ WebSocket streaming via `posted` events
- ✅ REST API polling with timestamp tracking
- 🎯 Channel filtering (monitor specific channels or all channels)
- 🏢 Team scoping (monitor channels within a specific team)

**WebSocket Events:**
- `posted` - Triggered when a new post is created

**Update Types:**
- `created` - New post was created

### 2. Reactions (`mattermost://reactions`)

Provides real-time updates for emoji reactions being added or removed.

**Features:**
- ✅ WebSocket streaming via `reaction_added`/`reaction_removed` events
- ✅ REST API polling with state comparison
- 🎯 Channel filtering (monitor specific channels or all channels)
- 🏢 Team scoping (monitor channels within a specific team)

**WebSocket Events:**
- `reaction_added` - Triggered when a reaction is added to a post
- `reaction_removed` - Triggered when a reaction is removed from a post

**Update Types:**
- `reaction_added` - New reaction was added
- `reaction_removed` - Existing reaction was removed

## Architecture

### Base Resource Classes

#### `BaseMCPResource`
Abstract base class providing streaming/polling infrastructure:
- Subscriber management
- Update emission
- Streaming lifecycle management
- Polling loop with error handling

#### `MCPResourceRegistry`
Manages multiple resources and their lifecycle:
- Resource registration/discovery
- Batch streaming/polling control
- Cleanup and error handling

### WebSocket Integration

#### `MattermostWebSocketClient`
Handles real-time WebSocket connection to Mattermost:
- Authentication via token
- Auto-reconnection with exponential backoff
- Event filtering and routing
- Connection state management

## Usage Examples

### Basic Setup

```python
from mcp_mattermost.server import MattermostMCPServer
from mcp_mattermost.resources import ResourceUpdate

def handle_update(update: ResourceUpdate):
    print(f"Update: {update.update_type} on {update.resource_uri}")
    print(f"Data: {update.data}")

server = MattermostMCPServer(
    mattermost_url="https://your-mattermost.com",
    mattermost_token="your-token",
    team_id="your-team-id",  # Optional
    enable_streaming=True,   # Enable WebSocket
    enable_polling=True,     # Enable REST polling fallback
    polling_interval=30.0,   # Poll every 30 seconds
)

server.set_resource_update_callback(handle_update)
await server.start()
```

### Channel-Specific Monitoring

```python
# Monitor only specific channels
server = MattermostMCPServer(
    mattermost_url="https://your-mattermost.com",
    mattermost_token="your-token",
    channel_ids=["channel1", "channel2", "channel3"],
    enable_streaming=True,
)
```

### Polling-Only Mode

```python
# Use only REST polling (no WebSocket)
server = MattermostMCPServer(
    mattermost_url="https://your-mattermost.com",
    mattermost_token="your-token",
    enable_streaming=False,  # Disable WebSocket
    enable_polling=True,     # Use only polling
    polling_interval=15.0,   # Poll every 15 seconds
)
```

## Configuration Options

### Server Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mattermost_url` | str | Required | Mattermost server URL |
| `mattermost_token` | str | Required | API authentication token |
| `team_id` | str | None | Optional team ID to scope operations |
| `enable_streaming` | bool | True | Enable WebSocket streaming |
| `enable_polling` | bool | True | Enable REST API polling |
| `polling_interval` | float | 30.0 | Polling interval in seconds |
| `channel_ids` | List[str] | None | List of channel IDs to monitor |

### WebSocket Client Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `auto_reconnect` | bool | True | Auto-reconnect on disconnection |
| `reconnect_delay` | float | 5.0 | Base delay between reconnection attempts |
| `max_reconnect_attempts` | int | 10 | Maximum reconnection attempts |

## Resource Update Format

### ResourceUpdate Object

```python
@dataclass
class ResourceUpdate:
    resource_uri: str        # e.g., "mattermost://new_channel_posts"
    update_type: str         # "created", "reaction_added", etc.
    data: Dict[str, Any]     # Update-specific data
    timestamp: float         # Unix timestamp
    event_id: str           # Unique event identifier
```

### New Post Update

```json
{
  "resource_uri": "mattermost://new_channel_posts",
  "update_type": "created",
  "data": {
    "post": {
      "id": "post-id",
      "user_id": "user-id",
      "channel_id": "channel-id",
      "message": "Hello world!",
      "create_at": 1672531200000
    },
    "channel_id": "channel-id",
    "user_id": "user-id"
  },
  "timestamp": 1672531200.123,
  "event_id": "post_post-id"
}
```

### Reaction Update

```json
{
  "resource_uri": "mattermost://reactions",
  "update_type": "reaction_added",
  "data": {
    "reaction": {
      "user_id": "user-id",
      "post_id": "post-id",
      "emoji_name": "thumbsup",
      "create_at": 1672531200000
    },
    "post_id": "post-id",
    "user_id": "user-id",
    "emoji_name": "thumbsup",
    "channel_id": "channel-id"
  },
  "timestamp": 1672531200.456,
  "event_id": "reaction_post-id_user-id_thumbsup"
}
```

## Error Handling

### Streaming Failures
- WebSocket disconnections trigger auto-reconnect with exponential backoff
- If WebSocket fails and polling is disabled, the server startup will fail
- Individual resource streaming failures don't affect other resources

### Polling Failures
- Failed poll attempts are logged and retried on next interval
- Individual channel polling failures don't stop other channels
- Exponential backoff on consecutive failures

### Resource State
- Resources maintain state for polling (e.g., last post timestamps)
- State is reset on resource restart
- Failed API calls are logged but don't crash the resource

## Performance Considerations

### WebSocket vs Polling
- **WebSocket**: Real-time updates, efficient for active channels
- **Polling**: Higher latency, more API calls, good for fallback

### Rate Limiting
- WebSocket events respect Mattermost's rate limits
- Polling intervals should account for API rate limits
- HTTP client includes automatic retry logic

### Memory Usage
- Resources track minimal state (timestamps, reaction sets)
- Large channel histories are paginated
- Old events are not stored permanently

## Troubleshooting

### Common Issues

1. **WebSocket Authentication Fails**
   - Check token validity and permissions
   - Ensure WebSocket endpoint is accessible
   - Verify Mattermost version supports WebSocket API

2. **No Updates Received**
   - Check channel permissions (must have read access)
   - Verify team_id/channel_ids configuration
   - Enable debug logging to see WebSocket events

3. **High API Usage**
   - Increase polling intervals
   - Use channel filtering to reduce scope
   - Monitor Mattermost API rate limits

### Debug Logging

```python
import structlog

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(10),  # DEBUG level
    logger_factory=structlog.PrintLoggerFactory(),
)
```

### Environment Variables

For the example script:

```bash
export MATTERMOST_URL="https://your-mattermost.com"
export MATTERMOST_TOKEN="your-personal-access-token"
export MATTERMOST_TEAM_ID="your-team-id"  # Optional
export MATTERMOST_CHANNEL_IDS="channel1,channel2"  # Optional
```

## Security Considerations

- **Token Security**: Use environment variables, never hardcode tokens
- **Permissions**: Resources respect Mattermost channel permissions
- **Network**: WebSocket connections support SSL/TLS
- **Logging**: Sensitive data is not logged at INFO level

## Future Enhancements

Potential improvements for streaming resources:

- **User Status Updates**: Real-time user presence/status changes
- **Channel Membership**: Users joining/leaving channels
- **File Uploads**: New file attachments
- **Direct Messages**: Private message updates
- **Typing Indicators**: Real-time typing notifications
- **Post Edits/Deletions**: Post modification events
