"""
MCP Server implementation for Mattermost integration.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

import structlog

from .events import MattermostWebSocketClient
from .metrics import metrics
from .resources import (
    MCPResourceRegistry,
    NewChannelPostResource,
    ReactionResource,
    ResourceUpdate,
)

logger = structlog.get_logger(__name__)


class MattermostMCPServer:
    """
    Main MCP server class for Mattermost integration.

    This class handles the MCP protocol implementation and provides
    tools and resources for interacting with Mattermost, including
    real-time streaming capabilities.
    """

    def __init__(
        self,
        mattermost_url: str,
        mattermost_token: str,
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
        Initialize the Mattermost MCP server.

        Args:
            mattermost_url: The URL of the Mattermost instance
            mattermost_token: API token for authentication
            team_id: Optional team ID to scope operations to
            enable_streaming: Whether to enable WebSocket streaming
            enable_polling: Whether to enable REST polling
            polling_interval: Polling interval in seconds
            channel_ids: Optional list of channel IDs to monitor (all if None)
            webhook_secret: Optional webhook secret for validation
            ws_url: Optional WebSocket URL (overrides default from mattermost_url)
            default_channel: Optional default channel ID for operations
        """
        self.mattermost_url = mattermost_url.rstrip("/")
        self.mattermost_token = mattermost_token
        self.team_id = team_id
        self.enable_streaming = enable_streaming
        self.enable_polling = enable_polling
        self.polling_interval = polling_interval
        self.channel_ids = channel_ids
        self.webhook_secret = webhook_secret
        self.ws_url = ws_url
        self.default_channel = default_channel

        # Resource registry
        self.resource_registry = MCPResourceRegistry()

        # Resource update callback
        self._resource_update_callback: Optional[Callable[[ResourceUpdate], None]] = (
            None
        )

        # WebSocket client for streaming
        self.websocket_client: Optional[MattermostWebSocketClient] = None

        # Server state
        self._is_running = False
        self._startup_tasks: List[asyncio.Task] = []

        # Initialize resources
        self._initialize_resources()

        logger.info(
            "Initializing Mattermost MCP server",
            url=self.mattermost_url,
            team_id=self.team_id,
            streaming=self.enable_streaming,
            polling=self.enable_polling,
            channels=len(channel_ids) if channel_ids else "all",
            webhook_secret_set=bool(self.webhook_secret),
            ws_url=self.ws_url,
            default_channel=self.default_channel,
        )

    def _initialize_resources(self) -> None:
        """Initialize MCP resources."""
        # New channel posts resource
        new_posts_resource = NewChannelPostResource(
            mattermost_url=self.mattermost_url,
            token=self.mattermost_token,
            channel_ids=self.channel_ids,
            team_id=self.team_id,
        )
        self.resource_registry.register(new_posts_resource)

        # Reactions resource
        reactions_resource = ReactionResource(
            mattermost_url=self.mattermost_url,
            token=self.mattermost_token,
            channel_ids=self.channel_ids,
            team_id=self.team_id,
        )
        self.resource_registry.register(reactions_resource)

        # Subscribe to resource updates
        for resource in self.resource_registry._resources.values():
            resource.subscribe(self._handle_resource_update)

    def set_resource_update_callback(
        self, callback: Callable[[ResourceUpdate], None]
    ) -> None:
        """Set callback for resource updates."""
        self._resource_update_callback = callback
        logger.info("Resource update callback set")

    def _handle_resource_update(self, update: ResourceUpdate) -> None:
        """Handle resource updates with metrics tracking."""
        logger.debug(
            "Resource update received",
            resource_uri=update.resource_uri,
            update_type=update.update_type,
            event_id=update.event_id,
        )

        # Record resource update metrics
        resource_type = (
            update.resource_uri.split("/")[-1]
            if "/" in update.resource_uri
            else update.resource_uri
        )
        metrics.record_resource_update(resource_type, update.update_type)

        if self._resource_update_callback:
            try:
                self._resource_update_callback(update)
            except Exception as e:
                logger.error(
                    "Error in resource update callback",
                    error=str(e),
                    error_type=type(e).__name__,
                    resource_uri=update.resource_uri,
                    exc_info=True,
                )
                # Record error metrics
                metrics.record_error(type(e).__name__, update.resource_uri)

    async def start(self) -> None:
        """Start the MCP server and resource streaming/polling."""
        if self._is_running:
            logger.warning("MCP server is already running")
            return

        logger.info("Starting Mattermost MCP server")

        try:
            # Initialize WebSocket client if streaming is enabled
            if self.enable_streaming:
                await self._initialize_websocket_client()

            # Start resource streaming if enabled
            if self.enable_streaming:
                try:
                    await self._start_streaming()
                except Exception as e:
                    logger.error("Failed to start streaming", error=str(e))
                    if not self.enable_polling:
                        raise

            # Start resource polling if enabled
            if self.enable_polling:
                try:
                    await self._start_polling()
                except Exception as e:
                    logger.error("Failed to start polling", error=str(e))
                    if not self.enable_streaming:
                        raise

            self._is_running = True
            logger.info("Mattermost MCP server started successfully")

        except Exception as e:
            logger.error("Failed to start MCP server", error=str(e))
            # Cleanup on failure
            await self._cleanup_on_failure()
            raise

    async def stop(self) -> None:
        """Stop the MCP server and cleanup resources."""
        if not self._is_running:
            logger.warning("MCP server is not running")
            return

        logger.info("Stopping Mattermost MCP server")

        try:
            # Cancel startup tasks if still running
            await self._cancel_startup_tasks()

            # Stop WebSocket client
            if self.websocket_client:
                logger.info("Disconnecting WebSocket client")
                await self.websocket_client.disconnect()
                self.websocket_client = None
                # Update connection metrics
                metrics.set_active_connections(0)

            # Cleanup resources (stops streaming and polling)
            logger.info("Cleaning up resources")
            await self.resource_registry.cleanup()

            self._is_running = False
            logger.info("Mattermost MCP server stopped successfully")

        except Exception as e:
            logger.error("Error during server shutdown", error=str(e), exc_info=True)
            self._is_running = False  # Force state update even on error
            raise

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get the list of available MCP tools.

        Returns:
            List of tool definitions
        """
        # TODO: Implement tool definitions when tools are added
        return []

    def get_resources(self) -> List[Dict[str, Any]]:
        """
        Get the list of available MCP resources.

        Returns:
            List of resource definitions
        """
        return [
            resource.model_dump()
            for resource in self.resource_registry.list_resources()
        ]

    async def read_resource(self, uri: str, **kwargs) -> Dict[str, Any]:
        """
        Read a resource by URI.

        Args:
            uri: Resource URI
            **kwargs: Additional arguments

        Returns:
            Resource data
        """
        resource = self.resource_registry.get(uri)
        if not resource:
            raise ValueError(f"Resource not found: {uri}")

        return await resource.read(uri, **kwargs)

    async def _initialize_websocket_client(self) -> None:
        """Initialize and connect WebSocket client."""
        if self.websocket_client:
            logger.warning("WebSocket client already initialized")
            return

        logger.info("Initializing WebSocket client", url=self.mattermost_url)

        # Use custom WebSocket URL if provided, otherwise derive from Mattermost URL
        websocket_url = self.ws_url or self.mattermost_url

        self.websocket_client = MattermostWebSocketClient(
            mattermost_url=websocket_url,
            token=self.mattermost_token,
            auto_reconnect=True,
            reconnect_delay=5.0,
            max_reconnect_attempts=10,
        )

        # Register WebSocket client with resources that support streaming
        streaming_resources = self.resource_registry.get_streaming_resources()
        for resource in streaming_resources:
            if hasattr(resource, "set_websocket_client"):
                resource.set_websocket_client(self.websocket_client)

        # Connect to WebSocket
        await self.websocket_client.connect()

        # Wait a moment to ensure connection is established
        await asyncio.sleep(1.0)

        if not self.websocket_client.is_connected:
            # Update connection metrics
            metrics.set_active_connections(0)
            raise RuntimeError("Failed to establish WebSocket connection")

        # Update connection metrics
        metrics.set_active_connections(1)

        logger.info("WebSocket client initialized and connected")

    async def _start_streaming(self) -> None:
        """Start resource streaming."""
        logger.info("Starting resource streaming")

        streaming_task = asyncio.create_task(
            self.resource_registry.start_all_streaming()
        )
        self._startup_tasks.append(streaming_task)

        # Wait for streaming to start
        await streaming_task

        logger.info("Resource streaming started")

    async def _start_polling(self) -> None:
        """Start resource polling."""
        logger.info("Starting resource polling", interval=self.polling_interval)

        polling_task = asyncio.create_task(
            self.resource_registry.start_all_polling(
                interval_seconds=self.polling_interval
            )
        )
        self._startup_tasks.append(polling_task)

        # Wait for polling to start
        await polling_task

        logger.info("Resource polling started")

    async def _cancel_startup_tasks(self) -> None:
        """Cancel any running startup tasks."""
        if not self._startup_tasks:
            return

        logger.info("Cancelling startup tasks", count=len(self._startup_tasks))

        for task in self._startup_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete cancellation
        if self._startup_tasks:
            await asyncio.gather(*self._startup_tasks, return_exceptions=True)

        self._startup_tasks.clear()
        logger.info("Startup tasks cancelled")

    async def _cleanup_on_failure(self) -> None:
        """Cleanup resources when startup fails."""
        logger.info("Cleaning up after startup failure")

        try:
            # Cancel startup tasks
            await self._cancel_startup_tasks()

            # Disconnect WebSocket
            if self.websocket_client:
                await self.websocket_client.disconnect()
                self.websocket_client = None

            # Cleanup resources
            await self.resource_registry.cleanup()

        except Exception as e:
            logger.error("Error during cleanup on failure", error=str(e), exc_info=True)

    @property
    def is_running(self) -> bool:
        """Whether the server is currently running."""
        return self._is_running

    @property
    def is_connected(self) -> bool:
        """Whether the WebSocket client is connected."""
        return self.websocket_client is not None and self.websocket_client.is_connected

    def get_metrics(self) -> Optional[str]:
        """
        Get Prometheus metrics in text format.

        Returns:
            Prometheus metrics as text, or None if metrics are disabled
        """
        return metrics.get_metrics()

    def get_metrics_content_type(self) -> str:
        """
        Get the appropriate content type for metrics response.

        Returns:
            Content type string for Prometheus metrics
        """
        return metrics.get_metrics_content_type()
