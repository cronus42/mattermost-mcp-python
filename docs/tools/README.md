# 🛠️ MCP Tool Catalog

Complete reference for all available MCP tools in Mattermost MCP Python.

## Tool Categories

- 💬 **[Messaging Tools](#messaging-tools)** - Send messages, replies, reactions
- 🏗️ **[Channel Tools](#channel-tools)** - Manage channels and memberships
- 👥 **[User Tools](#user-tools)** - User management and profiles
- 📁 **[File Tools](#file-tools)** - File operations and attachments
- ⚙️ **[Admin Tools](#admin-tools)** - System administration
- 📊 **[Monitoring Tools](#monitoring-tools)** - Health checks and metrics

## Quick Reference

| Tool | Purpose | Required Parameters |
|------|---------|-------------------|
| `send_message` | Send message to channel | `channel_id`, `message` |
| `reply_to_thread` | Reply to a thread | `root_post_id`, `message` |
| `get_channel_history` | Get channel messages | `channel_id` |
| `add_reaction` | Add emoji reaction | `post_id`, `emoji_name`, `user_id` |
| `list_channels` | List team channels | `team_id` |
| `create_channel` | Create new channel | `team_id`, `name`, `display_name` |
| `get_channel` | Get channel info | `channel_id` or `team_id`+`channel_name` |
| `add_user_to_channel` | Add user to channel | `channel_id`, `user_id` |
| `search_channels` | Search for channels | `team_id`, `term` |

---

## 💬 Messaging Tools

### send_message

Send a message to a channel or direct message.

**Parameters:**
- `channel_id` (required): Target channel ID
- `message` (required): Message text
- `root_id` (optional): Root post ID for threading
- `file_ids` (optional): Array of file attachment IDs
- `props` (optional): Additional post properties

**Example:**
```json
{
  "tool": "send_message",
  "arguments": {
    "channel_id": "4yca9c7c3jbg5rqwx8xbwxxx",
    "message": "Hello team! 👋",
    "props": {
      "priority": "high"
    }
  }
}
```

**Response:**
```json
{
  "post_id": "abc123post456",
  "channel_id": "4yca9c7c3jbg5rqwx8xbwxxx",
  "message": "Hello team! 👋",
  "create_at": 1642678800000,
  "user_id": "bot_user_id",
  "type": "",
  "props": {
    "priority": "high"
  }
}
```

### reply_to_thread

Reply to an existing thread.

**Parameters:**
- `root_post_id` (required): Root post ID to reply to
- `message` (required): Reply message text
- `file_ids` (optional): File attachments
- `props` (optional): Additional properties

**Example:**
```json
{
  "tool": "reply_to_thread",
  "arguments": {
    "root_post_id": "original_post_123",
    "message": "Great point! I agree with this approach."
  }
}
```

### get_channel_history

Retrieve message history for a channel.

**Parameters:**
- `channel_id` (required): Channel to get history from
- `page` (optional): Page number (default: 0)
- `per_page` (optional): Messages per page (default: 60)
- `since` (optional): Timestamp to get messages since
- `before` (optional): Get messages before this post ID
- `after` (optional): Get messages after this post ID

**Example:**
```json
{
  "tool": "get_channel_history",
  "arguments": {
    "channel_id": "4yca9c7c3jbg5rqwx8xbwxxx",
    "per_page": 20,
    "since": 1642678800000
  }
}
```

### add_reaction

Add an emoji reaction to a message.

**Parameters:**
- `post_id` (required): Post to react to
- `emoji_name` (required): Emoji name (without colons)
- `user_id` (required): User adding the reaction

**Example:**
```json
{
  "tool": "add_reaction",
  "arguments": {
    "post_id": "post_abc123",
    "emoji_name": "thumbsup",
    "user_id": "user_xyz789"
  }
}
```

### remove_reaction

Remove an emoji reaction from a message.

**Parameters:**
- `post_id` (required): Post to remove reaction from
- `emoji_name` (required): Emoji name to remove
- `user_id` (required): User removing the reaction

### update_message

Update/edit an existing message.

**Parameters:**
- `post_id` (required): Post ID to update
- `message` (optional): New message text
- `file_ids` (optional): Updated file attachments
- `props` (optional): Updated properties

### delete_message

Delete a message.

**Parameters:**
- `post_id` (required): Post ID to delete

### get_thread

Get complete thread of messages.

**Parameters:**
- `root_post_id` (required): Root post ID of the thread

### pin_message / unpin_message

Pin or unpin a message to/from its channel.

**Parameters:**
- `post_id` (required): Post ID to pin/unpin

---

## 🏗️ Channel Tools

### list_channels

List all channels for a team.

**Parameters:**
- `team_id` (required): Team to list channels for
- `page` (optional): Page number (default: 0)
- `per_page` (optional): Channels per page (default: 60)
- `include_deleted` (optional): Include deleted channels (default: false)
- `public_only` (optional): Only public channels (default: false)

**Example:**
```json
{
  "tool": "list_channels",
  "arguments": {
    "team_id": "team123abc456",
    "per_page": 50,
    "public_only": true
  }
}
```

### get_channel

Get information about a specific channel.

**Parameters:**
- `channel_id`: Channel ID (for ID lookup)
- `team_id` + `channel_name`: Team ID and channel name (for name lookup)

**Example:**
```json
{
  "tool": "get_channel",
  "arguments": {
    "team_id": "team123abc456",
    "channel_name": "general"
  }
}
```

### create_channel

Create a new channel.

**Parameters:**
- `team_id` (required): Team to create channel in
- `name` (required): Channel name (URL-friendly)
- `display_name` (required): Display name
- `type` (optional): Channel type - "O" (Open), "P" (Private), default: "O"
- `purpose` (optional): Channel purpose
- `header` (optional): Channel header

**Example:**
```json
{
  "tool": "create_channel",
  "arguments": {
    "team_id": "team123abc456",
    "name": "project-alpha",
    "display_name": "Project Alpha",
    "type": "P",
    "purpose": "Discussion for Project Alpha development",
    "header": "📁 Project Alpha - Confidential"
  }
}
```

### update_channel

Update channel information.

**Parameters:**
- `channel_id` (required): Channel to update
- `display_name` (optional): New display name
- `purpose` (optional): New purpose
- `header` (optional): New header

### delete_channel

Delete a channel.

**Parameters:**
- `channel_id` (required): Channel to delete

### search_channels

Search for channels in a team.

**Parameters:**
- `team_id` (required): Team to search in
- `term` (required): Search term

### add_user_to_channel

Add a user to a channel.

**Parameters:**
- `channel_id` (required): Target channel
- `user_id` (required): User to add

**Example:**
```json
{
  "tool": "add_user_to_channel",
  "arguments": {
    "channel_id": "channel_abc123",
    "user_id": "user_xyz789"
  }
}
```

### remove_user_from_channel

Remove a user from a channel.

**Parameters:**
- `channel_id` (required): Target channel
- `user_id` (required): User to remove

### get_channel_members

Get list of channel members.

**Parameters:**
- `channel_id` (required): Channel to get members for
- `page` (optional): Page number (default: 0)
- `per_page` (optional): Members per page (default: 60)

### get_channel_stats

Get channel statistics.

**Parameters:**
- `channel_id` (required): Channel to get stats for

**Response:**
```json
{
  "channel_id": "channel_abc123",
  "member_count": 15,
  "guest_count": 2,
  "pinned_post_count": 3
}
```

---

## 👥 User Tools

### get_user

Get user information.

**Parameters:**
- `user_id` (required): User ID to get info for

### get_me

Get current bot user information.

**Parameters:** None

### search_users

Search for users.

**Parameters:**
- `term` (required): Search term
- `team_id` (optional): Limit search to team
- `in_channel_id` (optional): Limit to channel members
- `not_in_channel_id` (optional): Exclude channel members

### get_user_status

Get user's current status.

**Parameters:**
- `user_id` (required): User to get status for

### get_users_by_ids

Get multiple users by their IDs.

**Parameters:**
- `user_ids` (required): Array of user IDs

---

## 📁 File Tools

### upload_file

Upload a file attachment.

**Parameters:**
- `channel_id` (required): Channel for file context
- `file_data` (required): Base64 encoded file data
- `filename` (required): Original filename

### get_file_info

Get file metadata.

**Parameters:**
- `file_id` (required): File ID

### download_file

Download file content.

**Parameters:**
- `file_id` (required): File ID

### get_file_thumbnail

Get file thumbnail (for images).

**Parameters:**
- `file_id` (required): File ID

### get_file_preview

Get file preview (for images and documents).

**Parameters:**
- `file_id` (required): File ID

---

## ⚙️ Admin Tools

### get_server_status

Get server status information.

**Parameters:** None

### get_system_stats

Get system statistics.

**Parameters:** None

### get_server_config

Get server configuration (admin only).

**Parameters:** None

---

## 📊 Monitoring Tools

### health_check

Check system health.

**Parameters:** None

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "mattermost_api": "ok",
    "websocket": "ok",
    "database": "ok"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### get_metrics

Get system metrics.

**Parameters:** None

### get_logs

Get application logs (admin only).

**Parameters:**
- `level` (optional): Log level filter
- `limit` (optional): Number of log entries
- `since` (optional): Get logs since timestamp

---

## Error Handling

All tools follow consistent error response format:

```json
{
  "error": {
    "code": "INVALID_CHANNEL",
    "message": "Channel not found or access denied",
    "details": {
      "channel_id": "invalid_channel_123",
      "correlation_id": "req-abc123"
    }
  }
}
```

### Common Error Codes

- `AUTHENTICATION_ERROR`: Invalid or expired token
- `PERMISSION_DENIED`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `RATE_LIMITED`: Too many requests
- `INVALID_INPUT`: Invalid parameters
- `SERVER_ERROR`: Internal server error
- `MATTERMOST_ERROR`: Mattermost API error

## Usage Examples

### Python Client Example

```python
import asyncio
from mcp_client import MCPClient

async def send_daily_report():
    async with MCPClient("http://localhost:3000") as client:
        # Send message to general channel
        await client.call_tool("send_message", {
            "channel_id": "general_channel_id",
            "message": "📊 Daily standup starting in 5 minutes!"
        })

        # Get recent channel activity
        history = await client.call_tool("get_channel_history", {
            "channel_id": "general_channel_id",
            "per_page": 10
        })

        # React to important messages
        for post in history["posts"][:3]:
            await client.call_tool("add_reaction", {
                "post_id": post["post_id"],
                "emoji_name": "eyes",
                "user_id": "bot_user_id"
            })

asyncio.run(send_daily_report())
```

### curl Examples

```bash
# Send a message
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "send_message",
      "arguments": {
        "channel_id": "channel123",
        "message": "Hello from curl!"
      }
    }
  }'

# List channels
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_channels",
      "arguments": {
        "team_id": "team456"
      }
    }
  }'
```

## Best Practices

1. **Error Handling**: Always handle errors gracefully
2. **Rate Limiting**: Respect API rate limits
3. **Batch Operations**: Use bulk operations when available
4. **Caching**: Cache frequently accessed data
5. **Logging**: Include correlation IDs for tracing
6. **Validation**: Validate inputs before tool calls
7. **Permissions**: Check user permissions before operations
8. **Testing**: Test tools in development environment first

## Tool Development

Want to add custom tools? See the [Development Guide](../development.md#custom-tools) for details on extending the tool catalog.
