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
            team_id="test-team-id",
        )

        assert server.team_id == "test-team-id"

    def test_get_tools_empty(self):
        """Test that get_tools returns empty list initially."""
        server = MattermostMCPServer()

        tools = server.get_tools()
        assert tools == []

    def test_get_resources_default(self):
        """Test that get_resources returns default resources initially."""
        server = MattermostMCPServer()

        resources = server.get_resources()
        assert len(resources) == 2  # new_channel_posts and reactions resources

        resource_names = [r["name"] for r in resources]
        assert "new_channel_posts" in resource_names
        assert "reactions" in resource_names

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test server start and stop methods."""
        server = MattermostMCPServer()

        # These should not raise exceptions
        await server.start()
        await server.stop()
