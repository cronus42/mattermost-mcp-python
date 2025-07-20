"""
Integration tests for MCP server subprocess communication.

This module contains tests that spawn the MCP server as a subprocess
and test the MCP protocol communication over stdio.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, Optional

import httpx
import pytest
import respx


class MCPServerTester:
    """Helper class to test MCP server subprocess communication."""

    def __init__(self, env_vars: Optional[Dict[str, str]] = None):
        self.proc: Optional[subprocess.Popen] = None
        self.env_vars = env_vars or {}
        self.message_id = 1

    async def start_server(self) -> None:
        """Start the MCP server subprocess."""
        command = [sys.executable, "-m", "mcp_mattermost"]

        # Merge test environment with provided env vars
        env = os.environ.copy()
        # Remove all Mattermost-related environment variables to avoid authentication
        for key in list(env.keys()):
            if key.startswith(("MATTERMOST_", "WEBHOOK_", "WS_", "DEFAULT_CHANNEL")):
                del env[key]

        env.update(
            {
                # Don't provide credentials during startup to avoid authentication failures
                # Credentials will be provided via the authenticate tool instead
                "LOG_LEVEL": "ERROR",  # Reduce log noise but keep errors visible
                "LOG_FORMAT": "json",  # Use JSON format to minimize interference
                "ENABLE_STREAMING": "false",  # Disable streaming for simpler tests
                "ENABLE_POLLING": "false",  # Disable polling for simpler tests
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),  # Preserve PYTHONPATH
            }
        )
        env.update(self.env_vars)

        self.proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=0,  # Unbuffered for real-time communication
        )

        # Give the server a moment to start
        await asyncio.sleep(0.5)

    async def send_message(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC message to the server."""
        if not self.proc:
            raise RuntimeError("Server not started")

        message = {
            "jsonrpc": "2.0",
            "id": self.message_id,
            "method": method,
            "params": params,
        }
        self.message_id += 1

        message_json = json.dumps(message) + "\n"
        self.proc.stdin.write(message_json)
        self.proc.stdin.flush()

        # Read response with timeout, skipping log lines
        try:
            max_attempts = 50  # Increase to handle many log lines before JSON response
            attempt = 0

            while attempt < max_attempts:
                response_line = await asyncio.wait_for(
                    asyncio.to_thread(self.proc.stdout.readline), timeout=10.0
                )

                if not response_line:
                    raise RuntimeError("No response from server")

                response_line = response_line.strip()
                if not response_line:
                    attempt += 1
                    continue

                # Check if this line contains a JSON-RPC message
                # JSON-RPC messages should start with '{"jsonrpc"'
                if response_line.startswith('{"jsonrpc"'):
                    try:
                        return json.loads(response_line)
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: JSON decode error: {e}", flush=True)
                        # This might be malformed JSON, try the next line
                        attempt += 1
                        continue
                else:
                    # This is a log line, skip it
                    attempt += 1
                    continue

            raise RuntimeError(
                "Failed to get valid JSON-RPC response after multiple attempts"
            )

        except asyncio.TimeoutError:
            raise RuntimeError("Server response timeout")

    async def cleanup(self) -> None:
        """Clean up the server subprocess."""
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
            self.proc = None


@pytest.mark.asyncio
async def test_mcp_server_initialize():
    """Test MCP server initialization."""
    tester = MCPServerTester()

    try:
        await tester.start_server()

        # Send initialize request
        response = await tester.send_message(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {},
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0",
                },
            },
        )

        # Verify initialize response
        assert "result" in response
        result = response["result"]
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result

        # Server info should contain name and version
        server_info = result["serverInfo"]
        assert "name" in server_info
        assert server_info["name"] == "mcp-mattermost"

    finally:
        await tester.cleanup()


@pytest.mark.asyncio
async def test_mcp_server_list_tools():
    """Test listing tools from MCP server."""
    tester = MCPServerTester()

    try:
        await tester.start_server()

        # Initialize first
        await tester.send_message(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # List tools
        response = await tester.send_message("tools/list", {})

        # Verify tools response
        assert "result" in response
        result = response["result"]
        assert "tools" in result

        tools = result["tools"]
        assert isinstance(tools, list)

        # Should have some tools available
        assert len(tools) > 0

        # Each tool should have required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

            # Tool names should be strings
            assert isinstance(tool["name"], str)
            assert isinstance(tool["description"], str)

            # Input schema should be a dict with type object
            assert isinstance(tool["inputSchema"], dict)
            assert tool["inputSchema"].get("type") == "object"

        # Should include authentication tools
        tool_names = [tool["name"] for tool in tools]
        assert "authenticate" in tool_names
        assert "get_auth_status" in tool_names

    finally:
        await tester.cleanup()


@pytest.mark.asyncio
async def test_mcp_server_list_resources():
    """Test listing resources from MCP server."""
    tester = MCPServerTester()

    try:
        await tester.start_server()

        # Initialize first
        await tester.send_message(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # List resources
        response = await tester.send_message("resources/list", {})

        # Verify resources response
        assert "result" in response
        result = response["result"]
        assert "resources" in result

        resources = result["resources"]
        assert isinstance(resources, list)

        # Should have some resources available
        assert len(resources) > 0

        # Each resource should have required fields
        for resource in resources:
            assert "uri" in resource
            assert "name" in resource
            assert (
                "mimeType" in resource
            ), f"Resource {resource['name']} missing mimeType"

            # URI should be a string
            assert isinstance(resource["uri"], str)
            assert isinstance(resource["name"], str)
            assert isinstance(resource["mimeType"], str)

        # Should include expected resources
        resource_names = [resource["name"] for resource in resources]
        assert "new_channel_posts" in resource_names
        assert "reactions" in resource_names

    finally:
        await tester.cleanup()


@pytest.mark.asyncio
@respx.mock
async def test_mcp_tool_invocation_with_mocked_mattermost():
    """Test tool invocation with mocked Mattermost API calls."""
    # Mock Mattermost API endpoints
    base_url = "https://mock-mattermost.example.com/api/v4"

    # Mock authentication endpoint
    respx.get(f"{base_url}/users/me").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "test-user-id",
                "username": "test-user",
                "email": "test@example.com",
            },
        )
    )

    # Mock team channels endpoint
    respx.get(f"{base_url}/teams/mock-team-id/channels").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "mock-channel-id",
                    "name": "test-channel",
                    "display_name": "Test Channel",
                    "type": "O",
                }
            ],
        )
    )

    # Mock create post endpoint
    respx.post(f"{base_url}/posts").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "created-post-id",
                "channel_id": "mock-channel-id",
                "message": "Test message",
                "user_id": "test-user-id",
                "create_at": 1234567890000,
                "update_at": 1234567890000,
            },
        )
    )

    tester = MCPServerTester()

    try:
        await tester.start_server()

        # Initialize
        await tester.send_message(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # First authenticate
        auth_response = await tester.send_message(
            "tools/call",
            {
                "name": "authenticate",
                "arguments": {
                    "mattermost_url": "https://mock-mattermost.example.com",
                    "token": "mock-token-12345",
                    "team_id": "mock-team-id",
                },
            },
        )

        # Verify authentication succeeded
        assert "result" in auth_response
        result = auth_response["result"]
        assert "content" in result
        assert len(result["content"]) > 0

        # Parse the authentication result
        content_text = result["content"][0]["text"]
        auth_result = json.loads(content_text)
        assert auth_result.get("success") is True

        # Test send_message tool (this will use the mocked endpoints)
        send_response = await tester.send_message(
            "tools/call",
            {
                "name": "send_message",
                "arguments": {
                    "channel_id": "mock-channel-id",
                    "message": "Test message",
                },
            },
        )

        # Verify message was sent (though mocked)
        assert "result" in send_response
        result = send_response["result"]
        assert "content" in result

        # Parse the message sending result
        content_text = result["content"][0]["text"]
        send_result = json.loads(content_text)
        assert "success" in send_result

    finally:
        await tester.cleanup()


@pytest.mark.asyncio
async def test_mcp_server_with_config_file():
    """Test MCP server with a configuration file."""
    config_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "test_config.json"
    )

    # Verify config file exists
    assert os.path.exists(config_path), f"Config file not found: {config_path}"

    with open(config_path) as f:
        config = json.load(f)

    # Verify config structure
    assert "mcpServers" in config
    assert "mattermost-test" in config["mcpServers"]

    server_config = config["mcpServers"]["mattermost-test"]
    assert "command" in server_config
    assert "args" in server_config
    assert "env" in server_config

    # Test that the config contains expected tools and resources
    assert "tools" in config
    assert "resources" in config

    tool_names = [tool["name"] for tool in config["tools"]]
    assert "authenticate" in tool_names
    assert "send_message" in tool_names
    assert "get_channel_history" in tool_names

    resource_uris = [resource["uri"] for resource in config["resources"]]
    assert "mattermost://new_channel_posts" in resource_uris
    assert "mattermost://reactions" in resource_uris


@pytest.mark.asyncio
@respx.mock
async def test_mcp_server_error_handling():
    """Test MCP server error handling with mocked failure responses."""
    base_url = "https://mock-mattermost.example.com/api/v4"

    # Mock authentication failure
    respx.get(f"{base_url}/users/me").mock(
        return_value=httpx.Response(
            401,
            json={"message": "Invalid or expired session", "status_code": 401},
        )
    )

    tester = MCPServerTester()

    try:
        await tester.start_server()

        # Initialize
        await tester.send_message(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # Try to authenticate with invalid credentials (should fail)
        auth_response = await tester.send_message(
            "tools/call",
            {
                "name": "authenticate",
                "arguments": {
                    "mattermost_url": "https://mock-mattermost.example.com",
                    "token": "invalid-token",
                    "team_id": "mock-team-id",
                },
            },
        )

        # Verify authentication failed gracefully
        assert "result" in auth_response
        result = auth_response["result"]
        assert "content" in result
        assert len(result["content"]) > 0

        # Parse the authentication result
        content_text = result["content"][0]["text"]
        auth_result = json.loads(content_text)
        assert auth_result.get("success") is False
        assert "error" in auth_result

    finally:
        await tester.cleanup()
