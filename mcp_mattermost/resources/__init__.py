"""
MCP resource implementations for Mattermost data access.

This module provides MCP resources that offer both read-only access to Mattermost
data and real-time streaming updates via WebSocket or polling mechanisms.
"""

from .base import (
    BaseMCPResource,
    MCPResourceDefinition,
    MCPResourceRegistry,
    ResourceUpdate,
    ResourceUpdateType,
)
from .channel_posts import NewChannelPostResource
from .reactions import ReactionResource

__all__ = [
    "BaseMCPResource",
    "MCPResourceRegistry",
    "MCPResourceDefinition",
    "ResourceUpdate",
    "ResourceUpdateType",
    "NewChannelPostResource",
    "ReactionResource",
]
