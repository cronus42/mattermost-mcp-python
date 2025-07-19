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
    __all__ = ["MattermostMCPServer"]
except ImportError:
    # If server dependencies are not available, just export the models
    __all__ = []
