"""
Streaming resource for reaction events in Mattermost.

This resource provides real-time updates for reactions being added or removed,
supporting both WebSocket streaming and REST polling.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import structlog

from ..api.client import AsyncHTTPClient
from ..events.websocket import MattermostWebSocketClient
from .base import BaseMCPResource, ResourceUpdate, ResourceUpdateType

logger = structlog.get_logger(__name__)


class ReactionResource(BaseMCPResource):
    """Resource for streaming reaction events."""

    def __init__(
        self,
        mattermost_url: str,
        token: str,
        channel_ids: Optional[List[str]] = None,
        team_id: Optional[str] = None,
    ):
        """
        Initialize the reaction resource.

        Args:
            mattermost_url: Mattermost server URL
            token: API token
            channel_ids: Optional list of channel IDs to monitor (all if None)
            team_id: Optional team ID to scope to
        """
        super().__init__(
            name="reactions",
            description="Real-time stream of reaction events in Mattermost",
            mime_type="application/json",
        )

        self.mattermost_url = mattermost_url
        self.token = token
        self.channel_ids = set(channel_ids) if channel_ids else None
        self.team_id = team_id

        # WebSocket client for streaming
        self._ws_client: Optional[MattermostWebSocketClient] = None

        # HTTP client for polling
        self._http_client: Optional[AsyncHTTPClient] = None

        # State tracking for polling
        self._known_reactions: Set[str] = set()  # post_id:user_id:emoji_name
        self._last_poll_time: Optional[datetime] = None

        logger.info(
            "Initialized reaction resource",
            channels=len(channel_ids) if channel_ids else "all",
            team_id=team_id,
        )

    def supports_streaming(self) -> bool:
        """This resource supports WebSocket streaming."""
        return True

    def supports_polling(self) -> bool:
        """This resource supports REST polling."""
        return True

    async def read(self, uri: str, **kwargs) -> Dict[str, Any]:
        """Read current state - returns recent reactions."""
        if not self._http_client:
            self._http_client = AsyncHTTPClient(self.mattermost_url, self.token)

        try:
            # Get recent posts with reactions
            recent_reactions = []

            # Get channels to read from
            channels_to_read = []

            if self.channel_ids:
                channels_to_read = list(self.channel_ids)
            elif self.team_id:
                # Get all channels for the team
                channels_data = await self._http_client.get(
                    f"/teams/{self.team_id}/channels"
                )
                channels_to_read = [ch["id"] for ch in channels_data]

            # Get recent posts and their reactions
            for channel_id in channels_to_read:
                try:
                    posts_data = await self._http_client.get(
                        f"/channels/{channel_id}/posts", params={"per_page": 20}
                    )

                    if "posts" not in posts_data:
                        continue

                    # Check each post for reactions
                    for post_data in posts_data["posts"].values():
                        post_id = post_data.get("id")
                        if not post_id:
                            continue

                        # Get reactions for this post
                        try:
                            reactions_data = await self._http_client.get(
                                f"/posts/{post_id}/reactions"
                            )

                            for reaction in reactions_data:
                                recent_reactions.append(
                                    {
                                        "post_id": post_id,
                                        "user_id": reaction.get("user_id"),
                                        "emoji_name": reaction.get("emoji_name"),
                                        "create_at": reaction.get("create_at"),
                                        "channel_id": channel_id,
                                    }
                                )

                        except Exception as e:
                            logger.debug(
                                "Failed to get reactions for post",
                                post_id=post_id,
                                error=str(e),
                            )

                except Exception as e:
                    logger.warning(
                        "Failed to get posts for channel",
                        channel_id=channel_id,
                        error=str(e),
                    )

            # Sort by creation time
            recent_reactions.sort(key=lambda r: r.get("create_at", 0), reverse=True)

            return {
                "resource_uri": self.uri,
                "reactions": recent_reactions[:100],  # Limit to 100 most recent
                "timestamp": datetime.utcnow().isoformat(),
                "channels_monitored": len(channels_to_read),
            }

        except Exception as e:
            logger.error("Error reading reactions", error=str(e))
            return {
                "resource_uri": self.uri,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _start_streaming(self, **kwargs) -> None:
        """Start WebSocket streaming for reaction events."""
        logger.info("Starting WebSocket streaming for reactions")

        self._ws_client = MattermostWebSocketClient(
            self.mattermost_url, self.token, auto_reconnect=True
        )

        # Register event handlers for reactions
        self._ws_client.on_event("reaction_added", self._handle_reaction_added_event)
        self._ws_client.on_event(
            "reaction_removed", self._handle_reaction_removed_event
        )

        # Connect to WebSocket
        await self._ws_client.connect()

        # Wait for connection to be established
        max_wait = 10.0
        wait_time = 0.0
        while not self._ws_client.is_connected and wait_time < max_wait:
            await asyncio.sleep(0.1)
            wait_time += 0.1

        if not self._ws_client.is_connected:
            raise RuntimeError("Failed to establish WebSocket connection")

        logger.info("WebSocket streaming started for reactions")

    async def _stop_streaming(self) -> None:
        """Stop WebSocket streaming."""
        if self._ws_client:
            await self._ws_client.disconnect()
            self._ws_client = None
        logger.info("WebSocket streaming stopped for reactions")

    def _handle_reaction_added_event(self, event_data: Dict[str, Any]) -> None:
        """Handle reaction added WebSocket event."""
        try:
            reaction_data = event_data.get("data", {})
            broadcast = event_data.get("broadcast", {})

            channel_id = broadcast.get("channel_id")

            # Filter by channel if specified
            if self.channel_ids and channel_id not in self.channel_ids:
                return

            # Create resource update
            update = ResourceUpdate(
                resource_uri=self.uri,
                update_type=ResourceUpdateType.REACTION_ADDED,
                data={
                    "reaction": reaction_data,
                    "channel_id": channel_id,
                    "post_id": reaction_data.get("post_id"),
                    "user_id": reaction_data.get("user_id"),
                    "emoji_name": reaction_data.get("emoji_name"),
                },
                event_id=f"reaction_{reaction_data.get('post_id')}_{reaction_data.get('user_id')}_{reaction_data.get('emoji_name')}",
            )

            # Emit the update (async call from sync handler)
            asyncio.create_task(self.emit_update(update))

            logger.debug(
                "Reaction added event processed",
                post_id=reaction_data.get("post_id"),
                emoji_name=reaction_data.get("emoji_name"),
                user_id=reaction_data.get("user_id"),
            )

        except Exception as e:
            logger.error(
                "Error handling reaction added event", error=str(e), exc_info=True
            )

    def _handle_reaction_removed_event(self, event_data: Dict[str, Any]) -> None:
        """Handle reaction removed WebSocket event."""
        try:
            reaction_data = event_data.get("data", {})
            broadcast = event_data.get("broadcast", {})

            channel_id = broadcast.get("channel_id")

            # Filter by channel if specified
            if self.channel_ids and channel_id not in self.channel_ids:
                return

            # Create resource update
            update = ResourceUpdate(
                resource_uri=self.uri,
                update_type=ResourceUpdateType.REACTION_REMOVED,
                data={
                    "reaction": reaction_data,
                    "channel_id": channel_id,
                    "post_id": reaction_data.get("post_id"),
                    "user_id": reaction_data.get("user_id"),
                    "emoji_name": reaction_data.get("emoji_name"),
                },
                event_id=f"reaction_removed_{reaction_data.get('post_id')}_{reaction_data.get('user_id')}_{reaction_data.get('emoji_name')}",
            )

            # Emit the update (async call from sync handler)
            asyncio.create_task(self.emit_update(update))

            logger.debug(
                "Reaction removed event processed",
                post_id=reaction_data.get("post_id"),
                emoji_name=reaction_data.get("emoji_name"),
                user_id=reaction_data.get("user_id"),
            )

        except Exception as e:
            logger.error(
                "Error handling reaction removed event", error=str(e), exc_info=True
            )

    async def _poll_for_updates(self, **kwargs) -> None:
        """Poll for reaction changes using REST API."""
        if not self._http_client:
            self._http_client = AsyncHTTPClient(self.mattermost_url, self.token)

        logger.debug("Polling for reaction updates")

        try:
            current_reactions: set[str] = set()

            # Get channels to poll
            channels_to_poll = []

            if self.channel_ids:
                channels_to_poll = list(self.channel_ids)
            elif self.team_id:
                # Get all channels for the team
                channels_data = await self._http_client.get(
                    f"/teams/{self.team_id}/channels"
                )
                channels_to_poll = [ch["id"] for ch in channels_data]

            # Poll each channel for posts and their reactions
            for channel_id in channels_to_poll:
                await self._poll_channel_reactions(channel_id, current_reactions)

            # Detect removed reactions (reactions that were there before but not now)
            if self._last_poll_time:  # Only check after first poll
                removed_reactions = self._known_reactions - current_reactions

                for reaction_key in removed_reactions:
                    post_id, user_id, emoji_name = reaction_key.split(":", 2)

                    update = ResourceUpdate(
                        resource_uri=self.uri,
                        update_type=ResourceUpdateType.REACTION_REMOVED,
                        data={
                            "post_id": post_id,
                            "user_id": user_id,
                            "emoji_name": emoji_name,
                        },
                        event_id=f"reaction_removed_{post_id}_{user_id}_{emoji_name}",
                    )

                    await self.emit_update(update)

            # Update known reactions
            self._known_reactions = current_reactions
            self._last_poll_time = datetime.utcnow()

        except Exception as e:
            logger.error("Error polling for reaction updates", error=str(e))

    async def _poll_channel_reactions(
        self, channel_id: str, current_reactions: Set[str]
    ) -> None:
        """Poll a specific channel for reaction changes."""
        try:
            # Get recent posts
            if not self._http_client:
                return
            posts_data = await self._http_client.get(
                f"/channels/{channel_id}/posts",
                params={"per_page": 50},  # Check more posts for reactions
            )

            if "posts" not in posts_data:
                return

            # Check reactions on each post
            for post_data in posts_data["posts"].values():
                post_id = post_data.get("id")
                if not post_id:
                    continue

                try:
                    if not self._http_client:
                        continue
                    reactions_data = await self._http_client.get(
                        f"/posts/{post_id}/reactions"
                    )

                    for reaction in reactions_data:
                        user_id = reaction.get("user_id")
                        emoji_name = reaction.get("emoji_name")

                        if not user_id or not emoji_name:
                            continue

                        reaction_key = f"{post_id}:{user_id}:{emoji_name}"
                        current_reactions.add(reaction_key)

                        # Check if this is a new reaction
                        if reaction_key not in self._known_reactions:
                            update = ResourceUpdate(
                                resource_uri=self.uri,
                                update_type=ResourceUpdateType.REACTION_ADDED,
                                data={
                                    "reaction": reaction,
                                    "channel_id": channel_id,
                                    "post_id": post_id,
                                    "user_id": user_id,
                                    "emoji_name": emoji_name,
                                },
                                event_id=f"reaction_{post_id}_{user_id}_{emoji_name}",
                            )

                            await self.emit_update(update)

                            logger.debug(
                                "Found new reaction in polling",
                                post_id=post_id,
                                emoji_name=emoji_name,
                                user_id=user_id,
                            )

                except Exception as e:
                    logger.debug(
                        "Failed to get reactions for post",
                        post_id=post_id,
                        error=str(e),
                    )

        except Exception as e:
            logger.warning(
                "Error polling channel for reactions",
                channel_id=channel_id,
                error=str(e),
            )
