"""
Messaging MCP tools for Mattermost.

This module provides MCP tools for messaging operations including
sending messages, replying to threads, and managing message reactions.
"""

from typing import Any, Dict, List, Optional
import structlog

from .base import BaseMCPTool, mcp_tool
from ..services import PostsService
from ..models.posts import PostCreate, PostPatch, Reaction

logger = structlog.get_logger(__name__)


class MessagingTools(BaseMCPTool):
    """MCP tools for messaging operations."""
    
    def __init__(self, services: Dict[str, Any]):
        super().__init__(services)
    
    def _get_posts_service(self) -> PostsService:
        """Get the posts service."""
        return self._get_service("posts")


# Tool function implementations

async def send_message(
    channel_id: str,
    message: str,
    root_id: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    props: Optional[Dict[str, Any]] = None,
    services: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send a message to a channel or as a reply to a thread.
    
    Args:
        channel_id: The channel ID to send the message to
        message: The message text
        root_id: The root post ID for threading (optional)
        file_ids: List of file IDs to attach (optional)
        props: Additional properties for the post (optional)
        services: Service dependencies
        
    Returns:
        Dictionary containing the created post information
    """
    if not services:
        raise ValueError("Services not provided")
    
    posts_service = services["posts"]
    
    # Create the post data
    post_data = PostCreate(
        channel_id=channel_id,
        message=message,
        root_id=root_id,
        file_ids=file_ids or [],
        props=props or {}
    )
    
    # Send the message
    post = await posts_service.create_post(post_data)
    
    return {
        "post_id": post.id,
        "channel_id": post.channel_id,
        "message": post.message,
        "create_at": post.create_at,
        "update_at": post.update_at,
        "user_id": post.user_id,
        "root_id": post.root_id,
        "type": post.type,
        "props": post.props
    }


async def reply_to_thread(
    root_post_id: str,
    message: str,
    file_ids: Optional[List[str]] = None,
    props: Optional[Dict[str, Any]] = None,
    services: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Reply to a thread (convenience wrapper for send_message with root_id).
    
    Args:
        root_post_id: The root post ID to reply to
        message: The reply message text
        file_ids: List of file IDs to attach (optional)
        props: Additional properties for the post (optional)
        services: Service dependencies
        
    Returns:
        Dictionary containing the created post information
    """
    if not services:
        raise ValueError("Services not provided")
    
    posts_service = services["posts"]
    
    # First get the root post to determine the channel
    root_post = await posts_service.get_post(root_post_id)
    
    # Send the reply
    return await send_message(
        channel_id=root_post.channel_id,
        message=message,
        root_id=root_post_id,
        file_ids=file_ids,
        props=props,
        services=services
    )


async def update_message(
    post_id: str,
    message: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    props: Optional[Dict[str, Any]] = None,
    services: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update an existing message.
    
    Args:
        post_id: The post ID to update
        message: The new message text (optional)
        file_ids: Updated list of file IDs (optional)
        props: Updated properties (optional)
        services: Service dependencies
        
    Returns:
        Dictionary containing the updated post information
    """
    if not services:
        raise ValueError("Services not provided")
    
    posts_service = services["posts"]
    
    # Create the patch data
    patch_data = PostPatch(
        message=message,
        file_ids=file_ids,
        props=props
    )
    
    # Update the message
    post = await posts_service.patch_post(post_id, patch_data)
    
    return {
        "post_id": post.id,
        "channel_id": post.channel_id,
        "message": post.message,
        "create_at": post.create_at,
        "update_at": post.update_at,
        "user_id": post.user_id,
        "root_id": post.root_id,
        "type": post.type,
        "props": post.props
    }


async def delete_message(
    post_id: str,
    services: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Delete a message.
    
    Args:
        post_id: The post ID to delete
        services: Service dependencies
        
    Returns:
        Dictionary with status information
    """
    if not services:
        raise ValueError("Services not provided")
    
    posts_service = services["posts"]
    
    # Delete the message
    await posts_service.delete_post(post_id)
    
    return {"status": "success", "message": "Post deleted successfully"}


async def get_channel_history(
    channel_id: str,
    page: int = 0,
    per_page: int = 60,
    since: Optional[int] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    services: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get message history for a channel.
    
    Args:
        channel_id: The channel ID to get history for
        page: Page number (0-based)
        per_page: Number of posts per page
        since: Get posts since timestamp
        before: Get posts before this post ID
        after: Get posts after this post ID
        services: Service dependencies
        
    Returns:
        Dictionary containing posts and metadata
    """
    if not services:
        raise ValueError("Services not provided")
    
    posts_service = services["posts"]
    
    # Get channel posts
    post_list = await posts_service.get_posts_for_channel(
        channel_id=channel_id,
        page=page,
        per_page=per_page,
        since=since,
        before=before,
        after=after
    )
    
    return {
        "posts": [
            {
                "post_id": post.id,
                "channel_id": post.channel_id,
                "message": post.message,
                "create_at": post.create_at,
                "update_at": post.update_at,
                "user_id": post.user_id,
                "root_id": post.root_id,
                "type": post.type,
                "props": post.props
            }
            for post in post_list.posts.values()
        ] if post_list.posts else [],
        "order": post_list.order or [],
        "next_post_id": post_list.next_post_id,
        "prev_post_id": post_list.prev_post_id
    }


async def get_thread(
    root_post_id: str,
    services: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get a complete thread of messages.
    
    Args:
        root_post_id: The root post ID of the thread
        services: Service dependencies
        
    Returns:
        Dictionary containing the thread posts
    """
    if not services:
        raise ValueError("Services not provided")
    
    posts_service = services["posts"]
    
    # Get the thread
    post_list = await posts_service.get_post_thread(root_post_id)
    
    return {
        "posts": [
            {
                "post_id": post.id,
                "channel_id": post.channel_id,
                "message": post.message,
                "create_at": post.create_at,
                "update_at": post.update_at,
                "user_id": post.user_id,
                "root_id": post.root_id,
                "type": post.type,
                "props": post.props
            }
            for post in post_list.posts.values()
        ] if post_list.posts else [],
        "order": post_list.order or []
    }


async def add_reaction(
    post_id: str,
    emoji_name: str,
    user_id: str,
    services: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add a reaction to a message.
    
    Args:
        post_id: The post ID to react to
        emoji_name: The emoji name (without colons)
        user_id: The user ID adding the reaction
        services: Service dependencies
        
    Returns:
        Dictionary containing the reaction information
    """
    if not services:
        raise ValueError("Services not provided")
    
    posts_service = services["posts"]
    
    # Add the reaction
    reaction = await posts_service.add_reaction(user_id, post_id, emoji_name)
    
    return {
        "user_id": reaction.user_id,
        "post_id": reaction.post_id,
        "emoji_name": reaction.emoji_name,
        "create_at": reaction.create_at
    }


async def remove_reaction(
    post_id: str,
    emoji_name: str,
    user_id: str,
    services: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Remove a reaction from a message.
    
    Args:
        post_id: The post ID to remove reaction from
        emoji_name: The emoji name (without colons)
        user_id: The user ID removing the reaction
        services: Service dependencies
        
    Returns:
        Dictionary with status information
    """
    if not services:
        raise ValueError("Services not provided")
    
    posts_service = services["posts"]
    
    # Remove the reaction
    await posts_service.remove_reaction(user_id, post_id, emoji_name)
    
    return {"status": "success", "message": "Reaction removed successfully"}


async def pin_message(
    post_id: str,
    services: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Pin a message to its channel.
    
    Args:
        post_id: The post ID to pin
        services: Service dependencies
        
    Returns:
        Dictionary with status information
    """
    if not services:
        raise ValueError("Services not provided")
    
    posts_service = services["posts"]
    
    # Pin the message
    await posts_service.pin_post(post_id)
    
    return {"status": "success", "message": "Post pinned successfully"}


async def unpin_message(
    post_id: str,
    services: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Unpin a message from its channel.
    
    Args:
        post_id: The post ID to unpin
        services: Service dependencies
        
    Returns:
        Dictionary with status information
    """
    if not services:
        raise ValueError("Services not provided")
    
    posts_service = services["posts"]
    
    # Unpin the message
    await posts_service.unpin_post(post_id)
    
    return {"status": "success", "message": "Post unpinned successfully"}


# MCP Tool Registrations

@mcp_tool(
    name="send_message",
    description="Send a message to a channel",
    input_schema={
        "type": "object",
        "properties": {
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
                "description": "The root post ID for threading (optional)"
            },
            "file_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file IDs to attach (optional)"
            },
            "props": {
                "type": "object",
                "description": "Additional properties for the post (optional)"
            }
        },
        "required": ["channel_id", "message"]
    }
)
async def _send_message_tool(**kwargs):
    return await send_message(**kwargs)


@mcp_tool(
    name="reply_to_thread",
    description="Reply to a thread",
    input_schema={
        "type": "object",
        "properties": {
            "root_post_id": {
                "type": "string",
                "description": "The root post ID to reply to"
            },
            "message": {
                "type": "string",
                "description": "The reply message text"
            },
            "file_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file IDs to attach (optional)"
            },
            "props": {
                "type": "object",
                "description": "Additional properties for the post (optional)"
            }
        },
        "required": ["root_post_id", "message"]
    }
)
async def _reply_to_thread_tool(**kwargs):
    return await reply_to_thread(**kwargs)


@mcp_tool(
    name="get_channel_history",
    description="Get message history for a channel",
    input_schema={
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "The channel ID to get history for"
            },
            "page": {
                "type": "integer",
                "description": "Page number (0-based)",
                "default": 0
            },
            "per_page": {
                "type": "integer",
                "description": "Number of posts per page",
                "default": 60
            },
            "since": {
                "type": "integer",
                "description": "Get posts since timestamp"
            },
            "before": {
                "type": "string",
                "description": "Get posts before this post ID"
            },
            "after": {
                "type": "string", 
                "description": "Get posts after this post ID"
            }
        },
        "required": ["channel_id"]
    }
)
async def _get_channel_history_tool(**kwargs):
    return await get_channel_history(**kwargs)


@mcp_tool(
    name="add_reaction",
    description="Add a reaction to a message",
    input_schema={
        "type": "object",
        "properties": {
            "post_id": {
                "type": "string",
                "description": "The post ID to react to"
            },
            "emoji_name": {
                "type": "string",
                "description": "The emoji name (without colons)"
            },
            "user_id": {
                "type": "string",
                "description": "The user ID adding the reaction"
            }
        },
        "required": ["post_id", "emoji_name", "user_id"]
    }
)
async def _add_reaction_tool(**kwargs):
    return await add_reaction(**kwargs)


@mcp_tool(
    name="remove_reaction", 
    description="Remove a reaction from a message",
    input_schema={
        "type": "object",
        "properties": {
            "post_id": {
                "type": "string",
                "description": "The post ID to remove reaction from"
            },
            "emoji_name": {
                "type": "string",
                "description": "The emoji name (without colons)"
            },
            "user_id": {
                "type": "string",
                "description": "The user ID removing the reaction"
            }
        },
        "required": ["post_id", "emoji_name", "user_id"]
    }
)
async def _remove_reaction_tool(**kwargs):
    return await remove_reaction(**kwargs)
