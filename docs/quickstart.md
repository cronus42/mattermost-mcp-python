# 🚀 Quick Start Guide

Get Mattermost MCP Python up and running in 5 minutes with our Docker Compose setup.

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- Text editor for configuration

## Option 1: Docker Compose Setup (Recommended)

### Step 1: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/cronus42/mattermost-mcp-python.git
cd mattermost-mcp-python

# Copy environment template
cp .env.example .env
```

### Step 2: Basic Configuration

Edit the `.env` file with your settings:

```bash
# Required: Set these after Mattermost is running
MATTERMOST_URL=http://localhost:8065
MATTERMOST_TOKEN=your_bot_token_here
MATTERMOST_TEAM_ID=your_team_id_here

# Optional: Customize these
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=3000
LOG_LEVEL=INFO
```

### Step 3: Start Services

```bash
# Start all services (PostgreSQL + Mattermost + MCP Server)
docker-compose up -d

# Check that services are healthy
docker-compose ps
```

Expected output:
```
      Name                     Command                  State                    Ports
------------------------------------------------------------------------------------------------
mattermost_postgres_1    docker-entrypoint.sh postgres   Up (healthy)   5432/tcp
mattermost_mattermost_1  /entrypoint.sh mattermost        Up (healthy)   0.0.0.0:8065->8065/tcp
mattermost_redis_1       docker-entrypoint.sh redis       Up (healthy)   6379/tcp
```

### Step 4: Initial Mattermost Setup

1. **Open Mattermost**: Navigate to http://localhost:8065
2. **Create Admin Account**: Set up your system administrator account
3. **Create a Team**: Create your first team
4. **Set up Bot Account**:
   ```bash
   # Access Mattermost container
   docker-compose exec mattermost bash

   # Create a bot user (replace with your details)
   ./bin/mmctl auth login http://localhost:8065 --name local --username admin --password yourpassword
   ./bin/mmctl bot create mcp-bot --display-name "MCP Bot" --description "MCP integration bot"

   # Note the token from the output
   ```

### Step 5: Configure MCP Server

Update your `.env` file with the bot token and team ID:

```bash
# Get team ID from Mattermost
curl -H "Authorization: Bearer YOUR_BOT_TOKEN" http://localhost:8065/api/v4/teams

# Update .env file
MATTERMOST_TOKEN=your_actual_bot_token
MATTERMOST_TEAM_ID=your_actual_team_id
```

Restart the MCP server:
```bash
docker-compose restart mcp-mattermost
```

### Step 6: Test the Setup

```bash
# Check MCP server health
curl http://localhost:3000/health

# Test MCP server logs
docker-compose logs mcp-mattermost
```

## Option 2: Manual Installation

### Step 1: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
pip install mattermost-mcp-python

# Or for development
git clone https://github.com/cronus42/mattermost-mcp-python.git
cd mattermost-mcp-python
pip install -r requirements.txt
```

### Step 2: Set Environment Variables

```bash
export MATTERMOST_URL="https://your-mattermost-instance.com"
export MATTERMOST_TOKEN="your-bot-token"
export MATTERMOST_TEAM_ID="your-team-id"
```

### Step 3: Run the Server

```bash
python -m mcp_mattermost
```

## Verification Steps

### 1. Health Check

```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "mattermost_connection": "ok",
  "websocket_connection": "ok"
}
```

### 2. MCP Protocol Test

Test MCP protocol endpoints:

```bash
# List available tools
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'

# List available resources
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "resources/list"}'
```

### 3. Send Test Message

Use the MCP client to send a message:

```python
import asyncio
from mcp_client import create_mcp_client

async def test_message():
    async with create_mcp_client("http://localhost:3000") as client:
        result = await client.call_tool("send_message", {
            "channel_id": "your-channel-id",
            "message": "Hello from MCP!"
        })
        print(f"Message sent: {result}")

# Run the test
asyncio.run(test_message())
```

## Common Next Steps

### 1. Connect to Your Mattermost Instance

If you have an existing Mattermost instance:

```bash
# Update docker-compose.yml to remove local Mattermost and PostgreSQL
# Or update .env to point to your instance
MATTERMOST_URL=https://your-company.mattermost.com
```

### 2. Enable WebSocket Streaming

```bash
# In .env file
ENABLE_STREAMING=true
WS_URL=wss://your-mattermost.com/api/v4/websocket
```

### 3. Configure Channel Monitoring

```bash
# Monitor specific channels
DEFAULT_CHANNEL=your-default-channel-id
ALLOWED_CHANNELS=channel1,channel2,channel3
```

### 4. Set up SSL/TLS (Production)

For production deployments, configure SSL:

```bash
# Update docker-compose.yml nginx service
# Add SSL certificates to ./docker/certs/
# Update nginx.conf for HTTPS
```

## Troubleshooting

### MCP Server Won't Start
```bash
# Check logs
docker-compose logs mcp-mattermost

# Common issues:
# 1. Invalid Mattermost token
# 2. Network connectivity issues
# 3. Port conflicts
```

### Mattermost Connection Issues
```bash
# Test Mattermost API directly
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8065/api/v4/users/me

# Check Mattermost logs
docker-compose logs mattermost
```

### Port Conflicts
```bash
# If port 8065 or 3000 are in use, update docker-compose.yml:
ports:
  - "8066:8065"  # Mattermost
  - "3001:3000"  # MCP Server
```

## What's Next?

- **[Architecture Overview](architecture.md)** - Understand the system design
- **[Tool Catalog](tools/README.md)** - Explore available MCP tools
- **[Examples](examples/README.md)** - See practical usage examples
- **[Configuration Guide](configuration.md)** - Advanced configuration options
- **[Development Guide](development.md)** - Contributing and customization

## Need Help?

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/cronus42/mattermost-mcp-python/issues)
- 💬 [Discussions](https://github.com/cronus42/mattermost-mcp-python/discussions)
- ❓ [FAQ](faq.md)
