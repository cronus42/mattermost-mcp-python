# 📚 Usage Examples

Practical examples demonstrating how to use Mattermost MCP Python in various scenarios.

## Example Categories

### 🏃‍♂️ **Getting Started**
- [Basic Usage](basic-usage.md) - Simple messaging and channel operations
- [Authentication Setup](authentication.md) - Setting up bot tokens and permissions
- [First Integration](first-integration.md) - Building your first MCP client

### 🤖 **Bot Development**
- [Chatbot Example](chatbot.md) - Building a conversational bot
- [Notification Bot](notification-bot.md) - Automated notifications and alerts
- [Workflow Automation](workflow-automation.md) - Process automation with Mattermost

### 🔄 **Real-time Integration**
- [WebSocket Streaming](websocket-streaming.md) - Real-time event handling
- [Live Monitoring](live-monitoring.md) - Channel activity monitoring
- [Event Processing](event-processing.md) - Advanced event handling patterns

### 🏗️ **Advanced Use Cases**
- [Multi-team Management](multi-team.md) - Managing multiple teams
- [File Processing](file-processing.md) - Handling file uploads and attachments
- [Custom Commands](custom-commands.md) - Building slash command integrations
- [Integration Patterns](integration-patterns.md) - Common integration architectures

### 🛠️ **Development & Testing**
- [Testing Strategies](testing.md) - Unit and integration testing
- [Local Development](local-development.md) - Development environment setup
- [Debugging Tips](debugging.md) - Common issues and solutions

### 📊 **Monitoring & Observability**
- [Health Monitoring](health-monitoring.md) - System health checks
- [Metrics Collection](metrics.md) - Performance and usage metrics
- [Log Analysis](logging.md) - Structured logging and analysis

## Quick Examples

### Send a Simple Message

```python
import asyncio
from mcp_client import MCPClient

async def send_hello():
    async with MCPClient("http://localhost:3000") as client:
        result = await client.call_tool("send_message", {
            "channel_id": "your-channel-id",
            "message": "Hello, Mattermost! 👋"
        })
        print(f"Message sent with ID: {result['post_id']}")

asyncio.run(send_hello())
```

### Create a Channel and Add Users

```python
async def setup_project_channel():
    async with MCPClient("http://localhost:3000") as client:
        # Create channel
        channel = await client.call_tool("create_channel", {
            "team_id": "your-team-id",
            "name": "project-alpha",
            "display_name": "Project Alpha",
            "type": "P",  # Private channel
            "purpose": "Project Alpha development discussions"
        })

        channel_id = channel["channel_id"]

        # Add team members
        user_ids = ["user1", "user2", "user3"]
        for user_id in user_ids:
            await client.call_tool("add_user_to_channel", {
                "channel_id": channel_id,
                "user_id": user_id
            })

        # Send welcome message
        await client.call_tool("send_message", {
            "channel_id": channel_id,
            "message": "🎉 Welcome to Project Alpha! Let's build something amazing."
        })

        return channel_id
```

### Monitor Channel Activity

```python
async def monitor_channel():
    async with MCPClient("http://localhost:3000") as client:
        # Get recent activity
        history = await client.call_tool("get_channel_history", {
            "channel_id": "your-channel-id",
            "per_page": 10
        })

        # React to messages containing "help"
        for post in history["posts"]:
            if "help" in post["message"].lower():
                await client.call_tool("add_reaction", {
                    "post_id": post["post_id"],
                    "emoji_name": "question",
                    "user_id": "bot-user-id"
                })

                # Reply with helpful information
                await client.call_tool("reply_to_thread", {
                    "root_post_id": post["post_id"],
                    "message": "I see you need help! Check our documentation or ping @support"
                })
```

### File Upload Example

```python
import base64

async def upload_and_share_file():
    async with MCPClient("http://localhost:3000") as client:
        # Read and encode file
        with open("report.pdf", "rb") as f:
            file_data = base64.b64encode(f.read()).decode()

        # Upload file
        file_info = await client.call_tool("upload_file", {
            "channel_id": "your-channel-id",
            "file_data": file_data,
            "filename": "monthly_report.pdf"
        })

        # Share file with message
        await client.call_tool("send_message", {
            "channel_id": "your-channel-id",
            "message": "📊 Here's the monthly report!",
            "file_ids": [file_info["file_id"]]
        })
```

### Error Handling Example

```python
from mcp_client import MCPClient, MCPError

async def robust_messaging():
    try:
        async with MCPClient("http://localhost:3000") as client:
            result = await client.call_tool("send_message", {
                "channel_id": "invalid-channel",
                "message": "This will fail"
            })
    except MCPError as e:
        if e.code == "NOT_FOUND":
            print("Channel not found, creating it first...")
            # Handle channel creation
        elif e.code == "PERMISSION_DENIED":
            print("No permission to send messages")
        else:
            print(f"Unexpected error: {e}")
```

## Language Examples

### JavaScript/Node.js

```javascript
const { MCPClient } = require('mcp-client');

async function sendMessage() {
    const client = new MCPClient('http://localhost:3000');

    try {
        const result = await client.callTool('send_message', {
            channel_id: 'your-channel-id',
            message: 'Hello from JavaScript!'
        });
        console.log('Message sent:', result.post_id);
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await client.close();
    }
}

sendMessage();
```

### curl/HTTP Examples

```bash
# Send message
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "send_message",
      "arguments": {
        "channel_id": "your-channel-id",
        "message": "Hello from curl!"
      }
    }
  }'

# Get channel list
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_channels",
      "arguments": {
        "team_id": "your-team-id"
      }
    }
  }'
```

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI
from mcp_client import MCPClient

app = FastAPI()

@app.post("/webhook/mattermost")
async def handle_webhook(payload: dict):
    async with MCPClient("http://localhost:3000") as client:
        if payload.get("event") == "post_created":
            # React to new posts
            await client.call_tool("add_reaction", {
                "post_id": payload["post"]["id"],
                "emoji_name": "thumbsup",
                "user_id": "bot-user-id"
            })

    return {"status": "ok"}
```

### Flask Integration

```python
from flask import Flask, request
import asyncio
from mcp_client import MCPClient

app = Flask(__name__)

@app.route('/send-notification', methods=['POST'])
def send_notification():
    data = request.json
    message = data.get('message', 'No message provided')
    channel_id = data.get('channel_id')

    async def send():
        async with MCPClient("http://localhost:3000") as client:
            return await client.call_tool("send_message", {
                "channel_id": channel_id,
                "message": f"🔔 Notification: {message}"
            })

    result = asyncio.run(send())
    return {"success": True, "post_id": result["post_id"]}
```

### GitHub Actions Integration

```yaml
name: Deploy Notification
on:
  deployment_status:
    branches: [main]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Notify Mattermost
        run: |
          curl -X POST ${{ secrets.MCP_SERVER_URL }}/mcp \
            -H "Content-Type: application/json" \
            -d '{
              "method": "tools/call",
              "params": {
                "name": "send_message",
                "arguments": {
                  "channel_id": "${{ secrets.DEPLOY_CHANNEL_ID }}",
                  "message": "🚀 Deployment completed successfully!"
                }
              }
            }'
```

## Common Patterns

### Batch Operations

```python
async def process_multiple_channels():
    async with MCPClient("http://localhost:3000") as client:
        # Get all channels
        channels = await client.call_tool("list_channels", {
            "team_id": "your-team-id"
        })

        # Send announcement to all channels
        message = "📢 Important announcement: System maintenance tonight at 10 PM"

        for channel in channels["channels"]:
            if channel["type"] == "O":  # Only public channels
                try:
                    await client.call_tool("send_message", {
                        "channel_id": channel["channel_id"],
                        "message": message
                    })
                except Exception as e:
                    print(f"Failed to send to {channel['name']}: {e}")
```

### Rate Limiting

```python
import asyncio

async def send_with_rate_limit(messages, delay=1.0):
    async with MCPClient("http://localhost:3000") as client:
        for message in messages:
            try:
                await client.call_tool("send_message", message)
                await asyncio.sleep(delay)  # Rate limiting
            except Exception as e:
                print(f"Error sending message: {e}")
```

## Next Steps

- Browse detailed examples in each category
- Try the [Basic Usage](basic-usage.md) examples first
- Check out [Real-time Integration](websocket-streaming.md) for advanced features
- See [Testing Strategies](testing.md) for development best practices

## Contributing Examples

Have a useful example? We'd love to include it! Please:

1. Create a new markdown file in the appropriate category
2. Include complete, working code examples
3. Add clear explanations and comments
4. Test your examples before submitting
5. Submit a pull request

See [Contributing Guidelines](../../CONTRIBUTING.md) for more details.
