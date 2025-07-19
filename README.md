# Mattermost MCP Python

A Model Context Protocol (MCP) server implementation for Mattermost integration.

## Overview

This project provides an MCP server that enables interaction with Mattermost through the Model Context Protocol, allowing AI assistants to interact with Mattermost channels, users, and other features.

## Features

- Connect to Mattermost instances
- Send and receive messages
- Manage channels and users
- Access Mattermost API functionality through MCP

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
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
