"""
Streaming resource for new channel posts in Mattermost.

This resource provides real-time updates for new posts in channels,
supporting both WebSocket streaming and REST polling.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

from ..api.client import AsyncHTTPClient
from ..events.websocket import MattermostWebSocketClient
from ..models.posts import Post
from .base import BaseMCPResource, ResourceUpdate, ResourceUpdateType

logger = structlog.get_logger(__name__)


class NewChannelPostResource(BaseMCPResource):
    """Resource for streaming new channel posts."""
    
    def __init__(
        self,
        mattermost_url: str,
        token: str,
        channel_ids: Optional[List[str]] = None,
        team_id: Optional[str] = None,
    ):
        """
        Initialize the new channel post resource.
        
        Args:
            mattermost_url: Mattermost server URL
            token: API token
            channel_ids: Optional list of channel IDs to monitor (all if None)
            team_id: Optional team ID to scope to
        """
        super().__init__(
            name="new_channel_posts",
            description="Real-time stream of new posts in Mattermost channels",
            mime_type="application/json"
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
        self._last_post_times: Dict[str, int] = {}  # channel_id -> timestamp
        
        logger.info(
            "Initialized new channel post resource",
            channels=len(channel_ids) if channel_ids else "all",
            team_id=team_id
        )
    
    def supports_streaming(self) -> bool:
        """This resource supports WebSocket streaming."""
        return True
    
    def supports_polling(self) -> bool:
        """This resource supports REST polling."""
        return True
    
    async def read(self, uri: str, **kwargs) -> Dict[str, Any]:
        """Read current state - returns recent posts from channels."""
        if not self._http_client:
            self._http_client = AsyncHTTPClient(self.mattermost_url, self.token)
        
        try:
            # Get channels to read from
            channels_to_read = []
            
            if self.channel_ids:
                channels_to_read = list(self.channel_ids)
            elif self.team_id:
                # Get all channels for the team
                channels_data = await self._http_client.get(f"/teams/{self.team_id}/channels")
                channels_to_read = [ch["id"] for ch in channels_data]
            
            # Get recent posts from each channel
            recent_posts = []
            for channel_id in channels_to_read:
                try:
                    posts_data = await self._http_client.get(
                        f"/channels/{channel_id}/posts",
                        params={"per_page": 10}
                    )
                    
                    if "posts" in posts_data:
                        for post_data in posts_data["posts"].values():
                            post = Post(**post_data)
                            recent_posts.append(post.model_dump())
                            
                except Exception as e:
                    logger.warning("Failed to get posts for channel", channel_id=channel_id, error=str(e))
            
            # Sort by creation time
            recent_posts.sort(key=lambda p: p.get("create_at", 0), reverse=True)
            
            return {
                "resource_uri": self.uri,
                "posts": recent_posts[:50],  # Limit to 50 most recent
                "timestamp": datetime.utcnow().isoformat(),
                "channels_monitored": len(channels_to_read),
            }
            
        except Exception as e:
            logger.error("Error reading new channel posts", error=str(e))
            return {
                "resource_uri": self.uri,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _start_streaming(self, **kwargs) -> None:
        """Start WebSocket streaming for new posts."""
        logger.info("Starting WebSocket streaming for new channel posts")
        
        self._ws_client = MattermostWebSocketClient(
            self.mattermost_url,
            self.token,
            auto_reconnect=True
        )
        
        # Register event handler for new posts
        self._ws_client.on_event("posted", self._handle_new_post_event)
        
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
        
        logger.info("WebSocket streaming started for new channel posts")
    
    async def _stop_streaming(self) -> None:
        """Stop WebSocket streaming."""
        if self._ws_client:
            await self._ws_client.disconnect()
            self._ws_client = None
        logger.info("WebSocket streaming stopped for new channel posts")
    
    def _handle_new_post_event(self, event_data: Dict[str, Any]) -> None:
        """Handle new post WebSocket event."""
        try:
            post_data = event_data.get("data", {})
            broadcast = event_data.get("broadcast", {})
            
            channel_id = post_data.get("channel_id") or broadcast.get("channel_id")
            
            # Filter by channel if specified
            if self.channel_ids and channel_id not in self.channel_ids:
                return
            
            # Create post object
            post = Post(**post_data)
            
            # Create resource update
            update = ResourceUpdate(
                resource_uri=self.uri,
                update_type=ResourceUpdateType.CREATED,
                data={
                    "post": post.model_dump(),
                    "channel_id": channel_id,
                    "user_id": post.user_id,
                },
                event_id=f"post_{post.id}"
            )
            
            # Emit the update (async call from sync handler)
            asyncio.create_task(self.emit_update(update))
            
            logger.debug(
                "New post event processed",
                post_id=post.id,
                channel_id=channel_id,
                user_id=post.user_id
            )
            
        except Exception as e:
            logger.error("Error handling new post event", error=str(e), exc_info=True)
    
    async def _poll_for_updates(self, **kwargs) -> None:
        """Poll for new posts using REST API."""
        if not self._http_client:
            self._http_client = AsyncHTTPClient(self.mattermost_url, self.token)
        
        logger.debug("Polling for new channel posts")
        
        try:
            # Get channels to poll
            channels_to_poll = []
            
            if self.channel_ids:
                channels_to_poll = list(self.channel_ids)
            elif self.team_id:
                # Get all channels for the team
                channels_data = await self._http_client.get(f"/teams/{self.team_id}/channels")
                channels_to_poll = [ch["id"] for ch in channels_data]
            
            # Poll each channel for new posts
            for channel_id in channels_to_poll:
                await self._poll_channel_posts(channel_id)
                
        except Exception as e:
            logger.error("Error polling for new posts", error=str(e))
    
    async def _poll_channel_posts(self, channel_id: str) -> None:
        """Poll a specific channel for new posts."""
        try:
            # Get the last post timestamp for this channel
            since_timestamp = self._last_post_times.get(channel_id, 0)
            
            # Get recent posts
            posts_data = await self._http_client.get(
                f"/channels/{channel_id}/posts",
                params={
                    "per_page": 20,
                    "since": since_timestamp
                }
            )
            
            if "posts" not in posts_data:
                return
            
            # Process new posts
            new_posts = []
            latest_timestamp = since_timestamp
            
            for post_data in posts_data["posts"].values():
                post = Post(**post_data)
                
                # Only include posts newer than our last timestamp
                if post.create_at and post.create_at > since_timestamp:
                    new_posts.append(post)
                    latest_timestamp = max(latest_timestamp, post.create_at)
            
            # Update last timestamp
            if latest_timestamp > since_timestamp:
                self._last_post_times[channel_id] = latest_timestamp
            
            # Sort by creation time (oldest first)
            new_posts.sort(key=lambda p: p.create_at or 0)
            
            # Emit updates for new posts
            for post in new_posts:
                update = ResourceUpdate(
                    resource_uri=self.uri,
                    update_type=ResourceUpdateType.CREATED,
                    data={
                        "post": post.model_dump(),
                        "channel_id": channel_id,
                        "user_id": post.user_id,
                    },
                    event_id=f"post_{post.id}"
                )
                
                await self.emit_update(update)
            
            if new_posts:
                logger.debug(
                    "Found new posts in polling",
                    channel_id=channel_id,
                    count=len(new_posts)
                )
                
        except Exception as e:
            logger.warning(
                "Error polling channel for posts",
                channel_id=channel_id,
                error=str(e)
            )
