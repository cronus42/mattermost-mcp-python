"""
Authentication tools for Mattermost MCP server.

This module provides MCP tools for handling authentication with Mattermost,
allowing the client (Warp) to securely provide credentials at runtime.
"""

from typing import Any, Dict

import structlog

from ..auth import get_auth_state
from .base import BaseMCPTool

logger = structlog.get_logger(__name__)


class AuthenticateTool(BaseMCPTool):
    """Tool for authenticating with Mattermost."""

    def __init__(self):
        """Initialize the authentication tool."""
        super().__init__(
            name="authenticate",
            description="Authenticate with Mattermost using API credentials",
            parameters={
                "type": "object",
                "properties": {
                    "mattermost_url": {
                        "type": "string",
                        "description": (
                            "Mattermost server URL "
                            "(e.g., https://your-mattermost.com)"
                        ),
                    },
                    "token": {
                        "type": "string",
                        "description": "Mattermost API token or bot token",
                    },
                    "team_id": {
                        "type": "string",
                        "description": "Optional team ID to scope operations to",
                        "default": None,
                    },
                },
                "required": ["mattermost_url", "token"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute authentication with provided credentials.

        Args:
            arguments: Dictionary containing mattermost_url, token, and optional team_id

        Returns:
            Authentication result
        """
        mattermost_url = arguments.get("mattermost_url")
        token = arguments.get("token")
        team_id = arguments.get("team_id")

        if not mattermost_url or not token:
            return {
                "success": False,
                "error": (
                    "Missing required parameters: "
                    "mattermost_url and token are required"
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

            return result

        except Exception as e:
            logger.error(
                "Authentication tool failed", error=str(e), error_type=type(e).__name__
            )

            return {"success": False, "error": str(e), "error_type": type(e).__name__}


class GetAuthStatusTool(BaseMCPTool):
    """Tool for checking current authentication status."""

    def __init__(self):
        """Initialize the auth status tool."""
        super().__init__(
            name="get_auth_status",
            description="Get current Mattermost authentication status",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current authentication status.

        Args:
            arguments: Empty dictionary (no parameters required)

        Returns:
            Current authentication status
        """
        auth_state = get_auth_state()
        return auth_state.auth_info


class LogoutTool(BaseMCPTool):
    """Tool for logging out and clearing authentication."""

    def __init__(self):
        """Initialize the logout tool."""
        super().__init__(
            name="logout",
            description="Clear Mattermost authentication and logout",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clear authentication state.

        Args:
            arguments: Empty dictionary (no parameters required)

        Returns:
            Logout result
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
