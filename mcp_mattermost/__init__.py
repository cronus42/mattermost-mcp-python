"""
Mattermost MCP Python - A Model Context Protocol server for Mattermost integration.

This package provides an MCP server implementation that enables AI assistants
to interact with Mattermost through the Model Context Protocol.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Optional imports to avoid dependency issues when just using models
try:
    from .server import MattermostMCPServer
    from .stdio_server import (
        MattermostStdioServer,
        create_stdio_server,
        run_stdio_server,
    )

    __all__ = [
        "MattermostMCPServer",
        "MattermostStdioServer",
        "create_stdio_server",
        "run_stdio_server",
    ]
except ImportError:
    # If server dependencies are not available, just export the models
    __all__ = []
