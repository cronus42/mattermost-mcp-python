#!/usr/bin/env python3
"""
Example script demonstrating CLI usage and configuration options for Mattermost MCP Server.

This script shows different ways to run the server with various configuration options.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and show the description."""
    print(f"\n{'='*60}")
    print(f"Example: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    # Don't actually run the commands, just show them
    print("(This is a demonstration - commands are not executed)")

def main():
    """Demonstrate various CLI usage patterns."""
    
    print("Mattermost MCP Server - CLI Usage Examples")
    print("==========================================")
    
    # Base command
    base_cmd = [sys.executable, "-m", "mcp_mattermost"]
    
    # Example 1: Basic usage with environment variables
    run_command(
        base_cmd,
        "Basic usage - relies on environment variables (MATTERMOST_URL, MATTERMOST_TOKEN)"
    )
    
    # Example 2: Override specific settings
    run_command(
        base_cmd + [
            "--mattermost-url", "https://mattermost.example.com",
            "--team-id", "team123",
            "--default-channel", "general"
        ],
        "Override Mattermost connection settings"
    )
    
    # Example 3: Configure webhook settings
    run_command(
        base_cmd + [
            "--webhook-secret", "my-secret-key",
            "--ws-url", "wss://custom-websocket.example.com/api/v4/websocket"
        ],
        "Configure webhook secret and custom WebSocket URL"
    )
    
    # Example 4: Server configuration
    run_command(
        base_cmd + [
            "--host", "0.0.0.0",
            "--port", "3000",
            "--log-level", "DEBUG",
            "--log-format", "json"
        ],
        "Configure server host, port, and logging"
    )
    
    # Example 5: Disable streaming, enable only polling
    run_command(
        base_cmd + [
            "--no-streaming",
            "--polling-interval", "60.0"
        ],
        "Disable WebSocket streaming, use only REST polling every 60 seconds"
    )
    
    # Example 6: Disable polling, use only streaming
    run_command(
        base_cmd + [
            "--no-polling"
        ],
        "Use only WebSocket streaming, disable REST polling"
    )
    
    # Example 7: Full configuration override
    run_command(
        base_cmd + [
            "--mattermost-url", "https://chat.company.com",
            "--mattermost-token", "xoxb-token-here",
            "--team-id", "engineering-team",
            "--webhook-secret", "webhook-validation-secret",
            "--ws-url", "wss://chat.company.com/api/v4/websocket",
            "--default-channel", "alerts",
            "--host", "127.0.0.1",
            "--port", "8080",
            "--log-level", "INFO",
            "--log-format", "console",
            "--polling-interval", "45.0"
        ],
        "Complete configuration override with all available options"
    )
    
    print(f"\n{'='*60}")
    print("Environment Variable Reference:")
    print("==============================")
    
    env_vars = [
        ("MATTERMOST_URL", "Mattermost server URL"),
        ("MATTERMOST_TOKEN", "API authentication token"),
        ("MATTERMOST_TEAM_ID", "Team ID (optional)"),
        ("WEBHOOK_SECRET", "Webhook validation secret"),
        ("WS_URL", "Custom WebSocket URL"),
        ("DEFAULT_CHANNEL", "Default channel ID"),
        ("MCP_SERVER_HOST", "Server host (default: localhost)"),
        ("MCP_SERVER_PORT", "Server port (default: 8000)"),
        ("LOG_LEVEL", "Logging level (default: INFO)"),
        ("LOG_FORMAT", "Logging format: console|json (default: console)"),
    ]
    
    for var, description in env_vars:
        print(f"  {var:<20} - {description}")
    
    print(f"\n{'='*60}")
    print("Usage Notes:")
    print("============")
    print("• Command-line arguments override environment variables")
    print("• MATTERMOST_URL and MATTERMOST_TOKEN are required")
    print("• Use --help to see all available options")
    print("• The server runs until interrupted with Ctrl+C")
    print("• Webhook secret is used for validating incoming webhooks")
    print("• Custom WebSocket URL overrides the default derived from MATTERMOST_URL")
    print("• Default channel is used when no specific channel is specified")

if __name__ == "__main__":
    main()
