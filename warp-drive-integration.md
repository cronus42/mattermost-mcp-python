# Warp Drive IDE & MCP Integration

## Introduction

This guide provides comprehensive instructions for integrating the Mattermost MCP (Model Context Protocol) server with Warp Drive IDE. The integration enables AI assistants and development workflows to interact with Mattermost teams directly from your IDE, providing real-time messaging capabilities, channel management, and team collaboration features.

### Benefits
- **Direct Mattermost Integration**: Send messages, manage channels, and interact with team members without leaving your IDE
- **Real-time Streaming**: Receive live updates from Mattermost channels and reactions
- **AI Assistant Integration**: Enable AI assistants to participate in team communication workflows
- **Development Workflow Enhancement**: Automate notifications, status updates, and team coordination

## Mattermost MCP Setup

This section covers the complete setup process for integrating Mattermost MCP with Warp Drive IDE.

### Prerequisites

Before setting up the Mattermost MCP integration, ensure you have the following:

#### Mattermost Server Requirements
1. **Mattermost Instance**: Access to a Mattermost server (cloud or self-hosted)
2. **Bot Token**: A Mattermost bot access token with appropriate permissions
3. **Team ID**: The team ID where the bot will operate
4. **Channel Access**: Bot must be added to channels it needs to interact with

#### System Requirements
- **Python 3.8+**: Required for running the MCP server
- **Warp Drive IDE**: Latest version with MCP support
- **Network Access**: Ability to connect to your Mattermost server

#### Obtaining Required Credentials

##### 1. Creating a Mattermost Bot Token
1. Log into your Mattermost instance as an admin
2. Go to **System Console** > **Integrations** > **Bot Accounts**
3. Click **Add Bot Account**
4. Fill in the bot details:
   - **Username**: `mcp-bot` (or your preferred name)
   - **Display Name**: `MCP Integration Bot`
   - **Description**: `Bot for Warp Drive MCP integration`
5. Assign appropriate roles (usually `Member` is sufficient)
6. Save and copy the generated **Access Token**

##### 2. Getting Your Team ID
1. In Mattermost, go to **Main Menu** > **System Console**
2. Navigate to **User Management** > **Teams**
3. Find your team and copy the **Team ID** from the URL or team settings

Alternatively, you can get the Team ID via API:
```bash
curl -H "Authorization: Bearer YOUR_BOT_TOKEN" \
     https://your-mattermost.com/api/v4/teams
```

### Environment Variables

Create a `.env` file or set the following environment variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `MATTERMOST_URL` | ✅ | Your Mattermost server URL | `https://your-team.mattermost.com` |
| `MATTERMOST_TOKEN` | ✅ | Bot access token | `abc123def456...` |
| `MATTERMOST_TEAM_ID` | ✅ | Target team ID | `team123abc456` |
| `MCP_SERVER_HOST` | ❌ | MCP server bind address | `localhost` (default) |
| `MCP_SERVER_PORT` | ❌ | MCP server port | `3000` (default) |
| `LOG_LEVEL` | ❌ | Logging verbosity | `INFO` (default) |
| `ENABLE_STREAMING` | ❌ | Enable WebSocket streaming | `true` (default) |
| `ENABLE_POLLING` | ❌ | Enable polling fallback | `true` (default) |

#### Example .env file:
```bash
# Mattermost Configuration
MATTERMOST_URL=https://your-team.mattermost.com
MATTERMOST_TOKEN=your-bot-token-here
MATTERMOST_TEAM_ID=your-team-id

# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3000
LOG_LEVEL=INFO

# Feature Flags
ENABLE_STREAMING=true
ENABLE_POLLING=true
```

### Warp Drive MCP Configuration

Add the following configuration to your Warp Drive `mcp_config.json` file:

```json
{
  "mcpServers": {
    "mattermost": {
      "command": "python",
      "args": ["-m", "mcp_mattermost"],
      "env": {
        "MATTERMOST_URL": "https://your-mattermost-instance.com",
        "MATTERMOST_TOKEN": "your-bot-token-here",
        "MATTERMOST_TEAM_ID": "your-team-id",
        "MCP_SERVER_HOST": "localhost",
        "MCP_SERVER_PORT": "3000",
        "LOG_LEVEL": "INFO",
        "ENABLE_STREAMING": "true",
        "ENABLE_POLLING": "true"
      },
      "description": "Mattermost MCP server for team communication",
      "disabled": false
    }
  },
  "resources": [
    {
      "uri": "mattermost://new_channel_posts",
      "name": "Channel Posts Stream",
      "description": "Real-time stream of new posts from monitored channels"
    },
    {
      "uri": "mattermost://reactions",
      "name": "Message Reactions",
      "description": "Real-time stream of emoji reactions on posts"
    }
  ],
  "tools": [
    {
      "name": "send_message",
      "description": "Send a message to a Mattermost channel",
      "parameters": {
        "channel_id": {
          "type": "string",
          "description": "The channel ID to send the message to"
        },
        "message": {
          "type": "string",
          "description": "The message text to send"
        },
        "root_id": {
          "type": "string",
          "description": "Optional root post ID for threading",
          "required": false
        }
      }
    },
    {
      "name": "get_channel_history",
      "description": "Retrieve message history from a channel",
      "parameters": {
        "channel_id": {
          "type": "string",
          "description": "The channel ID to get history from"
        },
        "limit": {
          "type": "integer",
          "description": "Number of messages to retrieve (default: 60)",
          "required": false
        }
      }
    },
    {
      "name": "search_channels",
      "description": "Search for channels by name or topic",
      "parameters": {
        "query": {
          "type": "string",
          "description": "Search query for channel names or topics"
        },
        "team_id": {
          "type": "string",
          "description": "Optional team ID to scope search",
          "required": false
        }
      }
    }
  ]
}
```

### Installation Steps

1. **Install the MCP Server**:
   ```bash
   pip install mattermost-mcp-python
   ```

2. **Set up environment variables** (choose one):
   
   **Option A: Using .env file**
   ```bash
   # Create .env file with your configuration
   cp .env.example .env
   # Edit .env with your actual values
   ```
   
   **Option B: Export directly**
   ```bash
   export MATTERMOST_URL="https://your-team.mattermost.com"
   export MATTERMOST_TOKEN="your-bot-token"
   export MATTERMOST_TEAM_ID="your-team-id"
   ```

3. **Test the MCP server**:
   ```bash
   python -m mcp_mattermost --help
   ```

4. **Add configuration to Warp Drive**:
   - Open Warp Drive IDE
   - Navigate to MCP settings
   - Add the JSON configuration above
   - Restart Warp Drive

### Verification

To verify your setup is working correctly:

1. **Check MCP Server Status**:
   ```bash
   python -m mcp_mattermost --no-streaming --no-polling
   ```
   You should see:
   ```
   ✅ Mattermost MCP Server starting...
   📊 Found 2 MCP resources
   🔧 Server initialized successfully
   ```

2. **Test in Warp Drive**:
   - Open Warp Drive IDE
   - Check that the Mattermost MCP server appears in your MCP server list
   - Try using one of the tools (e.g., `send_message`) in a chat with an AI assistant

3. **Test Basic Operations**:
   ```python
   # Example usage in Warp Drive chat:
   # "Send a message to the general channel saying 'Hello from MCP!'"
   ```

### Common Troubleshooting Tips

#### Connection Issues

**Problem**: "Unable to connect to Mattermost server"

**Solutions**:
1. **Check URL format**: Ensure `MATTERMOST_URL` doesn't have trailing slashes
   ```bash
   # ✅ Correct
   MATTERMOST_URL=https://your-team.mattermost.com
   
   # ❌ Incorrect
   MATTERMOST_URL=https://your-team.mattermost.com/
   ```

2. **Verify network access**: Test connectivity to your Mattermost server
   ```bash
   curl -I https://your-team.mattermost.com/api/v4/system/ping
   ```

3. **Check firewall settings**: Ensure your development environment can reach the Mattermost server

#### Authentication Errors

**Problem**: "401 Unauthorized" or "Invalid token"

**Solutions**:
1. **Verify bot token**: Check that your bot token is correctly copied
2. **Check bot permissions**: Ensure the bot has necessary permissions
3. **Regenerate token**: If needed, create a new bot token in Mattermost
4. **Test token manually**:
   ```bash
   curl -H "Authorization: Bearer YOUR_BOT_TOKEN" \
        https://your-mattermost.com/api/v4/users/me
   ```

#### Configuration Issues

**Problem**: "MCP server not appearing in Warp Drive"

**Solutions**:
1. **Validate JSON**: Ensure your `mcp_config.json` is valid JSON
2. **Check file location**: Verify the config file is in the correct Warp Drive directory
3. **Restart Warp Drive**: Sometimes a restart is needed after configuration changes
4. **Check logs**: Look for error messages in Warp Drive's MCP server logs

#### Channel Access Issues

**Problem**: "Cannot access channel" or "Channel not found"

**Solutions**:
1. **Add bot to channels**: Invite the bot to channels it needs to access
2. **Use channel IDs**: Always use channel IDs, not display names
3. **Get channel ID**:
   ```bash
   # Via API
   curl -H "Authorization: Bearer YOUR_BOT_TOKEN" \
        "https://your-mattermost.com/api/v4/teams/TEAM_ID/channels/name/CHANNEL_NAME"
   ```
4. **Check team membership**: Ensure the bot is a member of the correct team

#### Performance Issues

**Problem**: Slow response times or timeouts

**Solutions**:
1. **Adjust timeouts**: Increase timeout values in environment variables
   ```bash
   export MATTERMOST_TIMEOUT=30
   ```

2. **Disable streaming**: If having WebSocket issues, disable streaming
   ```bash
   export ENABLE_STREAMING=false
   ```

3. **Enable polling fallback**: Ensure polling is enabled as backup
   ```bash
   export ENABLE_POLLING=true
   ```

4. **Check server resources**: Monitor your Mattermost server's performance

#### Debug Mode

For additional troubleshooting, enable debug logging:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python -m mcp_mattermost --verbose
```

This will provide detailed information about:
- API requests and responses
- WebSocket connection status
- Resource streaming events
- Error stack traces

### Support Resources

If you continue experiencing issues:

1. **Check the documentation**: [Mattermost MCP Docs](docs/README.md)
2. **Review examples**: [Usage Examples](examples/README.md)
3. **Search issues**: [GitHub Issues](https://github.com/cronus42/mattermost-mcp-python/issues)
4. **Create new issue**: Include debug logs and configuration details

## Additional Configuration Options

For advanced users who need additional configuration beyond the standard Mattermost MCP setup above, the following options are available:

## Usage Examples

Once you have completed the Mattermost MCP Setup above, you can use these examples to test and work with your integration.

### Basic Workflow

1. **Send a message to a channel**:
   ```
   AI Assistant: "Send a message to the general channel saying 'Hello from MCP integration!'"
   ```

2. **Get recent messages from a channel**:
   ```
   AI Assistant: "Show me the last 10 messages from the dev-team channel"
   ```

3. **Search for channels**:
   ```
   AI Assistant: "Find all channels related to 'development' in our team"
   ```

### Advanced Use Cases

#### Automated Team Notifications
Set up automated notifications for deployment status, build results, or other CI/CD events:
```python
# Example: Notify team of successful deployment
# This would be handled automatically by the AI assistant using MCP tools
```

#### Real-time Channel Monitoring
Monitor specific channels for important updates and react accordingly:
- Development alerts
- Support requests
- Team announcements

### Integration with Existing Projects

#### Development Workflow Integration
- **Code Review Notifications**: Automatically notify relevant team members about code reviews
- **Issue Tracking**: Create Mattermost threads for tracking issues and their resolution
- **Status Updates**: Regular project status updates sent to project channels

#### CI/CD Integration
- **Build Notifications**: Send build status updates to development channels
- **Deployment Alerts**: Notify operations channels about deployments
- **Error Monitoring**: Alert teams about critical errors or system issues

## Next Steps

After completing the Mattermost MCP setup:

1. **Explore Documentation**: Review the [full documentation](docs/README.md) for advanced features
2. **Try Examples**: Experiment with the [usage examples](examples/README.md) 
3. **Customize Configuration**: Adapt the setup for your team's specific needs
4. **Monitor Performance**: Set up logging and monitoring for production use
5. **Join the Community**: Contribute back with issues, feature requests, or improvements

## Support and Resources

For additional help and resources:

- 📚 **Documentation**: [Complete docs](docs/README.md)
- 🔧 **Examples**: [Code examples](examples/README.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/cronus42/mattermost-mcp-python/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/cronus42/mattermost-mcp-python/discussions)
- 📖 **API Reference**: [API docs](docs/api/README.md)
