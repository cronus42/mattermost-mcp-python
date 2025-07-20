# 🏃‍♂️ Basic Usage Examples

This guide provides simple, practical examples to get you started with Mattermost MCP Python.

## Prerequisites

- MCP Mattermost server running (see [Quick Start](../quickstart.md))
- Valid Mattermost bot token
- Python 3.8+ with `asyncio` support

## Installation

```bash
pip install mcp-client  # Generic MCP client
# Or use any MCP-compatible client
```

## Basic Examples

### 1. Send Your First Message

```python
import asyncio
from mcp_client import MCPClient

async def send_first_message():
    """Send a simple message to a channel."""
    async with MCPClient("http://localhost:3000") as client:
        result = await client.call_tool("send_message", {
            "channel_id": "your-channel-id",  # Replace with actual channel ID
            "message": "Hello, World! This is my first MCP message 🎉"
        })
        
        print(f"✅ Message sent successfully!")
        print(f"📝 Post ID: {result['post_id']}")
        print(f"📅 Created at: {result['create_at']}")

# Run the example
asyncio.run(send_first_message())
```

**Expected Output:**
```
✅ Message sent successfully!
📝 Post ID: abc123def456
📅 Created at: 1642678800000
```

### 2. List Available Channels

```python
async def list_my_channels():
    """Get a list of all channels in a team."""
    async with MCPClient("http://localhost:3000") as client:
        channels = await client.call_tool("list_channels", {
            "team_id": "your-team-id",  # Replace with actual team ID
            "per_page": 20
        })
        
        print(f"📋 Found {len(channels['channels'])} channels:")
        
        for channel in channels["channels"]:
            channel_type = "🔒 Private" if channel["type"] == "P" else "🌐 Public"
            print(f"  {channel_type} {channel['display_name']} ({channel['name']})")
            print(f"    └── ID: {channel['channel_id']}")
            print(f"    └── Members: {channel.get('total_msg_count', 'N/A')} messages")

asyncio.run(list_my_channels())
```

**Expected Output:**
```
📋 Found 5 channels:
  🌐 Public General (general)
    └── ID: 4yca9c7c3jbg5rqwx8xbwxxx
    └── Members: 1,234 messages
  🔒 Private Development (development)
    └── ID: 5zdb8d8d4kcg6sryx9ycwyyy
    └── Members: 567 messages
```

### 3. Get Channel History

```python
async def read_channel_history():
    """Read recent messages from a channel."""
    async with MCPClient("http://localhost:3000") as client:
        history = await client.call_tool("get_channel_history", {
            "channel_id": "your-channel-id",
            "per_page": 5  # Get last 5 messages
        })
        
        print(f"📬 Recent messages in channel:")
        
        for post in history["posts"]:
            # Convert timestamp to readable format
            import datetime
            timestamp = datetime.datetime.fromtimestamp(post["create_at"] / 1000)
            
            print(f"  🕐 {timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"  👤 User: {post['user_id']}")
            print(f"  💬 Message: {post['message'][:100]}...")
            print(f"  📝 Post ID: {post['post_id']}")
            print("  " + "-" * 40)

asyncio.run(read_channel_history())
```

### 4. Create a New Channel

```python
async def create_project_channel():
    """Create a new channel for a project."""
    async with MCPClient("http://localhost:3000") as client:
        try:
            channel = await client.call_tool("create_channel", {
                "team_id": "your-team-id",
                "name": "my-new-project",  # URL-friendly name
                "display_name": "My New Project",  # Display name
                "type": "O",  # "O" = Open/Public, "P" = Private
                "purpose": "Discussion space for my awesome new project",
                "header": "🚀 Welcome to My New Project!"
            })
            
            print("✅ Channel created successfully!")
            print(f"📝 Channel ID: {channel['channel_id']}")
            print(f"🏷️ Channel Name: {channel['name']}")
            print(f"📺 Display Name: {channel['display_name']}")
            print(f"🔗 Channel URL: /channels/{channel['name']}")
            
            return channel["channel_id"]
            
        except Exception as e:
            print(f"❌ Failed to create channel: {e}")
            return None

# Create channel and store the ID
channel_id = asyncio.run(create_project_channel())
```

### 5. Add Users to a Channel

```python
async def invite_team_members():
    """Add multiple users to a channel."""
    channel_id = "your-channel-id"
    user_ids = [
        "user1-id-here",
        "user2-id-here", 
        "user3-id-here"
    ]
    
    async with MCPClient("http://localhost:3000") as client:
        successful_invites = []
        failed_invites = []
        
        for user_id in user_ids:
            try:
                await client.call_tool("add_user_to_channel", {
                    "channel_id": channel_id,
                    "user_id": user_id
                })
                successful_invites.append(user_id)
                print(f"✅ Added user {user_id}")
                
            except Exception as e:
                failed_invites.append((user_id, str(e)))
                print(f"❌ Failed to add user {user_id}: {e}")
        
        # Send welcome message if any users were added
        if successful_invites:
            welcome_msg = f"🎉 Welcome to the channel! Added {len(successful_invites)} new members."
            await client.call_tool("send_message", {
                "channel_id": channel_id,
                "message": welcome_msg
            })
            
        print(f"\n📊 Summary:")
        print(f"   ✅ Successfully added: {len(successful_invites)}")
        print(f"   ❌ Failed to add: {len(failed_invites)}")

asyncio.run(invite_team_members())
```

### 6. React to Messages

```python
async def add_reactions():
    """Add emoji reactions to messages."""
    async with MCPClient("http://localhost:3000") as client:
        # First, get recent messages
        history = await client.call_tool("get_channel_history", {
            "channel_id": "your-channel-id",
            "per_page": 3
        })
        
        bot_user_id = "your-bot-user-id"  # Replace with bot's user ID
        
        for post in history["posts"]:
            try:
                # Add different reactions based on content
                message = post["message"].lower()
                
                if "good" in message or "great" in message:
                    emoji = "thumbsup"
                elif "help" in message:
                    emoji = "question"
                elif "thanks" in message:
                    emoji = "heart"
                else:
                    emoji = "eyes"  # Default reaction
                
                await client.call_tool("add_reaction", {
                    "post_id": post["post_id"],
                    "emoji_name": emoji,
                    "user_id": bot_user_id
                })
                
                print(f"✅ Added :{emoji}: to message: '{post['message'][:50]}...'")
                
            except Exception as e:
                print(f"❌ Failed to add reaction: {e}")

asyncio.run(add_reactions())
```

### 7. Reply to Threads

```python
async def reply_to_messages():
    """Reply to recent messages to create threads."""
    async with MCPClient("http://localhost:3000") as client:
        # Get recent messages
        history = await client.call_tool("get_channel_history", {
            "channel_id": "your-channel-id",
            "per_page": 2
        })
        
        for post in history["posts"]:
            # Reply to posts that contain questions
            if "?" in post["message"]:
                try:
                    await client.call_tool("reply_to_thread", {
                        "root_post_id": post["post_id"],
                        "message": "🤖 I saw your question! Let me help you find an answer."
                    })
                    
                    print(f"✅ Replied to question: '{post['message'][:50]}...'")
                    
                except Exception as e:
                    print(f"❌ Failed to reply: {e}")

asyncio.run(reply_to_messages())
```

### 8. Search for Channels

```python
async def search_channels():
    """Search for channels by name or purpose."""
    async with MCPClient("http://localhost:3000") as client:
        try:
            results = await client.call_tool("search_channels", {
                "team_id": "your-team-id",
                "term": "development"  # Search term
            })
            
            print(f"🔍 Found {len(results['channels'])} channels matching 'development':")
            
            for channel in results["channels"]:
                print(f"  📺 {channel['display_name']}")
                print(f"    └── Name: {channel['name']}")
                print(f"    └── Purpose: {channel.get('purpose', 'No purpose set')}")
                print(f"    └── Type: {'Private' if channel['type'] == 'P' else 'Public'}")
                print()
                
        except Exception as e:
            print(f"❌ Search failed: {e}")

asyncio.run(search_channels())
```

## Error Handling Patterns

### Basic Error Handling

```python
async def robust_message_sending():
    """Example with proper error handling."""
    async with MCPClient("http://localhost:3000") as client:
        try:
            result = await client.call_tool("send_message", {
                "channel_id": "invalid-channel-id",
                "message": "This might fail"
            })
            print("✅ Message sent successfully")
            
        except Exception as e:
            # Handle specific error types
            error_message = str(e).lower()
            
            if "not found" in error_message:
                print("❌ Channel not found - please check the channel ID")
            elif "permission" in error_message:
                print("❌ Permission denied - bot may not have access to this channel")
            elif "rate limit" in error_message:
                print("❌ Rate limited - please wait before sending more messages")
            else:
                print(f"❌ Unexpected error: {e}")

asyncio.run(robust_message_sending())
```

### Retry Pattern

```python
import asyncio
import random

async def send_with_retry(channel_id, message, max_retries=3):
    """Send message with automatic retry on failure."""
    async with MCPClient("http://localhost:3000") as client:
        for attempt in range(max_retries):
            try:
                result = await client.call_tool("send_message", {
                    "channel_id": channel_id,
                    "message": message
                })
                print(f"✅ Message sent on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Wait with exponential backoff
                    wait_time = 2 ** attempt + random.uniform(0, 1)
                    print(f"⏰ Waiting {wait_time:.1f} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    print("❌ All retry attempts failed")
                    raise

# Usage
asyncio.run(send_with_retry("your-channel-id", "Hello with retry!"))
```

## Configuration Examples

### Environment-Based Configuration

```python
import os
import asyncio
from mcp_client import MCPClient

# Set up environment variables first
os.environ["MCP_SERVER_URL"] = "http://localhost:3000"
os.environ["DEFAULT_CHANNEL_ID"] = "your-default-channel"
os.environ["BOT_USER_ID"] = "your-bot-user-id"

async def configured_example():
    """Use environment variables for configuration."""
    mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
    default_channel = os.getenv("DEFAULT_CHANNEL_ID")
    bot_user_id = os.getenv("BOT_USER_ID")
    
    if not default_channel:
        print("❌ Please set DEFAULT_CHANNEL_ID environment variable")
        return
    
    async with MCPClient(mcp_url) as client:
        # Send a configured message
        await client.call_tool("send_message", {
            "channel_id": default_channel,
            "message": f"🤖 Bot {bot_user_id} is online and configured!"
        })
        
        print("✅ Configured message sent!")

asyncio.run(configured_example())
```

## Common Patterns

### Batch Operations

```python
async def send_multiple_messages():
    """Send messages to multiple channels."""
    channels = [
        "channel-1-id",
        "channel-2-id", 
        "channel-3-id"
    ]
    
    message = "📢 Important announcement for all teams!"
    
    async with MCPClient("http://localhost:3000") as client:
        results = []
        
        for channel_id in channels:
            try:
                result = await client.call_tool("send_message", {
                    "channel_id": channel_id,
                    "message": message
                })
                results.append({"channel": channel_id, "success": True, "post_id": result["post_id"]})
                print(f"✅ Sent to {channel_id}")
                
            except Exception as e:
                results.append({"channel": channel_id, "success": False, "error": str(e)})
                print(f"❌ Failed to send to {channel_id}: {e}")
        
        # Summary
        successful = sum(1 for r in results if r["success"])
        print(f"\n📊 Sent to {successful}/{len(channels)} channels")

asyncio.run(send_multiple_messages())
```

### Rate-Limited Operations

```python
async def rate_limited_operations():
    """Perform operations with rate limiting."""
    operations = [
        {"channel_id": "channel-1", "message": "Message 1"},
        {"channel_id": "channel-2", "message": "Message 2"},
        {"channel_id": "channel-3", "message": "Message 3"},
    ]
    
    async with MCPClient("http://localhost:3000") as client:
        for i, op in enumerate(operations):
            await client.call_tool("send_message", op)
            print(f"✅ Sent message {i + 1}")
            
            # Rate limiting: wait 1 second between messages
            if i < len(operations) - 1:
                await asyncio.sleep(1)

asyncio.run(rate_limited_operations())
```

## Next Steps

Once you're comfortable with these basics:

1. **Try Real-time Features**: [WebSocket Streaming](websocket-streaming.md)
2. **Build a Bot**: [Chatbot Example](chatbot.md)
3. **Handle Files**: [File Processing](file-processing.md)
4. **Set Up Monitoring**: [Health Monitoring](health-monitoring.md)

## Common Issues

### Channel ID Not Found
- Double-check the channel ID in Mattermost
- Ensure the bot has access to the channel
- Verify the team ID is correct

### Permission Denied
- Check bot permissions in Mattermost
- Ensure bot is a member of the channel
- Verify API token is valid and has correct scope

### Rate Limiting
- Add delays between requests (`asyncio.sleep()`)
- Implement exponential backoff
- Use batch operations when available

### Connection Issues
- Verify MCP server is running (`curl http://localhost:3000/health`)
- Check network connectivity
- Review server logs for errors

Need more help? Check the [Troubleshooting Guide](../troubleshooting.md) or [FAQ](../faq.md).
