"""
Authentication tools for Mattermost MCP server.

This module provides MCP tools for handling authentication with Mattermost,
allowing the client (Warp) to securely provide credentials at runtime.
"""

from typing import Any, Dict, Optional

import structlog

from ..auth import get_auth_state
from .base import BaseMCPTool, mcp_tool

logger = structlog.get_logger(__name__)


async def authenticate(
    mattermost_url: str,
    token: str,
    team_id: Optional[str] = None,
    services: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Authenticate with Mattermost using API credentials.

    Args:
        mattermost_url: Mattermost server URL (e.g., https://your-mattermost.com)
        token: Mattermost API token or bot token
        team_id: Optional team ID to scope operations to
        services: Service dependencies (unused for auth tools)

    Returns:
        Authentication result with user info and status
    """
    if not mattermost_url or not token:
        return {
            "success": False,
            "error": (
                "Missing required parameters: " "mattermost_url and token are required"
            ),
        }

    try:
        auth_state = get_auth_state()
        result = await auth_state.authenticate(
            mattermost_url=mattermost_url, token=token, team_id=team_id
        )

        logger.info(
            "Authentication tool succeeded",
            user_id=result.get("user_id"),
            username=result.get("username"),
        )

        # Notify any registered callbacks (e.g., for WebSocket reconnection)
        await _notify_auth_callbacks(auth_state)

        return result

    except Exception as e:
        logger.error(
            "Authentication tool failed", error=str(e), error_type=type(e).__name__
        )

        return {"success": False, "error": str(e), "error_type": type(e).__name__}


async def _notify_auth_callbacks(auth_state) -> None:
    """Notify authentication callbacks (e.g., for reconnecting WebSocket)."""
    try:
        # Trigger WebSocket reconnection through the auth state callbacks
        # The server instance registers callbacks during initialization
        logger.info("Authentication successful, notifying callbacks")
        # The actual notification happens through the auth_state._notify_auth_callbacks() method
    except Exception as e:
        logger.warning("Failed to notify auth callbacks", error=str(e))


def require_authentication(func):
    """Decorator to require authentication for tool/resource access."""

    async def wrapper(*args, **kwargs):
        auth_state = get_auth_state()
        if not auth_state.is_authenticated:
            logger.warning("Unauthorized access attempt", tool=func.__name__)
            return {
                "success": False,
                "error": "Authentication required. Please authenticate with Mattermost first.",
                "error_type": "AuthenticationError",
            }
        return await func(*args, **kwargs)

    return wrapper


def check_authentication() -> Dict[str, Any]:
    """Check if authentication is present and return status."""
    auth_state = get_auth_state()
    if not auth_state.is_authenticated:
        return {
            "authenticated": False,
            "error": "Authentication required. Please authenticate with Mattermost first.",
            "error_type": "AuthenticationError",
        }
    return {
        "authenticated": True,
        "user_id": auth_state.user_id,
        "username": auth_state.username,
        "mattermost_url": auth_state.mattermost_url,
        "team_id": auth_state.team_id,
    }


async def get_auth_status(
    services: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get current Mattermost authentication status.

    Args:
        services: Service dependencies (unused for auth tools)

    Returns:
        Current authentication status with user info and connection state
    """
    auth_state = get_auth_state()
    return auth_state.auth_info


async def logout(
    services: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Clear Mattermost authentication and logout.

    Args:
        services: Service dependencies (unused for auth tools)

    Returns:
        Logout result with success status
    """
    try:
        auth_state = get_auth_state()
        await auth_state.clear_authentication()

        logger.info("User logged out successfully")

        return {
            "success": True,
            "message": "Successfully logged out and cleared authentication",
        }

    except Exception as e:
        logger.error("Logout failed", error=str(e), error_type=type(e).__name__)

        return {"success": False, "error": str(e), "error_type": type(e).__name__}


# Tool function decorators for MCP registration


@mcp_tool(
    name="authenticate",
    description="Authenticate with Mattermost using API credentials",
    input_schema={
        "type": "object",
        "properties": {
            "mattermost_url": {
                "type": "string",
                "description": "Mattermost server URL (e.g., https://your-mattermost.com)",
            },
            "token": {
                "type": "string",
                "description": "Mattermost API token or bot token",
            },
            "team_id": {
                "type": "string",
                "description": "Optional team ID to scope operations to",
            },
        },
        "required": ["mattermost_url", "token"],
    },
)
async def _authenticate_tool(**kwargs):
    """MCP tool wrapper for authenticate function."""
    return await authenticate(**kwargs)


@mcp_tool(
    name="get_auth_status",
    description="Get current Mattermost authentication status",
    input_schema={"type": "object", "properties": {}, "required": []},
)
async def _get_auth_status_tool(**kwargs):
    """MCP tool wrapper for get_auth_status function."""
    return await get_auth_status(**kwargs)


@mcp_tool(
    name="logout",
    description="Clear Mattermost authentication and logout",
    input_schema={"type": "object", "properties": {}, "required": []},
)
async def _logout_tool(**kwargs):
    """MCP tool wrapper for logout function."""
    return await logout(**kwargs)
