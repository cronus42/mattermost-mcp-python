"""
Base classes for MCP resource implementations with streaming capabilities.

This module provides base classes for MCP resources that can emit updates
through WebSocket events or periodic polling.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import structlog
from mcp.types import Resource
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ResourceUpdateType(str, Enum):
    """Types of resource updates."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    REACTION_ADDED = "reaction_added"
    REACTION_REMOVED = "reaction_removed"


@dataclass
class ResourceUpdate:
    """Represents a resource update event."""

    resource_uri: str
    update_type: ResourceUpdateType
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    event_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "resource_uri": self.resource_uri,
            "update_type": self.update_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "event_id": self.event_id,
        }


class MCPResourceDefinition(BaseModel):
    """MCP resource definition."""

    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: str = Field(..., description="Resource description")
    mime_type: str = Field(default="application/json", description="MIME type")
    supports_streaming: bool = Field(
        default=False, description="Supports streaming updates"
    )
    supports_polling: bool = Field(
        default=False, description="Supports polling updates"
    )


class BaseMCPResource(ABC):
    """Abstract base class for MCP resources with streaming/polling support."""

    def __init__(
        self, name: str, description: str, mime_type: str = "application/json"
    ):
        self.name = name
        self.description = description
        self.mime_type = mime_type
        self._subscribers: Set[Callable[[ResourceUpdate], None]] = set()
        self._is_streaming = False
        self._polling_task: Optional[asyncio.Task] = None
        self._last_poll_time: Optional[datetime] = None

    @property
    def uri(self) -> str:
        """Get the resource URI."""
        return f"mattermost://{self.name}"

    def get_definition(self) -> MCPResourceDefinition:
        """Get the resource definition."""
        return MCPResourceDefinition(
            uri=self.uri,
            name=self.name,
            description=self.description,
            mime_type=self.mime_type,
            supports_streaming=self.supports_streaming(),
            supports_polling=self.supports_polling(),
        )

    @abstractmethod
    async def read(self, uri: str, **kwargs) -> Dict[str, Any]:
        """Read resource data by URI."""
        pass

    def supports_streaming(self) -> bool:
        """Whether this resource supports streaming updates."""
        return False

    def supports_polling(self) -> bool:
        """Whether this resource supports polling updates."""
        return False

    def subscribe(self, callback: Callable[[ResourceUpdate], None]) -> None:
        """Subscribe to resource updates."""
        self._subscribers.add(callback)
        logger.info(
            "Subscriber added",
            resource=self.name,
            total_subscribers=len(self._subscribers),
        )

    def unsubscribe(self, callback: Callable[[ResourceUpdate], None]) -> None:
        """Unsubscribe from resource updates."""
        self._subscribers.discard(callback)
        logger.info(
            "Subscriber removed",
            resource=self.name,
            total_subscribers=len(self._subscribers),
        )

    async def emit_update(self, update: ResourceUpdate) -> None:
        """Emit a resource update to all subscribers."""
        if not self._subscribers:
            return

        logger.debug(
            "Emitting resource update",
            resource=self.name,
            update_type=update.update_type,
            subscribers=len(self._subscribers),
        )

        for callback in self._subscribers.copy():
            try:
                callback(update)
            except Exception as e:
                logger.error(
                    "Error in resource update callback",
                    resource=self.name,
                    error=str(e),
                    exc_info=True,
                )

    async def start_streaming(self, **kwargs) -> None:
        """Start streaming updates (if supported)."""
        if not self.supports_streaming():
            raise NotImplementedError(
                f"Resource {self.name} does not support streaming"
            )

        if self._is_streaming:
            logger.warning("Already streaming", resource=self.name)
            return

        self._is_streaming = True
        logger.info("Starting streaming", resource=self.name)

        try:
            await self._start_streaming(**kwargs)
        except Exception as e:
            logger.error("Error starting streaming", resource=self.name, error=str(e))
            self._is_streaming = False
            raise

    async def stop_streaming(self) -> None:
        """Stop streaming updates."""
        if not self._is_streaming:
            return

        self._is_streaming = False
        logger.info("Stopping streaming", resource=self.name)

        await self._stop_streaming()

    async def start_polling(self, interval_seconds: float = 30.0, **kwargs) -> None:
        """Start polling for updates."""
        if not self.supports_polling():
            raise NotImplementedError(f"Resource {self.name} does not support polling")

        if self._polling_task and not self._polling_task.done():
            logger.warning("Already polling", resource=self.name)
            return

        logger.info("Starting polling", resource=self.name, interval=interval_seconds)
        self._polling_task = asyncio.create_task(
            self._polling_loop(interval_seconds, **kwargs)
        )

    async def stop_polling(self) -> None:
        """Stop polling for updates."""
        if self._polling_task and not self._polling_task.done():
            logger.info("Stopping polling", resource=self.name)
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            self._polling_task = None

    async def _start_streaming(self, **kwargs) -> None:
        """Override to implement streaming logic."""
        pass

    async def _stop_streaming(self) -> None:
        """Override to implement streaming stop logic."""
        pass

    async def _polling_loop(self, interval_seconds: float, **kwargs) -> None:
        """Polling loop implementation."""
        while True:
            try:
                await asyncio.sleep(interval_seconds)

                if not self._subscribers:
                    continue

                await self._poll_for_updates(**kwargs)
                self._last_poll_time = datetime.utcnow()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in polling loop", resource=self.name, error=str(e))
                await asyncio.sleep(min(interval_seconds * 2, 300))  # Back off on error

    async def _poll_for_updates(self, **kwargs) -> None:
        """Override to implement polling logic."""
        pass


class MCPResourceRegistry:
    """Registry for MCP resources."""

    def __init__(self):
        self._resources: Dict[str, BaseMCPResource] = {}

    def register(self, resource: BaseMCPResource) -> None:
        """Register a resource."""
        self._resources[resource.uri] = resource
        logger.info("Registered resource", uri=resource.uri, name=resource.name)

    def unregister(self, uri: str) -> None:
        """Unregister a resource."""
        if uri in self._resources:
            resource = self._resources.pop(uri)
            logger.info("Unregistered resource", uri=uri, name=resource.name)

    def get(self, uri: str) -> Optional[BaseMCPResource]:
        """Get a resource by URI."""
        return self._resources.get(uri)

    def list_resources(self) -> List[MCPResourceDefinition]:
        """List all registered resources."""
        return [resource.get_definition() for resource in self._resources.values()]

    def list_mcp_resources(self) -> List[Resource]:
        """List all resources in MCP Resource format."""
        mcp_resources = []
        for resource in self._resources.values():
            definition = resource.get_definition()
            mcp_resource = Resource(
                uri=definition.uri,
                name=definition.name,
                description=definition.description,
                mimeType=definition.mime_type,
            )
            mcp_resources.append(mcp_resource)
        return mcp_resources

    def get_streaming_resources(self) -> List[BaseMCPResource]:
        """Get all resources that support streaming."""
        return [r for r in self._resources.values() if r.supports_streaming()]

    def get_polling_resources(self) -> List[BaseMCPResource]:
        """Get all resources that support polling."""
        return [r for r in self._resources.values() if r.supports_polling()]

    async def start_all_streaming(self, **kwargs) -> None:
        """Start streaming for all supported resources."""
        streaming_resources = self.get_streaming_resources()
        if not streaming_resources:
            logger.info("No streaming resources to start")
            return

        logger.info(
            "Starting streaming for all resources", count=len(streaming_resources)
        )

        tasks = []
        for resource in streaming_resources:
            task = asyncio.create_task(resource.start_streaming(**kwargs))
            tasks.append(task)

        # Wait for all to start, but don't fail if some fail
        results = await asyncio.gather(*tasks, return_exceptions=True)

        failures = [r for r in results if isinstance(r, Exception)]
        if failures:
            logger.warning(
                "Some streaming resources failed to start", failures=len(failures)
            )

    async def stop_all_streaming(self) -> None:
        """Stop streaming for all resources."""
        streaming_resources = self.get_streaming_resources()
        if not streaming_resources:
            return

        logger.info(
            "Stopping streaming for all resources", count=len(streaming_resources)
        )

        tasks = [resource.stop_streaming() for resource in streaming_resources]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def start_all_polling(self, interval_seconds: float = 30.0, **kwargs) -> None:
        """Start polling for all supported resources."""
        polling_resources = self.get_polling_resources()
        if not polling_resources:
            logger.info("No polling resources to start")
            return

        logger.info(
            "Starting polling for all resources",
            count=len(polling_resources),
            interval=interval_seconds,
        )

        tasks = []
        for resource in polling_resources:
            task = asyncio.create_task(
                resource.start_polling(interval_seconds, **kwargs)
            )
            tasks.append(task)

        # Wait for all to start, but don't fail if some fail
        results = await asyncio.gather(*tasks, return_exceptions=True)

        failures = [r for r in results if isinstance(r, Exception)]
        if failures:
            logger.warning(
                "Some polling resources failed to start", failures=len(failures)
            )

    async def stop_all_polling(self) -> None:
        """Stop polling for all resources."""
        polling_resources = self.get_polling_resources()
        if not polling_resources:
            return

        logger.info("Stopping polling for all resources", count=len(polling_resources))

        tasks = [resource.stop_polling() for resource in polling_resources]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def cleanup(self) -> None:
        """Cleanup all resources."""
        logger.info("Cleaning up resource registry")
        await self.stop_all_streaming()
        await self.stop_all_polling()
