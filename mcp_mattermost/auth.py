"""
Authentication handler for Mattermost MCP server.

This module provides secure authentication handling for the MCP server,
allowing credentials to be provided dynamically by the MCP client (Warp)
instead of requiring them to be hardcoded in environment variables.
"""

from typing import Any, Dict, Optional

import structlog

from .api.client import AsyncHTTPClient
from .api.exceptions import MattermostAPIError

logger = structlog.get_logger(__name__)


class AuthenticationState:
    """Manages authentication state for the Mattermost MCP server."""

    def __init__(self):
        """Initialize authentication state."""
        self.mattermost_url: Optional[str] = None
        self.token: Optional[str] = None
        self.team_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None
        self.is_authenticated = False
        self._http_client: Optional[AsyncHTTPClient] = None

        # Authentication callbacks
        self._auth_callbacks: list = []

    async def authenticate(
        self,
        mattermost_url: str,
        token: str,
        team_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Authenticate with Mattermost and validate credentials.

        Args:
            mattermost_url: Mattermost server URL
            token: API token
            team_id: Optional team ID

        Returns:
            Dict containing authentication result and user info

        Raises:
            MattermostAPIError: If authentication fails
        """
        logger.info(
            "Attempting authentication",
            url=mattermost_url,
            team_id=team_id,
        )

        try:
            # Clean up existing client
            if self._http_client:
                await self._http_client.close()

            # Create new HTTP client with provided credentials
            self.mattermost_url = mattermost_url.rstrip("/")
            self.token = token
            self.team_id = team_id

            self._http_client = AsyncHTTPClient(
                f"{self.mattermost_url}/api/v4", self.token
            )

            # Validate credentials by getting user info
            user_data = await self._http_client.get("/users/me")

            self.user_id = user_data.get("id")
            self.username = user_data.get("username")
            self.is_authenticated = True

            logger.info(
                "Authentication successful",
                user_id=self.user_id,
                username=self.username,
            )

            # Notify callbacks about successful authentication
            await self._notify_auth_callbacks()

            return {
                "success": True,
                "user_id": self.user_id,
                "username": self.username,
                "mattermost_url": self.mattermost_url,
                "team_id": self.team_id,
            }

        except Exception as e:
            logger.error(
                "Authentication failed",
                error=str(e),
                error_type=type(e).__name__,
            )

            # Reset authentication state on failure
            await self.clear_authentication()

            raise MattermostAPIError(
                f"Authentication failed: {str(e)}",
                status_code=getattr(e, "status_code", 401),
            )

    async def clear_authentication(self) -> None:
        """Clear authentication state and cleanup resources."""
        logger.info("Clearing authentication state")

        if self._http_client:
            await self._http_client.close()
            self._http_client = None

        self.mattermost_url = None
        self.token = None
        self.team_id = None
        self.user_id = None
        self.username = None
        self.is_authenticated = False

    def get_http_client(self) -> Optional[AsyncHTTPClient]:
        """
        Get the authenticated HTTP client.

        Returns:
            AsyncHTTPClient instance if authenticated, None otherwise
        """
        if not self.is_authenticated:
            return None
        return self._http_client

    def require_authentication(self) -> None:
        """
        Ensure authentication is present.

        Raises:
            MattermostAPIError: If not authenticated
        """
        if not self.is_authenticated:
            raise MattermostAPIError(
                "Authentication required. Please provide Mattermost credentials.",
                status_code=401,
            )

    def add_auth_callback(self, callback) -> None:
        """
        Add a callback to be called when authentication succeeds.

        Args:
            callback: Async function to call on authentication
        """
        self._auth_callbacks.append(callback)

    def remove_auth_callback(self, callback) -> None:
        """
        Remove an authentication callback.

        Args:
            callback: Callback to remove
        """
        if callback in self._auth_callbacks:
            self._auth_callbacks.remove(callback)

    async def _notify_auth_callbacks(self) -> None:
        """Notify all authentication callbacks."""
        for callback in self._auth_callbacks:
            try:
                await callback(self)
            except Exception as e:
                logger.error(
                    "Error in auth callback",
                    callback=str(callback),
                    error=str(e),
                    exc_info=True,
                )

    @property
    def auth_info(self) -> Dict[str, Any]:
        """
        Get current authentication information.

        Returns:
            Dict containing current auth state
        """
        return {
            "is_authenticated": self.is_authenticated,
            "mattermost_url": self.mattermost_url,
            "user_id": self.user_id,
            "username": self.username,
            "team_id": self.team_id,
        }


# Global authentication state instance
auth_state = AuthenticationState()


def get_auth_state() -> AuthenticationState:
    """Get the global authentication state instance."""
    return auth_state
