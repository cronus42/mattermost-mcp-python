"""
Tests for service layer classes.

This module tests the service classes that provide high-level API operations
for different Mattermost domains like posts, channels, etc.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_mattermost.api.client import AsyncHTTPClient
from mcp_mattermost.api.exceptions import AuthenticationError, HTTPError, NotFoundError
from mcp_mattermost.models.base import MattermostResponse
from mcp_mattermost.models.channels import (
    Channel,
    ChannelCreate,
    ChannelMember,
    ChannelPatch,
)
from mcp_mattermost.models.posts import Post, PostCreate, PostList, PostPatch, Reaction
from mcp_mattermost.services.base import BaseService
from mcp_mattermost.services.channels import ChannelsService
from mcp_mattermost.services.posts import PostsService

# Note: Using respx for mocking


class TestBaseService:
    """Test the BaseService class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = AsyncMock(spec=AsyncHTTPClient)
        self.service = BaseService(self.mock_client)

    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful API request."""
        # Mock response data
        response_data = {"id": "test123", "name": "Test"}
        self.mock_client.request.return_value = response_data

        # Make request
        result = await self.service._make_request("GET", "/test", MattermostResponse)

        # Verify request was made
        self.mock_client.request.assert_called_once_with(
            method="GET", endpoint="/test", data=None, params=None, headers=None
        )

        # Verify result
        assert isinstance(result, MattermostResponse)
        assert result.model_validate(response_data)

    @pytest.mark.asyncio
    async def test_make_request_with_data(self):
        """Test API request with data payload."""
        request_data = {"name": "New Item"}
        response_data = {"id": "item123", "name": "New Item"}
        self.mock_client.request.return_value = response_data

        result = await self.service._make_request(
            "POST", "/items", MattermostResponse, data=request_data
        )

        self.mock_client.request.assert_called_once_with(
            method="POST",
            endpoint="/items",
            data=request_data,
            params=None,
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_make_request_with_params_and_headers(self):
        """Test API request with query params and headers."""
        params = {"page": 0, "per_page": 50}
        headers = {"X-Custom-Header": "value"}
        response_data = {"data": "test"}
        self.mock_client.request.return_value = response_data

        await self.service._make_request(
            "GET", "/items", MattermostResponse, params=params, headers=headers
        )

        self.mock_client.request.assert_called_once_with(
            method="GET", endpoint="/items", data=None, params=params, headers=headers
        )

    @pytest.mark.asyncio
    async def test_make_request_empty_response(self):
        """Test handling of empty responses."""
        self.mock_client.request.return_value = None

        result = await self.service._make_request(
            "DELETE", "/item/123", MattermostResponse
        )

        assert isinstance(result, MattermostResponse)

    @pytest.mark.asyncio
    async def test_make_request_http_error_passthrough(self):
        """Test that HTTP errors are passed through."""
        self.mock_client.request.side_effect = AuthenticationError("Unauthorized")

        with pytest.raises(AuthenticationError):
            await self.service._make_request("GET", "/test", MattermostResponse)

    @pytest.mark.asyncio
    async def test_make_request_unexpected_error(self):
        """Test handling of unexpected errors."""
        self.mock_client.request.side_effect = ValueError("Unexpected error")

        with pytest.raises(HTTPError) as exc_info:
            await self.service._make_request("GET", "/test", MattermostResponse)

        assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_list_request_success(self):
        """Test successful list request."""
        response_data = [
            {"id": "item1", "name": "Item 1"},
            {"id": "item2", "name": "Item 2"},
        ]
        self.mock_client.request.return_value = response_data

        result = await self.service._make_list_request(
            "GET", "/items", MattermostResponse
        )

        assert len(result) == 2
        assert all(isinstance(item, MattermostResponse) for item in result)

    @pytest.mark.asyncio
    async def test_make_list_request_invalid_response(self):
        """Test list request with non-list response."""
        self.mock_client.request.return_value = {"not": "a list"}

        with pytest.raises(HTTPError) as exc_info:
            await self.service._make_list_request("GET", "/items", MattermostResponse)

        assert "Expected list response" in str(exc_info.value)

    def test_build_query_params(self):
        """Test query parameter building."""
        params = self.service._build_query_params(
            page=0, per_page=50, include_deleted=True, missing_param=None
        )

        expected = {"page": 0, "per_page": 50, "include_deleted": True}
        assert params == expected

    @pytest.mark.asyncio
    async def test_convenience_methods(self):
        """Test convenience HTTP method wrappers."""
        response_data = {"id": "test"}
        self.mock_client.request.return_value = response_data

        # Test GET
        await self.service._get("/test", MattermostResponse)
        self.mock_client.request.assert_called_with(
            method="GET", endpoint="/test", data=None, params=None, headers=None
        )

        # Test POST
        await self.service._post("/test", MattermostResponse, data={"test": "data"})
        self.mock_client.request.assert_called_with(
            method="POST",
            endpoint="/test",
            data={"test": "data"},
            params=None,
            headers=None,
        )

        # Test PUT
        await self.service._put("/test", MattermostResponse, data={"test": "data"})
        self.mock_client.request.assert_called_with(
            method="PUT",
            endpoint="/test",
            data={"test": "data"},
            params=None,
            headers=None,
        )

        # Test PATCH
        await self.service._patch("/test", MattermostResponse, data={"test": "data"})
        self.mock_client.request.assert_called_with(
            method="PATCH",
            endpoint="/test",
            data={"test": "data"},
            params=None,
            headers=None,
        )

        # Test DELETE
        await self.service._delete("/test", MattermostResponse)
        self.mock_client.request.assert_called_with(
            method="DELETE", endpoint="/test", data=None, params=None, headers=None
        )


class TestPostsService:
    """Test the PostsService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = AsyncMock(spec=AsyncHTTPClient)
        self.service = PostsService(self.mock_client)

    @pytest.mark.asyncio
    async def test_create_post(self):
        """Test post creation."""
        post_data = PostCreate(
            channel_id="channel123", message="Hello, World!", root_id=None
        )
        response_data = {
            "id": "post123",
            "create_at": 1234567890,
            "update_at": 1234567890,
            "edit_at": 0,
            "delete_at": 0,
            "is_pinned": False,
            "user_id": "user123",
            "channel_id": "channel123",
            "root_id": "",
            "parent_id": "",
            "original_id": "",
            "message": "Hello, World!",
            "type": "",
            "props": {},
            "hashtags": "",
            "pending_post_id": "",
            "reply_count": 0,
            "last_reply_at": 0,
            "participants": None,
            "metadata": {},
        }

        self.mock_client.request.return_value = response_data

        result = await self.service.create_post(post_data)

        assert isinstance(result, Post)
        assert result.id == "post123"
        assert result.message == "Hello, World!"

        self.mock_client.request.assert_called_once_with(
            method="POST",
            endpoint="posts",
            data=post_data.model_dump(exclude_none=True),
            params=None,
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_get_post(self):
        """Test getting a post by ID."""
        post_id = "post123"
        response_data = {
            "id": post_id,
            "create_at": 1234567890,
            "update_at": 1234567890,
            "edit_at": 0,
            "delete_at": 0,
            "is_pinned": False,
            "user_id": "user123",
            "channel_id": "channel123",
            "root_id": "",
            "parent_id": "",
            "original_id": "",
            "message": "Test message",
            "type": "",
            "props": {},
            "hashtags": "",
            "pending_post_id": "",
            "reply_count": 0,
            "last_reply_at": 0,
            "participants": None,
            "metadata": {},
        }

        self.mock_client.request.return_value = response_data

        result = await self.service.get_post(post_id)

        assert isinstance(result, Post)
        assert result.id == post_id

        self.mock_client.request.assert_called_once_with(
            method="GET",
            endpoint=f"posts/{post_id}",
            data=None,
            params=None,
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_update_post(self):
        """Test updating a post."""
        post_id = "post123"
        post_patch = PostPatch(message="Updated message")

        response_data = {
            "id": post_id,
            "create_at": 1234567890,
            "update_at": 1234567891,
            "edit_at": 1234567891,
            "delete_at": 0,
            "is_pinned": False,
            "user_id": "user123",
            "channel_id": "channel123",
            "root_id": "",
            "parent_id": "",
            "original_id": "",
            "message": "Updated message",
            "type": "",
            "props": {},
            "hashtags": "",
            "pending_post_id": "",
            "reply_count": 0,
            "last_reply_at": 0,
            "participants": None,
            "metadata": {},
        }

        self.mock_client.request.return_value = response_data

        result = await self.service.update_post(post_id, post_patch)

        assert isinstance(result, Post)
        assert result.message == "Updated message"

        self.mock_client.request.assert_called_once_with(
            method="PUT",
            endpoint=f"posts/{post_id}",
            data=post_patch.model_dump(exclude_none=True),
            params=None,
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_delete_post(self):
        """Test deleting a post."""
        post_id = "post123"
        self.mock_client.request.return_value = {"status": "OK"}

        result = await self.service.delete_post(post_id)

        assert isinstance(result, MattermostResponse)

        self.mock_client.request.assert_called_once_with(
            method="DELETE",
            endpoint=f"posts/{post_id}",
            data=None,
            params=None,
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_get_posts_for_channel(self):
        """Test getting posts for a channel."""
        channel_id = "channel123"
        response_data = {
            "order": ["post2", "post1"],
            "posts": {
                "post1": {
                    "id": "post1",
                    "create_at": 1234567890,
                    "update_at": 1234567890,
                    "edit_at": 0,
                    "delete_at": 0,
                    "is_pinned": False,
                    "user_id": "user123",
                    "channel_id": channel_id,
                    "root_id": "",
                    "parent_id": "",
                    "original_id": "",
                    "message": "First post",
                    "type": "",
                    "props": {},
                    "hashtags": "",
                    "pending_post_id": "",
                    "reply_count": 0,
                    "last_reply_at": 0,
                    "participants": None,
                    "metadata": {},
                },
                "post2": {
                    "id": "post2",
                    "create_at": 1234567891,
                    "update_at": 1234567891,
                    "edit_at": 0,
                    "delete_at": 0,
                    "is_pinned": False,
                    "user_id": "user123",
                    "channel_id": channel_id,
                    "root_id": "",
                    "parent_id": "",
                    "original_id": "",
                    "message": "Second post",
                    "type": "",
                    "props": {},
                    "hashtags": "",
                    "pending_post_id": "",
                    "reply_count": 0,
                    "last_reply_at": 0,
                    "participants": None,
                    "metadata": {},
                },
            },
            "next_post_id": "",
            "prev_post_id": "",
            "has_next": False,
        }

        self.mock_client.request.return_value = response_data

        result = await self.service.get_posts_for_channel(
            channel_id, page=0, per_page=50
        )

        assert isinstance(result, PostList)
        assert len(result.order) == 2
        assert "post1" in result.posts
        assert "post2" in result.posts

        self.mock_client.request.assert_called_once_with(
            method="GET",
            endpoint=f"channels/{channel_id}/posts",
            data=None,
            params={"page": 0, "per_page": 50},
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_add_reaction(self):
        """Test adding a reaction to a post."""
        user_id = "user123"
        post_id = "post123"
        emoji_name = "thumbsup"

        response_data = {
            "user_id": user_id,
            "post_id": post_id,
            "emoji_name": emoji_name,
            "create_at": 1234567890,
        }

        self.mock_client.request.return_value = response_data

        result = await self.service.add_reaction(user_id, post_id, emoji_name)

        assert isinstance(result, Reaction)
        assert result.user_id == user_id
        assert result.post_id == post_id
        assert result.emoji_name == emoji_name

        self.mock_client.request.assert_called_once_with(
            method="POST",
            endpoint="reactions",
            data={"user_id": user_id, "post_id": post_id, "emoji_name": emoji_name},
            params=None,
            headers=None,
        )


class TestChannelsService:
    """Test the ChannelsService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = AsyncMock(spec=AsyncHTTPClient)
        self.service = ChannelsService(self.mock_client)

    @pytest.mark.asyncio
    async def test_create_channel(self):
        """Test channel creation."""
        channel_data = ChannelCreate(
            team_id="team123",
            name="test-channel",
            display_name="Test Channel",
            type="O",  # Open channel
            purpose="Test purpose",
            header="Test header",
        )

        response_data = {
            "id": "channel123",
            "create_at": 1234567890,
            "update_at": 1234567890,
            "delete_at": 0,
            "team_id": "team123",
            "type": "O",
            "display_name": "Test Channel",
            "name": "test-channel",
            "header": "Test header",
            "purpose": "Test purpose",
            "last_post_at": 0,
            "total_msg_count": 0,
            "extra_update_at": 0,
            "creator_id": "user123",
            "scheme_id": "",
            "props": None,
            "group_constrained": None,
            "shared": None,
            "total_msg_count_root": 0,
            "policy_id": None,
            "last_root_post_at": 0,
        }

        self.mock_client.request.return_value = response_data

        result = await self.service.create_channel(channel_data)

        assert isinstance(result, Channel)
        assert result.id == "channel123"
        assert result.name == "test-channel"
        assert result.display_name == "Test Channel"

        self.mock_client.request.assert_called_once_with(
            method="POST",
            endpoint="channels",
            data=channel_data.model_dump(exclude_none=True),
            params=None,
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_get_channel(self):
        """Test getting a channel by ID."""
        channel_id = "channel123"
        response_data = {
            "id": channel_id,
            "create_at": 1234567890,
            "update_at": 1234567890,
            "delete_at": 0,
            "team_id": "team123",
            "type": "O",
            "display_name": "Test Channel",
            "name": "test-channel",
            "header": "Test header",
            "purpose": "Test purpose",
            "last_post_at": 0,
            "total_msg_count": 0,
            "extra_update_at": 0,
            "creator_id": "user123",
            "scheme_id": "",
            "props": None,
            "group_constrained": None,
            "shared": None,
            "total_msg_count_root": 0,
            "policy_id": None,
            "last_root_post_at": 0,
        }

        self.mock_client.request.return_value = response_data

        result = await self.service.get_channel(channel_id)

        assert isinstance(result, Channel)
        assert result.id == channel_id

        self.mock_client.request.assert_called_once_with(
            method="GET",
            endpoint=f"channels/{channel_id}",
            data=None,
            params=None,
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_get_channel_by_name(self):
        """Test getting a channel by name."""
        team_id = "team123"
        channel_name = "test-channel"
        response_data = {
            "id": "channel123",
            "create_at": 1234567890,
            "update_at": 1234567890,
            "delete_at": 0,
            "team_id": team_id,
            "type": "O",
            "display_name": "Test Channel",
            "name": channel_name,
            "header": "Test header",
            "purpose": "Test purpose",
            "last_post_at": 0,
            "total_msg_count": 0,
            "extra_update_at": 0,
            "creator_id": "user123",
            "scheme_id": "",
            "props": None,
            "group_constrained": None,
            "shared": None,
            "total_msg_count_root": 0,
            "policy_id": None,
            "last_root_post_at": 0,
        }

        self.mock_client.request.return_value = response_data

        result = await self.service.get_channel_by_name(team_id, channel_name)

        assert isinstance(result, Channel)
        assert result.name == channel_name

        self.mock_client.request.assert_called_once_with(
            method="GET",
            endpoint=f"teams/{team_id}/channels/name/{channel_name}",
            data=None,
            params=None,
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_add_channel_member(self):
        """Test adding a member to a channel."""
        channel_id = "channel123"
        user_id = "user123"

        response_data = {
            "channel_id": channel_id,
            "user_id": user_id,
            "roles": "channel_user",
            "last_viewed_at": 0,
            "msg_count": 0,
            "mention_count": 0,
            "notify_props": {
                "desktop": "default",
                "email": "default",
                "mark_unread": "all",
                "push": "default",
                "ignore_channel_mentions": "default",
            },
            "last_update_at": 1234567890,
            "scheme_user": True,
            "scheme_admin": False,
            "explicit_roles": "",
            "mention_count_root": 0,
            "msg_count_root": 0,
        }

        self.mock_client.request.return_value = response_data

        result = await self.service.add_channel_member(channel_id, user_id)

        assert isinstance(result, ChannelMember)
        assert result.channel_id == channel_id
        assert result.user_id == user_id

        self.mock_client.request.assert_called_once_with(
            method="POST",
            endpoint=f"channels/{channel_id}/members",
            data={"user_id": user_id},
            params=None,
            headers=None,
        )

    @pytest.mark.asyncio
    async def test_get_channels_for_team(self):
        """Test getting channels for a team."""
        team_id = "team123"
        response_data = [
            {
                "id": "channel1",
                "create_at": 1234567890,
                "update_at": 1234567890,
                "delete_at": 0,
                "team_id": team_id,
                "type": "O",
                "display_name": "Channel 1",
                "name": "channel-1",
                "header": "",
                "purpose": "",
                "last_post_at": 0,
                "total_msg_count": 0,
                "extra_update_at": 0,
                "creator_id": "user123",
                "scheme_id": "",
                "props": None,
                "group_constrained": None,
                "shared": None,
                "total_msg_count_root": 0,
                "policy_id": None,
                "last_root_post_at": 0,
            },
            {
                "id": "channel2",
                "create_at": 1234567891,
                "update_at": 1234567891,
                "delete_at": 0,
                "team_id": team_id,
                "type": "P",
                "display_name": "Channel 2",
                "name": "channel-2",
                "header": "",
                "purpose": "",
                "last_post_at": 0,
                "total_msg_count": 0,
                "extra_update_at": 0,
                "creator_id": "user123",
                "scheme_id": "",
                "props": None,
                "group_constrained": None,
                "shared": None,
                "total_msg_count_root": 0,
                "policy_id": None,
                "last_root_post_at": 0,
            },
        ]

        self.mock_client.request.return_value = response_data

        result = await self.service.get_channels_for_team(team_id, page=0, per_page=50)

        assert len(result) == 2
        assert all(isinstance(channel, Channel) for channel in result)
        assert result[0].id == "channel1"
        assert result[1].id == "channel2"

        self.mock_client.request.assert_called_once_with(
            method="GET",
            endpoint=f"teams/{team_id}/channels",
            data=None,
            params={"page": 0, "per_page": 50, "include_deleted": False},
            headers=None,
        )


# Note: Integration tests with httpx mocking have been removed
# in favor of unit tests with mocked AsyncHTTPClient


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
