"""
Event handling and real-time features for Mattermost integration.

This module provides WebSocket connectivity, event processing, and real-time
monitoring capabilities for the Mattermost MCP server.
"""

from .websocket import MattermostWebSocketClient, WebSocketMessage

__all__ = [
    "MattermostWebSocketClient",
    "WebSocketMessage",
]
