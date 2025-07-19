# Mattermost MCP Python

A Model Context Protocol (MCP) server implementation for Mattermost integration.

## Overview

This project provides an MCP server that enables interaction with Mattermost through the Model Context Protocol, allowing AI assistants to interact with Mattermost channels, users, and other features.

## Features

- **MCP Server**: Full Model Context Protocol server implementation
- **Async HTTP Client**: Advanced HTTP client with retries, rate limiting, and error handling
- **Typed Models**: Comprehensive Pydantic models for all Mattermost entities
- **Domain Services**: High-level async services for core Mattermost operations:
  - **UsersService**: User management, authentication, search, and profiles
  - **TeamsService**: Team operations, membership management, and invitations
  - **ChannelsService**: Channel CRUD, membership, and statistics
  - **PostsService**: Post creation, editing, search, reactions, and threads
  - **FilesService**: File upload, download, metadata, and attachment management
- **Error Handling**: Comprehensive error types and logging
- **Type Safety**: Full type hints and runtime validation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cronus42/mattermost-mcp-python.git
cd mattermost-mcp-python
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env with your Mattermost configuration
```

## Configuration

Copy `.env.example` to `.env` and configure the following variables:

- `MATTERMOST_URL`: Your Mattermost instance URL
- `MATTERMOST_TOKEN`: Your Mattermost API token
- `MATTERMOST_TEAM_ID`: Team ID to connect to (optional)

## Usage

### Running the MCP Server

```bash
python -m mcp_mattermost
```

### Using Domain Services

The library provides high-level domain services for easy Mattermost API interaction:

```python
from mcp_mattermost.api.client import AsyncHTTPClient
from mcp_mattermost.services import UsersService, TeamsService, PostsService

# Initialize HTTP client
async with AsyncHTTPClient(
    base_url="https://your-mattermost.com/api/v4",
    token="your-token"
) as client:
    # Use domain services
    users_service = UsersService(client)
    teams_service = TeamsService(client)
    posts_service = PostsService(client)
    
    # Get current user
    current_user = await users_service.get_me()
    
    # Get user's teams
    teams = await teams_service.get_teams_for_user(current_user.id)
    
    # Create a post
    from mcp_mattermost.models.posts import PostCreate
    post_data = PostCreate(
        channel_id="channel_id_here",
        message="Hello from the Mattermost MCP Python library!"
    )
    new_post = await posts_service.create_post(post_data)
```

### Development

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

Run tests:
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions, please open an issue on the GitHub repository.
