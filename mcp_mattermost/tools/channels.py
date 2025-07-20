"""
Channel management MCP tools for Mattermost.

This module provides MCP tools for channel operations including
listing channels, creating channels, managing channel membership, etc.
"""

from typing import Any, Dict, Optional

import structlog

from ..models.channels import ChannelCreate, ChannelPatch, ChannelSearch
from ..services import ChannelsService
from .base import BaseMCPTool, mcp_tool

logger = structlog.get_logger(__name__)


class ChannelTools(BaseMCPTool):
    """MCP tools for channel operations."""

    def __init__(self, services: Dict[str, Any]):
        super().__init__(services)

    def _get_channels_service(self) -> ChannelsService:
        """Get the channels service."""
        return self._get_service("channels")


# Tool function implementations


async def list_channels(
    team_id: str,
    page: int = 0,
    per_page: int = 60,
    include_deleted: bool = False,
    public_only: bool = False,
    services: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    List channels for a team.

    Args:
        team_id: The team ID to list channels for
        page: Page number (0-based)
        per_page: Number of channels per page
        include_deleted: Include deleted channels
        public_only: Only show public channels
        services: Service dependencies

    Returns:
        Dictionary containing list of channels
    """
    if not services:
        raise ValueError("Services not provided")

    channels_service = services["channels"]

    if public_only:
        channels = await channels_service.get_public_channels_for_team(
            team_id=team_id, page=page, per_page=per_page
        )
    else:
        channels = await channels_service.get_channels_for_team(
            team_id=team_id,
            page=page,
            per_page=per_page,
            include_deleted=include_deleted,
        )

    return {
        "channels": [
            {
                "channel_id": channel.id,
                "name": channel.name,
                "display_name": channel.display_name,
                "type": channel.type,
                "team_id": channel.team_id,
                "creator_id": channel.creator_id,
                "create_at": channel.create_at,
                "update_at": channel.update_at,
                "delete_at": channel.delete_at,
                "header": channel.header,
                "purpose": channel.purpose,
                "last_post_at": channel.last_post_at,
                "total_msg_count": channel.total_msg_count,
                "extra_update_at": channel.extra_update_at,
            }
            for channel in channels
        ]
    }


async def get_channel(
    channel_id: Optional[str] = None,
    team_id: Optional[str] = None,
    channel_name: Optional[str] = None,
    services: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get a specific channel by ID or by name within a team.

    Args:
        channel_id: The channel ID (if using ID lookup)
        team_id: The team ID (required if using name lookup)
        channel_name: The channel name (if using name lookup)
        services: Service dependencies

    Returns:
        Dictionary containing channel information
    """
    if not services:
        raise ValueError("Services not provided")

    if not channel_id and not (team_id and channel_name):
        raise ValueError(
            "Either channel_id or (team_id and channel_name) must be provided"
        )

    channels_service = services["channels"]

    if channel_id:
        channel = await channels_service.get_channel(channel_id)
    else:
        channel = await channels_service.get_channel_by_name(team_id, channel_name)

    return {
        "channel_id": channel.id,
        "name": channel.name,
        "display_name": channel.display_name,
        "type": channel.type,
        "team_id": channel.team_id,
        "creator_id": channel.creator_id,
        "create_at": channel.create_at,
        "update_at": channel.update_at,
        "delete_at": channel.delete_at,
        "header": channel.header,
        "purpose": channel.purpose,
        "last_post_at": channel.last_post_at,
        "total_msg_count": channel.total_msg_count,
        "extra_update_at": channel.extra_update_at,
    }


async def create_channel(
    team_id: str,
    name: str,
    display_name: str,
    type: str = "O",  # O=Open, P=Private, D=Direct, G=Group
    purpose: Optional[str] = None,
    header: Optional[str] = None,
    services: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a new channel.

    Args:
        team_id: The team ID to create the channel in
        name: The channel name (URL-friendly)
        display_name: The channel display name
        type: Channel type (O=Open/Public, P=Private, D=Direct, G=Group)
        purpose: Channel purpose description
        header: Channel header text
        services: Service dependencies

    Returns:
        Dictionary containing created channel information
    """
    if not services:
        raise ValueError("Services not provided")

    channels_service = services["channels"]

    # Create the channel data
    channel_data = ChannelCreate(
        team_id=team_id,
        name=name,
        display_name=display_name,
        type=type,
        purpose=purpose or "",
        header=header or "",
    )

    # Create the channel
    channel = await channels_service.create_channel(channel_data)

    return {
        "channel_id": channel.id,
        "name": channel.name,
        "display_name": channel.display_name,
        "type": channel.type,
        "team_id": channel.team_id,
        "creator_id": channel.creator_id,
        "create_at": channel.create_at,
        "update_at": channel.update_at,
        "header": channel.header,
        "purpose": channel.purpose,
    }


async def update_channel(
    channel_id: str,
    display_name: Optional[str] = None,
    purpose: Optional[str] = None,
    header: Optional[str] = None,
    services: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update a channel's information.

    Args:
        channel_id: The channel ID to update
        display_name: New display name
        purpose: New purpose
        header: New header
        services: Service dependencies

    Returns:
        Dictionary containing updated channel information
    """
    if not services:
        raise ValueError("Services not provided")

    channels_service = services["channels"]

    # Create the patch data
    patch_data = ChannelPatch(display_name=display_name, purpose=purpose, header=header)

    # Update the channel
    channel = await channels_service.patch_channel(channel_id, patch_data)

    return {
        "channel_id": channel.id,
        "name": channel.name,
        "display_name": channel.display_name,
        "type": channel.type,
        "team_id": channel.team_id,
        "creator_id": channel.creator_id,
        "create_at": channel.create_at,
        "update_at": channel.update_at,
        "header": channel.header,
        "purpose": channel.purpose,
    }


async def delete_channel(
    channel_id: str, services: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Delete a channel.

    Args:
        channel_id: The channel ID to delete
        services: Service dependencies

    Returns:
        Dictionary with status information
    """
    if not services:
        raise ValueError("Services not provided")

    channels_service = services["channels"]

    # Delete the channel
    await channels_service.delete_channel(channel_id)

    return {"status": "success", "message": "Channel deleted successfully"}


async def search_channels(
    team_id: str, term: str, services: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Search for channels in a team.

    Args:
        team_id: The team ID to search in
        term: Search term
        services: Service dependencies

    Returns:
        Dictionary containing matching channels
    """
    if not services:
        raise ValueError("Services not provided")

    channels_service = services["channels"]

    # Create search data
    search_data = ChannelSearch(term=term)

    # Search channels
    channels = await channels_service.search_channels(team_id, search_data)

    return {
        "channels": [
            {
                "channel_id": channel.id,
                "name": channel.name,
                "display_name": channel.display_name,
                "type": channel.type,
                "team_id": channel.team_id,
                "header": channel.header,
                "purpose": channel.purpose,
                "total_msg_count": channel.total_msg_count,
            }
            for channel in channels
        ]
    }


async def add_user_to_channel(
    channel_id: str, user_id: str, services: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add a user to a channel.

    Args:
        channel_id: The channel ID
        user_id: The user ID to add
        services: Service dependencies

    Returns:
        Dictionary containing channel membership information
    """
    if not services:
        raise ValueError("Services not provided")

    channels_service = services["channels"]

    # Add user to channel
    member = await channels_service.add_channel_member(channel_id, user_id)

    return {
        "channel_id": member.channel_id,
        "user_id": member.user_id,
        "roles": member.roles,
        "last_viewed_at": member.last_viewed_at,
        "msg_count": member.msg_count,
        "mention_count": member.mention_count,
        "notify_props": member.notify_props,
    }


async def remove_user_from_channel(
    channel_id: str, user_id: str, services: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Remove a user from a channel.

    Args:
        channel_id: The channel ID
        user_id: The user ID to remove
        services: Service dependencies

    Returns:
        Dictionary with status information
    """
    if not services:
        raise ValueError("Services not provided")

    channels_service = services["channels"]

    # Remove user from channel
    await channels_service.remove_channel_member(channel_id, user_id)

    return {"status": "success", "message": "User removed from channel successfully"}


async def get_channel_members(
    channel_id: str,
    page: int = 0,
    per_page: int = 60,
    services: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get members of a channel.

    Args:
        channel_id: The channel ID
        page: Page number (0-based)
        per_page: Number of members per page
        services: Service dependencies

    Returns:
        Dictionary containing channel members
    """
    if not services:
        raise ValueError("Services not provided")

    channels_service = services["channels"]

    # Get channel members
    members = await channels_service.get_channel_members(
        channel_id=channel_id, page=page, per_page=per_page
    )

    return {
        "members": [
            {
                "channel_id": member.channel_id,
                "user_id": member.user_id,
                "roles": member.roles,
                "last_viewed_at": member.last_viewed_at,
                "msg_count": member.msg_count,
                "mention_count": member.mention_count,
                "notify_props": member.notify_props,
            }
            for member in members
        ]
    }


async def get_channel_stats(
    channel_id: str, services: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get channel statistics.

    Args:
        channel_id: The channel ID
        services: Service dependencies

    Returns:
        Dictionary containing channel statistics
    """
    if not services:
        raise ValueError("Services not provided")

    channels_service = services["channels"]

    # Get channel stats
    stats = await channels_service.get_channel_stats(channel_id)

    return {
        "channel_id": stats.channel_id,
        "member_count": stats.member_count,
        "guest_count": stats.guest_count or 0,
        "pinned_post_count": stats.pinnedpost_count or 0,
    }


# MCP Tool Registrations


@mcp_tool(
    name="list_channels",
    description="List channels for a team",
    input_schema={
        "type": "object",
        "properties": {
            "team_id": {
                "type": "string",
                "description": "The team ID to list channels for",
            },
            "page": {
                "type": "integer",
                "description": "Page number (0-based)",
                "default": 0,
            },
            "per_page": {
                "type": "integer",
                "description": "Number of channels per page",
                "default": 60,
            },
            "include_deleted": {
                "type": "boolean",
                "description": "Include deleted channels",
                "default": False,
            },
            "public_only": {
                "type": "boolean",
                "description": "Only show public channels",
                "default": False,
            },
        },
        "required": ["team_id"],
    },
)
async def _list_channels_tool(**kwargs):
    return await list_channels(**kwargs)


@mcp_tool(
    name="get_channel",
    description="Get a specific channel by ID or name",
    input_schema={
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "The channel ID (if using ID lookup)",
            },
            "team_id": {
                "type": "string",
                "description": "The team ID (required if using name lookup)",
            },
            "channel_name": {
                "type": "string",
                "description": "The channel name (if using name lookup)",
            },
        },
    },
)
async def _get_channel_tool(**kwargs):
    return await get_channel(**kwargs)


@mcp_tool(
    name="create_channel",
    description="Create a new channel",
    input_schema={
        "type": "object",
        "properties": {
            "team_id": {
                "type": "string",
                "description": "The team ID to create the channel in",
            },
            "name": {
                "type": "string",
                "description": "The channel name (URL-friendly)",
            },
            "display_name": {
                "type": "string",
                "description": "The channel display name",
            },
            "type": {
                "type": "string",
                "description": (
                    "Channel type (O=Open/Public, P=Private, D=Direct, G=Group)"
                ),
                "enum": ["O", "P", "D", "G"],
                "default": "O",
            },
            "purpose": {"type": "string", "description": "Channel purpose description"},
            "header": {"type": "string", "description": "Channel header text"},
        },
        "required": ["team_id", "name", "display_name"],
    },
)
async def _create_channel_tool(**kwargs):
    return await create_channel(**kwargs)


@mcp_tool(
    name="add_user_to_channel",
    description="Add a user to a channel",
    input_schema={
        "type": "object",
        "properties": {
            "channel_id": {"type": "string", "description": "The channel ID"},
            "user_id": {"type": "string", "description": "The user ID to add"},
        },
        "required": ["channel_id", "user_id"],
    },
)
async def _add_user_to_channel_tool(**kwargs):
    return await add_user_to_channel(**kwargs)


@mcp_tool(
    name="remove_user_from_channel",
    description="Remove a user from a channel",
    input_schema={
        "type": "object",
        "properties": {
            "channel_id": {"type": "string", "description": "The channel ID"},
            "user_id": {"type": "string", "description": "The user ID to remove"},
        },
        "required": ["channel_id", "user_id"],
    },
)
async def _remove_user_from_channel_tool(**kwargs):
    return await remove_user_from_channel(**kwargs)


@mcp_tool(
    name="get_channel_members",
    description="Get members of a channel",
    input_schema={
        "type": "object",
        "properties": {
            "channel_id": {"type": "string", "description": "The channel ID"},
            "page": {
                "type": "integer",
                "description": "Page number (0-based)",
                "default": 0,
            },
            "per_page": {
                "type": "integer",
                "description": "Number of members per page",
                "default": 60,
            },
        },
        "required": ["channel_id"],
    },
)
async def _get_channel_members_tool(**kwargs):
    return await get_channel_members(**kwargs)


@mcp_tool(
    name="search_channels",
    description="Search for channels in a team",
    input_schema={
        "type": "object",
        "properties": {
            "team_id": {"type": "string", "description": "The team ID to search in"},
            "term": {"type": "string", "description": "Search term"},
        },
        "required": ["team_id", "term"],
    },
)
async def _search_channels_tool(**kwargs):
    return await search_channels(**kwargs)
