# Mattermost MCP Python Documentation

Welcome to the comprehensive documentation for Mattermost MCP Python - a Model Context Protocol server implementation for seamless Mattermost integration.

## 📚 Documentation Overview

- **[Quick Start Guide](quickstart.md)** - Get up and running in 5 minutes
- **[Architecture Overview](architecture.md)** - System design and component architecture
- **[API Reference](api/README.md)** - Complete API documentation
- **[Tool Catalog](tools/README.md)** - Available MCP tools and usage
- **[Examples](examples/README.md)** - Code examples and use cases
- **[Configuration Guide](configuration.md)** - Detailed configuration options
- **[Deployment Guide](deployment.md)** - Production deployment strategies
- **[Development Guide](development.md)** - Contributing and development setup
- **[FAQ](faq.md)** - Frequently asked questions
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## 🚀 Quick Links

### For Users
- [🔧 Installation & Setup](quickstart.md#installation)
- [🎯 Basic Usage Examples](examples/basic-usage.md)
- [🛠️ Tool Reference](tools/README.md)
- [⚙️ Configuration Options](configuration.md)

### For Developers
- [📐 Architecture Design](architecture.md)
- [🧪 Development Setup](development.md)
- [🧩 API Documentation](api/README.md)
- [📝 Contributing Guidelines](../CONTRIBUTING.md)

### For DevOps
- [🐳 Docker Deployment](deployment.md#docker)
- [☸️ Kubernetes Deployment](deployment.md#kubernetes)
- [📊 Monitoring & Metrics](monitoring.md)
- [🔒 Security Configuration](security.md)

## 🏃‍♂️ Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/cronus42/mattermost-mcp-python.git
cd mattermost-mcp-python

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

This will start:
- PostgreSQL database
- Mattermost server (accessible at http://localhost:8065)
- MCP Mattermost server (accessible at http://localhost:3000)

### Manual Installation

```bash
# Install the package
pip install mattermost-mcp-python

# Set up environment
export MATTERMOST_URL="https://your-mattermost.com"
export MATTERMOST_TOKEN="your-api-token"

# Run the server
python -m mcp_mattermost
```

## 🎯 What You Can Do

With Mattermost MCP Python, you can:

### 💬 **Messaging Operations**
- Send messages to channels or direct messages
- Reply to threads and manage conversations
- Add/remove reactions to posts
- Pin and unpin important messages

### 🏗️ **Channel Management**
- Create, update, and delete channels
- Manage channel memberships
- Search channels and get channel statistics
- Handle channel permissions

### 👥 **User Operations**
- Search and manage users
- Get user profiles and status
- Handle team memberships
- Manage user authentication

### 📁 **File Operations**
- Upload and download files
- Manage file attachments
- Get file metadata and thumbnails

### 📡 **Real-time Features**
- Stream live updates via WebSocket
- Monitor channel activity
- React to real-time events
- Automatic failover to polling

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Assistant  │    │   MCP Client    │    │  Your App/Bot   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    MCP Protocol │
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      ▼                      │
          │            MCP Mattermost Server           │
          │                                            │
          │  ┌─────────────┐  ┌─────────────┐         │
          │  │   Tools     │  │ Resources   │         │
          │  │ (Actions)   │  │ (Streams)   │         │
          │  └─────────────┘  └─────────────┘         │
          └──────────────┬─────────────────────────────┘
                         │
            HTTP/WS API  │
                         │
          ┌──────────────▼─────────────────────────────┐
          │            Mattermost Server               │
          │                                            │
          │  PostgreSQL  │  File Store  │  WebSocket  │
          └────────────────────────────────────────────┘
```

## 📖 Getting Help

- **Documentation**: Browse the documentation sections above
- **Issues**: [GitHub Issues](https://github.com/cronus42/mattermost-mcp-python/issues)
- **Examples**: Check the [examples directory](examples/)
- **FAQ**: See [Frequently Asked Questions](faq.md)

## 🤝 Contributing

We welcome contributions! Please see:
- [Development Guide](development.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
