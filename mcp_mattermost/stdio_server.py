"""
MCP Stdio Server implementation for Mattermost integration.

This module provides a stdio-based MCP server that handles JSON-RPC communication
over stdin/stdout for the Model Context Protocol.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional, Union

import structlog
from mcp import ResourceUpdatedNotification
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    GetPromptRequest,
    InitializeRequest,
    ListPromptsRequest,
    ListResourcesRequest,
    ListToolsRequest,
    ReadResourceRequest,
    SetLevelRequest,
)

from .server import MattermostMCPServer

# Import tool modules to register them
from .tools import auth, channels, messaging
from .tools.auth import check_authentication
from .tools.base import get_registry

logger = structlog.get_logger(__name__)


class MattermostStdioServer:
    """
    MCP stdio server for Mattermost integration.

    This class implements the Model Context Protocol over stdio transport,
    handling JSON-RPC message parsing and routing to appropriate handlers.
    """

    def __init__(
        self,
        team_id: Optional[str] = None,
        enable_streaming: bool = True,
        enable_polling: bool = True,
        polling_interval: float = 30.0,
        channel_ids: Optional[List[str]] = None,
        webhook_secret: Optional[str] = None,
        ws_url: Optional[str] = None,
        default_channel: Optional[str] = None,
    ):
        """
        Initialize the MCP stdio server.

        Args:
            team_id: Optional team ID to scope operations to
            enable_streaming: Whether to enable WebSocket streaming
            enable_polling: Whether to enable REST polling
            polling_interval: Polling interval in seconds
            channel_ids: Optional list of channel IDs to monitor
            webhook_secret: Optional webhook secret for validation
            ws_url: Optional WebSocket URL for streaming
            default_channel: Optional default channel ID for operations
        """
        # Initialize the underlying Mattermost MCP server
        self.mattermost_server = MattermostMCPServer(
            team_id=team_id,
            enable_streaming=enable_streaming,
            enable_polling=enable_polling,
            polling_interval=polling_interval,
            channel_ids=channel_ids,
            webhook_secret=webhook_secret,
            ws_url=ws_url,
            default_channel=default_channel,
        )

        # Initialize MCP server
        self.mcp_server = Server("mcp-mattermost")

        # Set resource update callback for streaming events
        self.mattermost_server.set_resource_update_callback(self._send_resource_update_notification)  # type: ignore[arg-type]

        # Resource subscription management
        self._resource_subscriptions: set = set()

        # Setup authentication callback to refresh services
        self._setup_auth_callback()

        self._initialize_services()

        # Setup MCP handlers
        self._setup_handlers()

        # Server state
        self._initialized = False
        self._session: Optional[Any] = None

        logger.info("Mattermost MCP stdio server initialized")

    def _initialize_services(self) -> None:
        """Initialize services for tool dependency injection."""
        from .auth import get_auth_state
        from .services import (
            ChannelsService,
            FilesService,
            PostsService,
            TeamsService,
            UsersService,
        )

        # Get the authenticated HTTP client from auth state
        auth_state = get_auth_state()

        if auth_state.is_authenticated:
            # Use real services with authenticated client
            http_client = auth_state.get_http_client()
            if http_client:
                services = {
                    "posts": PostsService(http_client),
                    "channels": ChannelsService(http_client),
                    "users": UsersService(http_client),
                    "teams": TeamsService(http_client),
                    "files": FilesService(http_client),
                }

                # Register services with the tool registry
                _registry = get_registry()
                _registry.set_services(services)

                logger.info(
                    "Real services initialized for tool registry",
                    services=list(services.keys()),
                )
                return

        # Fallback to minimal services that return auth errors
        class AuthRequiredService:
            async def __getattr__(self, name):
                return lambda *args, **kwargs: {
                    "success": False,
                    "error": "Authentication required",
                    "error_type": "AuthenticationError",
                }

        # Create placeholder services that indicate auth is needed
        auth_service = AuthRequiredService()
        services = {
            "posts": auth_service,  # type: ignore[dict-item]
            "channels": auth_service,  # type: ignore[dict-item]
            "users": auth_service,  # type: ignore[dict-item]
            "teams": auth_service,  # type: ignore[dict-item]
            "files": auth_service,  # type: ignore[dict-item]
        }

        # Register services with the tool registry
        _registry = get_registry()
        _registry.set_services(services)

        logger.info(
            "Placeholder services initialized - authentication required",
            services=list(services.keys()),
        )

    def _setup_auth_callback(self) -> None:
        """Setup callback to refresh services when authentication changes."""
        from .auth import get_auth_state

        auth_state = get_auth_state()

        async def on_auth_success(auth_state_instance):
            """Callback to refresh services after successful authentication."""
            logger.info("Authentication successful, refreshing services")
            self._initialize_services()

        auth_state.add_auth_callback(on_auth_success)
        logger.debug("Auth callback registered for service refresh")

    def _setup_handlers(self) -> None:
        """Set up MCP protocol handlers."""

        @self.mcp_server.list_tools()
        async def handle_list_tools() -> List[Dict[str, Any]]:
            """Handle list_tools requests."""
            logger.debug("Handling list_tools request")
            try:
                # Get tools from the tool registry
                _registry = get_registry()
                tools = _registry.list_tools()
                logger.debug("Listed tools from registry", count=len(tools))
                return tools
            except Exception as e:
                logger.error("Error listing tools", error=str(e), exc_info=True)
                raise

        @self.mcp_server.list_resources()
        async def handle_list_resources() -> List[Dict[str, Any]]:
            """Handle list_resources requests."""
            logger.debug("Handling list_resources request")
            try:
                resources = self.mattermost_server.get_resources()
                logger.debug("Listed resources", count=len(resources))
                return resources
            except Exception as e:
                logger.error("Error listing resources", error=str(e), exc_info=True)
                raise

        @self.mcp_server.read_resource()
        async def handle_read_resource(uri: str) -> Dict[str, Any]:
            """Handle read_resource requests."""
            logger.debug("Handling read_resource request", uri=uri)
            try:
                # Check authentication for resource access
                auth_status = check_authentication()
                if not auth_status.get("authenticated", False):
                    raise RuntimeError(
                        f"Authentication required: {auth_status.get('error')}"
                    )

                resource_data = await self.mattermost_server.read_resource(uri)
                logger.debug("Read resource", uri=uri)
                return resource_data
            except Exception as e:
                logger.error(
                    "Error reading resource", uri=uri, error=str(e), exc_info=True
                )
                raise

        @self.mcp_server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[Dict[str, Any]]:
            """Handle call_tool requests."""
            logger.debug(
                "Handling call_tool request", tool_name=name, arguments=arguments
            )
            try:
                # Skip authentication check for auth tools themselves
                if name not in ["authenticate", "get_auth_status", "logout"]:
                    auth_status = check_authentication()
                    if not auth_status.get("authenticated", False):
                        error_result = {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "success": False,
                                    "error": auth_status.get("error"),
                                    "error_type": auth_status.get("error_type"),
                                },
                                indent=2,
                            ),
                        }
                        return [error_result]

                # Get the tool registry and call the tool
                _registry = get_registry()
                result = await _registry.call_tool(name, arguments)

                # Wrap result in MCP format
                if isinstance(result, dict):
                    # Convert dictionary result to MCP text content
                    text_result = json.dumps(result, indent=2)
                    mcp_result = {"type": "text", "text": text_result}
                elif isinstance(result, str):
                    mcp_result = {"type": "text", "text": result}
                else:
                    # Convert other types to string
                    mcp_result = {"type": "text", "text": str(result)}

                logger.debug(
                    "Tool called successfully",
                    tool_name=name,
                    result_type=type(result).__name__,
                )
                return [mcp_result]

            except Exception as e:
                logger.error(
                    "Error calling tool", tool_name=name, error=str(e), exc_info=True
                )
                # Return error as MCP content
                error_result = {
                    "type": "text",
                    "text": f"Error calling tool '{name}': {str(e)}",
                }
                return [error_result]

    async def _send_resource_update_notification(self, update) -> None:
        """Send MCP ResourceUpdatedNotification to subscribers."""
        try:
            # Only send notifications if we have an active session
            # In MCP, notifications are sent via the session context during requests
            # For now, we'll log the notification and store it for potential future use
            logger.debug(
                "Resource update received",
                resource_uri=update.resource_uri,
                update_type=update.update_type.value,
                data_keys=list(update.data.keys())
                if isinstance(update.data, dict)
                else "non-dict",
            )

            # Note: MCP ResourceUpdatedNotification will be sent when a client subscribes
            # The actual notification sending happens in the context of a client request
            # This callback just tracks that updates are available

        except Exception as e:
            logger.error(
                "Error handling resource update notification",
                error=str(e),
                resource_uri=update.resource_uri,
                exc_info=True,
            )

    async def run(self) -> None:
        """
        Run the MCP stdio server.

        This method starts the server and handles JSON-RPC communication
        over stdin/stdout until shutdown.
        """
        logger.info("Starting MCP stdio server")

        try:
            # Start the underlying Mattermost server
            await self.mattermost_server.start()

            # Run the stdio server using the MCP stdio transport
            async with stdio_server() as (read_stream, write_stream):
                logger.info("MCP stdio server started, waiting for messages")

                # Run the server with stdio streams
                await self.mcp_server.run(
                    read_stream,
                    write_stream,
                    self.mcp_server.create_initialization_options(),
                )

        except Exception as e:
            logger.error("Error in MCP stdio server", error=str(e), exc_info=True)
            raise
        finally:
            # Cleanup
            await self._cleanup()

    async def _cleanup(self) -> None:
        """Cleanup server resources."""
        logger.info("Cleaning up MCP stdio server")

        try:
            if self.mattermost_server.is_running:
                await self.mattermost_server.stop()

            self._session = None
            self._initialized = False

            logger.info("MCP stdio server cleanup completed")

        except Exception as e:
            logger.error("Error during cleanup", error=str(e), exc_info=True)

    @property
    def is_running(self) -> bool:
        """Whether the server is currently running."""
        return self._session is not None and self.mattermost_server.is_running


def create_stdio_server(**kwargs) -> MattermostStdioServer:
    """
    Factory function to create a Mattermost stdio server.

    Args:
        **kwargs: Arguments to pass to MattermostStdioServer

    Returns:
        Configured MattermostStdioServer instance
    """
    return MattermostStdioServer(**kwargs)


async def run_stdio_server(**kwargs) -> None:
    """
    Convenience function to run a Mattermost stdio server.

    Args:
        **kwargs: Arguments to pass to MattermostStdioServer
    """
    server = create_stdio_server(**kwargs)
    await server.run()


if __name__ == "__main__":
    """Entry point for standalone stdio server execution."""

    async def main():
        """Main entry point."""
        import os

        # Get configuration from environment variables
        config = {
            "team_id": os.getenv("MATTERMOST_TEAM_ID"),
            "enable_streaming": os.getenv("ENABLE_STREAMING", "true").lower() == "true",
            "enable_polling": os.getenv("ENABLE_POLLING", "true").lower() == "true",
            "polling_interval": float(os.getenv("POLLING_INTERVAL", "30.0")),
            "webhook_secret": os.getenv("WEBHOOK_SECRET"),
            "ws_url": os.getenv("WEBSOCKET_URL"),
            "default_channel": os.getenv("DEFAULT_CHANNEL_ID"),
        }

        # Parse channel IDs if provided
        channel_ids_str = os.getenv("CHANNEL_IDS")
        if channel_ids_str:
            config["channel_ids"] = [
                cid.strip() for cid in channel_ids_str.split(",") if cid.strip()
            ]

        # Filter out None values
        config = {k: v for k, v in config.items() if v is not None}

        logger.info("Starting MCP stdio server with configuration", **config)

        try:
            await run_stdio_server(**config)
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down")
        except Exception as e:
            logger.error("Unexpected error", error=str(e), exc_info=True)
            sys.exit(1)

    # Run the server
    asyncio.run(main())
