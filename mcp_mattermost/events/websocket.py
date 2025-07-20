"""
WebSocket client for Mattermost real-time events.

This module provides a WebSocket client that connects to the Mattermost WebSocket API
to receive real-time events like new posts, reactions, and other activities.
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, cast
from urllib.parse import urljoin, urlparse

import structlog
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from websockets.legacy.client import WebSocketClientProtocol

logger = structlog.get_logger(__name__)


@dataclass
class WebSocketMessage:
    """Represents a WebSocket message."""

    seq: Optional[int] = None
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    event: Optional[str] = None
    broadcast: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    seq_reply: Optional[int] = None
    error: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebSocketMessage":
        """Create from dictionary."""
        return cls(
            seq=data.get("seq"),
            action=data.get("action"),
            data=data.get("data"),
            event=data.get("event"),
            broadcast=data.get("broadcast"),
            status=data.get("status"),
            seq_reply=data.get("seq_reply"),
            error=data.get("error"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        for key, value in {
            "seq": self.seq,
            "action": self.action,
            "data": self.data,
            "event": self.event,
            "broadcast": self.broadcast,
            "status": self.status,
            "seq_reply": self.seq_reply,
            "error": self.error,
        }.items():
            if value is not None:
                result[key] = value
        return result


class MattermostWebSocketClient:
    """WebSocket client for Mattermost real-time events."""

    def __init__(
        self,
        mattermost_url: str,
        token: str,
        auto_reconnect: bool = True,
        reconnect_delay: float = 5.0,
        max_reconnect_attempts: int = 10,
    ):
        """Initialize WebSocket client.

        Args:
            mattermost_url: Base Mattermost URL (http/https)
            token: Authentication token
            auto_reconnect: Whether to automatically reconnect on disconnection
            reconnect_delay: Delay between reconnection attempts
            max_reconnect_attempts: Maximum number of reconnection attempts
        """
        self.mattermost_url = mattermost_url.rstrip("/")
        self.token = token
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        # WebSocket connection
        self._websocket: Optional[WebSocketClientProtocol] = None
        self._connection_task: Optional[asyncio.Task] = None
        self._is_connected = False
        self._is_authenticated = False
        self._reconnect_attempts = 0
        self._seq_counter = 0

        # Event handlers
        self._event_handlers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self._message_handlers: Dict[int, Callable[[Dict[str, Any]], None]] = {}

        # Build WebSocket URL
        parsed = urlparse(self.mattermost_url)
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        self.ws_url = f"{ws_scheme}://{parsed.netloc}{parsed.path}/api/v4/websocket"

        logger.info("Initialized Mattermost WebSocket client", ws_url=self.ws_url)

    @property
    def is_connected(self) -> bool:
        """Whether the WebSocket is connected."""
        return self._is_connected and self._is_authenticated

    def on_event(
        self, event_type: str, handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Register an event handler.

        Args:
            event_type: Event type to listen for (e.g., 'posted', 'reaction_added')
            handler: Handler function that takes event data
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.debug("Registered event handler", event_type=event_type)

    def remove_event_handler(
        self, event_type: str, handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Remove an event handler."""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
                logger.debug("Removed event handler", event_type=event_type)
            except ValueError:
                pass

    async def connect(self) -> None:
        """Connect to the WebSocket."""
        if self._connection_task and not self._connection_task.done():
            logger.warning("Already connecting")
            return

        logger.info("Connecting to Mattermost WebSocket", url=self.ws_url)
        self._connection_task = asyncio.create_task(self._connection_loop())

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket."""
        logger.info("Disconnecting from Mattermost WebSocket")

        self.auto_reconnect = False  # Prevent reconnection

        if self._connection_task:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass
            self._connection_task = None

        if self._websocket:
            await self._websocket.close()
            self._websocket = None

        self._is_connected = False
        self._is_authenticated = False

        logger.info("Disconnected from Mattermost WebSocket")

    async def send_message(self, message: WebSocketMessage) -> None:
        """Send a message through the WebSocket."""
        if not self._websocket or not self._is_connected:
            raise RuntimeError("WebSocket not connected")

        if message.seq is None:
            self._seq_counter += 1
            message.seq = self._seq_counter

        data = json.dumps(message.to_dict())
        await self._websocket.send(data)
        logger.debug("Sent WebSocket message", seq=message.seq, action=message.action)

    async def send_user_typing(self, channel_id: str, parent_id: str = "") -> None:
        """Send user typing notification."""
        message = WebSocketMessage(
            action="user_typing",
            data={
                "channel_id": channel_id,
                "parent_id": parent_id,
            },
        )
        await self.send_message(message)

    async def _connection_loop(self) -> None:
        """Main connection loop with auto-reconnect."""
        while True:
            try:
                await self._connect_websocket()
                self._reconnect_attempts = 0  # Reset on successful connection
                await self._message_loop()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("WebSocket connection error", error=str(e), exc_info=True)

                if not self.auto_reconnect:
                    break

                self._reconnect_attempts += 1
                if self._reconnect_attempts > self.max_reconnect_attempts:
                    logger.error("Max reconnect attempts reached, giving up")
                    break

                delay = min(self.reconnect_delay * (2**self._reconnect_attempts), 300)
                logger.info(
                    "Attempting to reconnect",
                    attempt=self._reconnect_attempts,
                    delay=delay,
                )
                await asyncio.sleep(delay)

            finally:
                self._is_connected = False
                self._is_authenticated = False
                if self._websocket:
                    await self._websocket.close()
                    self._websocket = None

    async def _connect_websocket(self) -> None:
        """Connect to the WebSocket and authenticate."""
        logger.debug("Establishing WebSocket connection")

        connection = await websockets.connect(
            self.ws_url,
            ping_interval=30,
            ping_timeout=10,
            close_timeout=10,
        )
        self._websocket = cast(WebSocketClientProtocol, connection)

        self._is_connected = True
        logger.debug("WebSocket connected, authenticating...")

        # Send authentication challenge
        auth_message = WebSocketMessage(
            seq=1, action="authentication_challenge", data={"token": self.token}
        )

        await self.send_message(auth_message)

        # Wait for authentication response
        try:
            if not self._websocket:
                raise RuntimeError("WebSocket not connected")
            response_data = await asyncio.wait_for(self._websocket.recv(), timeout=10.0)
            response = json.loads(response_data)

            if response.get("status") == "OK" and response.get("seq_reply") == 1:
                self._is_authenticated = True
                logger.info("WebSocket authenticated successfully")
            else:
                raise RuntimeError(f"Authentication failed: {response}")

        except asyncio.TimeoutError:
            raise RuntimeError("Authentication timeout")

    async def _message_loop(self) -> None:
        """Main message processing loop."""
        logger.debug("Starting message loop")

        if self._websocket is None:
            raise RuntimeError("WebSocket not connected")
        async for message_data in self._websocket:
            try:
                data = json.loads(message_data)
                message = WebSocketMessage.from_dict(data)
                await self._handle_message(message)

            except json.JSONDecodeError as e:
                logger.warning("Failed to parse WebSocket message", error=str(e))
            except Exception as e:
                logger.error(
                    "Error handling WebSocket message", error=str(e), exc_info=True
                )

    async def _handle_message(self, message: WebSocketMessage) -> None:
        """Handle an incoming WebSocket message."""
        # Handle responses to our requests
        if message.seq_reply and message.seq_reply in self._message_handlers:
            handler = self._message_handlers.pop(message.seq_reply)
            try:
                # Convert message to dict for handler
                handler_data = {
                    "seq": message.seq,
                    "seq_reply": message.seq_reply,
                    "data": message.data,
                    "status": message.status,
                    "error": message.error,
                }
                handler(handler_data)
            except Exception as e:
                logger.error("Error in message response handler", error=str(e))
            return

        # Handle events
        if message.event:
            logger.debug(
                "Received WebSocket event",
                event=message.event,
                channel_id=(
                    message.broadcast.get("channel_id") if message.broadcast else None
                ),
                user_id=message.broadcast.get("user_id") if message.broadcast else None,
            )

            # Call event handlers
            handlers = self._event_handlers.get(message.event, [])
            for handler in handlers:
                try:
                    event_dict = {
                        "event": message.event,
                        "data": message.data or {},
                        "broadcast": message.broadcast or {},
                        "timestamp": time.time(),
                    }
                    handler(event_dict)
                except Exception as e:
                    logger.error(
                        "Error in event handler",
                        event=message.event,
                        error=str(e),
                        exc_info=True,
                    )

            # Special handling for hello event (connection established)
            if message.event == "hello":
                server_version = (
                    message.data.get("server_version") if message.data else None
                )
                logger.info("Received hello event", server_version=server_version)
