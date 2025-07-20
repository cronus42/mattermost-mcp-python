"""
Tests for streaming MCP resources.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_mattermost.resources import (
    NewChannelPostResource,
    ReactionResource,
    MCPResourceRegistry,
    ResourceUpdate,
    ResourceUpdateType,
)
from mcp_mattermost.server import MattermostMCPServer


class TestResourceUpdate:
    """Test ResourceUpdate dataclass."""
    
    def test_create_resource_update(self):
        """Test creating a resource update."""
        update = ResourceUpdate(
            resource_uri="test://resource",
            update_type=ResourceUpdateType.CREATED,
            data={"key": "value"},
            event_id="test-event"
        )
        
        assert update.resource_uri == "test://resource"
        assert update.update_type == ResourceUpdateType.CREATED
        assert update.data == {"key": "value"}
        assert update.event_id == "test-event"
        assert isinstance(update.timestamp, float)
    
    def test_to_dict(self):
        """Test converting resource update to dictionary."""
        update = ResourceUpdate(
            resource_uri="test://resource",
            update_type=ResourceUpdateType.CREATED,
            data={"key": "value"},
            event_id="test-event",
            timestamp=1672531200.0
        )
        
        result = update.to_dict()
        expected = {
            "resource_uri": "test://resource",
            "update_type": "created",
            "data": {"key": "value"},
            "event_id": "test-event",
            "timestamp": 1672531200.0,
        }
        
        assert result == expected


class TestNewChannelPostResource:
    """Test NewChannelPostResource class."""
    
    def test_init(self):
        """Test resource initialization."""
        resource = NewChannelPostResource(
            mattermost_url="https://test.com",
            token="test-token",
            channel_ids=["ch1", "ch2"],
            team_id="team1"
        )
        
        assert resource.name == "new_channel_posts"
        assert resource.mattermost_url == "https://test.com"
        assert resource.token == "test-token"
        assert resource.channel_ids == {"ch1", "ch2"}
        assert resource.team_id == "team1"
        assert resource.uri == "mattermost://new_channel_posts"
    
    def test_supports_streaming(self):
        """Test that resource supports streaming."""
        resource = NewChannelPostResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        
        assert resource.supports_streaming() is True
    
    def test_supports_polling(self):
        """Test that resource supports polling."""
        resource = NewChannelPostResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        
        assert resource.supports_polling() is True
    
    def test_get_definition(self):
        """Test getting resource definition."""
        resource = NewChannelPostResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        
        definition = resource.get_definition()
        
        assert definition.uri == "mattermost://new_channel_posts"
        assert definition.name == "new_channel_posts"
        assert definition.supports_streaming is True
        assert definition.supports_polling is True
        assert definition.mime_type == "application/json"


class TestReactionResource:
    """Test ReactionResource class."""
    
    def test_init(self):
        """Test resource initialization."""
        resource = ReactionResource(
            mattermost_url="https://test.com",
            token="test-token",
            channel_ids=["ch1", "ch2"],
            team_id="team1"
        )
        
        assert resource.name == "reactions"
        assert resource.mattermost_url == "https://test.com"
        assert resource.token == "test-token"
        assert resource.channel_ids == {"ch1", "ch2"}
        assert resource.team_id == "team1"
        assert resource.uri == "mattermost://reactions"
    
    def test_supports_streaming(self):
        """Test that resource supports streaming."""
        resource = ReactionResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        
        assert resource.supports_streaming() is True
    
    def test_supports_polling(self):
        """Test that resource supports polling."""
        resource = ReactionResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        
        assert resource.supports_polling() is True


class TestMCPResourceRegistry:
    """Test MCPResourceRegistry class."""
    
    def test_init(self):
        """Test registry initialization."""
        registry = MCPResourceRegistry()
        assert len(registry._resources) == 0
    
    def test_register_resource(self):
        """Test registering a resource."""
        registry = MCPResourceRegistry()
        resource = NewChannelPostResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        
        registry.register(resource)
        
        assert len(registry._resources) == 1
        assert registry.get(resource.uri) == resource
    
    def test_unregister_resource(self):
        """Test unregistering a resource."""
        registry = MCPResourceRegistry()
        resource = NewChannelPostResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        
        registry.register(resource)
        assert len(registry._resources) == 1
        
        registry.unregister(resource.uri)
        assert len(registry._resources) == 0
        assert registry.get(resource.uri) is None
    
    def test_list_resources(self):
        """Test listing resources."""
        registry = MCPResourceRegistry()
        resource1 = NewChannelPostResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        resource2 = ReactionResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        
        registry.register(resource1)
        registry.register(resource2)
        
        resources = registry.list_resources()
        assert len(resources) == 2
        
        # Check that we get resource definitions
        uris = [r.uri for r in resources]
        assert "mattermost://new_channel_posts" in uris
        assert "mattermost://reactions" in uris
    
    def test_get_streaming_resources(self):
        """Test getting streaming resources."""
        registry = MCPResourceRegistry()
        resource = NewChannelPostResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        
        registry.register(resource)
        
        streaming_resources = registry.get_streaming_resources()
        assert len(streaming_resources) == 1
        assert streaming_resources[0] == resource
    
    def test_get_polling_resources(self):
        """Test getting polling resources."""
        registry = MCPResourceRegistry()
        resource = NewChannelPostResource(
            mattermost_url="https://test.com",
            token="test-token"
        )
        
        registry.register(resource)
        
        polling_resources = registry.get_polling_resources()
        assert len(polling_resources) == 1
        assert polling_resources[0] == resource


class TestMattermostMCPServer:
    """Test MattermostMCPServer with streaming resources."""
    
    def test_init_with_streaming_resources(self):
        """Test server initialization with streaming configuration."""
        server = MattermostMCPServer(
            mattermost_url="https://test.com",
            mattermost_token="test-token",
            team_id="team1",
            enable_streaming=True,
            enable_polling=False,
            channel_ids=["ch1", "ch2"]
        )
        
        assert server.mattermost_url == "https://test.com"
        assert server.mattermost_token == "test-token"
        assert server.team_id == "team1"
        assert server.enable_streaming is True
        assert server.enable_polling is False
        assert server.channel_ids == ["ch1", "ch2"]
        
        # Check that resources were initialized
        resources = server.resource_registry.list_resources()
        assert len(resources) == 2
        
        resource_names = [r.name for r in resources]
        assert "new_channel_posts" in resource_names
        assert "reactions" in resource_names
    
    def test_get_resources(self):
        """Test getting resource definitions."""
        server = MattermostMCPServer(
            mattermost_url="https://test.com",
            mattermost_token="test-token"
        )
        
        resources = server.get_resources()
        assert len(resources) == 2
        
        # Should return serialized resource definitions
        for resource in resources:
            assert "uri" in resource
            assert "name" in resource
            assert "description" in resource
            assert "supports_streaming" in resource
            assert "supports_polling" in resource
    
    def test_resource_update_callback(self):
        """Test resource update callback."""
        server = MattermostMCPServer(
            mattermost_url="https://test.com",
            mattermost_token="test-token"
        )
        
        updates_received = []
        
        def callback(update: ResourceUpdate):
            updates_received.append(update)
        
        server.set_resource_update_callback(callback)
        
        # Simulate a resource update
        update = ResourceUpdate(
            resource_uri="test://resource",
            update_type=ResourceUpdateType.CREATED,
            data={"test": "data"}
        )
        
        server._handle_resource_update(update)
        
        assert len(updates_received) == 1
        assert updates_received[0] == update
    
    @pytest.mark.asyncio
    async def test_read_resource(self):
        """Test reading a resource."""
        server = MattermostMCPServer(
            mattermost_url="https://test.com",
            mattermost_token="test-token"
        )
        
        # Mock the resource's read method
        resource = server.resource_registry.get("mattermost://new_channel_posts")
        resource.read = AsyncMock(return_value={"test": "data"})
        
        result = await server.read_resource("mattermost://new_channel_posts")
        assert result == {"test": "data"}
        
        resource.read.assert_called_once_with("mattermost://new_channel_posts")
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_resource(self):
        """Test reading a nonexistent resource."""
        server = MattermostMCPServer(
            mattermost_url="https://test.com",
            mattermost_token="test-token"
        )
        
        with pytest.raises(ValueError, match="Resource not found"):
            await server.read_resource("nonexistent://resource")


@pytest.mark.asyncio
async def test_server_lifecycle():
    """Test server start/stop lifecycle."""
    server = MattermostMCPServer(
        mattermost_url="https://test.com",
        mattermost_token="test-token",
        enable_streaming=False,  # Disable to avoid WebSocket connection
        enable_polling=True,
        polling_interval=60.0
    )
    
    # Mock the registry methods to avoid actual network calls
    server.resource_registry.start_all_streaming = AsyncMock()
    server.resource_registry.start_all_polling = AsyncMock()
    server.resource_registry.cleanup = AsyncMock()
    
    # Test start
    await server.start()
    server.resource_registry.start_all_polling.assert_called_once_with(interval_seconds=60.0)
    server.resource_registry.start_all_streaming.assert_not_called()
    
    # Test stop
    await server.stop()
    server.resource_registry.cleanup.assert_called_once()
