"""
Tests for the MattermostMCPServer class.
"""

import pytest

from mcp_mattermost.server import MattermostMCPServer


class TestMattermostMCPServer:
    """Test cases for MattermostMCPServer."""

    def test_init(self):
        """Test server initialization."""
        server = MattermostMCPServer(
            mattermost_url="https://example.com",
            mattermost_token="test-token",
            team_id="test-team-id",
        )

        assert server.mattermost_url == "https://example.com"
        assert server.mattermost_token == "test-token"
        assert server.team_id == "test-team-id"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from URL."""
        server = MattermostMCPServer(
            mattermost_url="https://example.com/",
            mattermost_token="test-token",
        )

        assert server.mattermost_url == "https://example.com"

    def test_get_tools_empty(self):
        """Test that get_tools returns empty list initially."""
        server = MattermostMCPServer(
            mattermost_url="https://example.com",
            mattermost_token="test-token",
        )

        tools = server.get_tools()
        assert tools == []

    def test_get_resources_empty(self):
        """Test that get_resources returns empty list initially."""
        server = MattermostMCPServer(
            mattermost_url="https://example.com",
            mattermost_token="test-token",
        )

        resources = server.get_resources()
        assert resources == []

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test server start and stop methods."""
        server = MattermostMCPServer(
            mattermost_url="https://example.com",
            mattermost_token="test-token",
        )

        # These should not raise exceptions
        await server.start()
        await server.stop()
