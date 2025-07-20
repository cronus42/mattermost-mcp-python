#!/usr/bin/env python3
"""
Example script demonstrating MCP streaming/polling resources for Mattermost.

This script shows how to use the streaming resource providers to receive
real-time updates for new channel posts and reactions.
"""

import asyncio
import json
import os
from typing import Any, Dict

import structlog
from mcp_mattermost.server import MattermostMCPServer
from mcp_mattermost.resources import ResourceUpdate

# Configure logging
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def handle_resource_update(update: ResourceUpdate) -> None:
    """Handle resource updates from streaming/polling."""
    
    print(f"\n🔔 Resource Update Received:")
    print(f"   URI: {update.resource_uri}")
    print(f"   Type: {update.update_type}")
    print(f"   Event ID: {update.event_id}")
    print(f"   Timestamp: {update.timestamp}")
    
    # Handle different update types
    if update.update_type == "created" and "post" in update.data:
        # New post
        post = update.data["post"]
        print(f"   📝 New Post:")
        print(f"      Channel: {update.data.get('channel_id')}")
        print(f"      User: {update.data.get('user_id')}")
        print(f"      Message: {post.get('message', '')[:100]}...")
        
    elif update.update_type in ["reaction_added", "reaction_removed"]:
        # Reaction event
        action = "➕ Added" if update.update_type == "reaction_added" else "➖ Removed"
        print(f"   {action} Reaction:")
        print(f"      Post: {update.data.get('post_id')}")
        print(f"      User: {update.data.get('user_id')}")
        print(f"      Emoji: {update.data.get('emoji_name')}")
        print(f"      Channel: {update.data.get('channel_id')}")
    
    print()


async def main():
    """Main example function."""
    
    # Get configuration from environment variables
    mattermost_url = os.getenv("MATTERMOST_URL", "https://your-mattermost-instance.com")
    mattermost_token = os.getenv("MATTERMOST_TOKEN")
    team_id = os.getenv("MATTERMOST_TEAM_ID")
    
    if not mattermost_token:
        print("❌ Please set MATTERMOST_TOKEN environment variable")
        print("   You can get this from your Mattermost user settings > Personal Access Tokens")
        return
    
    # Optional: Monitor specific channels only
    channel_ids = None
    if os.getenv("MATTERMOST_CHANNEL_IDS"):
        channel_ids = os.getenv("MATTERMOST_CHANNEL_IDS").split(",")
    
    print(f"🚀 Starting Mattermost MCP Streaming Example")
    print(f"   Server: {mattermost_url}")
    print(f"   Team ID: {team_id or 'All teams'}")
    print(f"   Channels: {len(channel_ids) if channel_ids else 'All channels'}")
    print()
    
    # Create MCP server with streaming enabled
    server = MattermostMCPServer(
        mattermost_url=mattermost_url,
        mattermost_token=mattermost_token,
        team_id=team_id,
        enable_streaming=True,  # Enable WebSocket streaming
        enable_polling=True,    # Enable REST polling as fallback
        polling_interval=30.0,  # Poll every 30 seconds
        channel_ids=channel_ids,
    )
    
    # Set up resource update callback
    server.set_resource_update_callback(handle_resource_update)
    
    try:
        # Start the server (this will start streaming/polling)
        await server.start()
        
        # List available resources
        resources = server.get_resources()
        print("📋 Available MCP Resources:")
        for resource in resources:
            streaming = "✅" if resource.get("supports_streaming") else "❌"
            polling = "✅" if resource.get("supports_polling") else "❌"
            print(f"   • {resource['name']}")
            print(f"     URI: {resource['uri']}")
            print(f"     Description: {resource['description']}")
            print(f"     Streaming: {streaming}  Polling: {polling}")
            print()
        
        print("🎧 Listening for real-time events...")
        print("   Press Ctrl+C to stop")
        print()
        
        # Read current state of resources
        for resource in resources:
            try:
                print(f"📖 Reading current state of {resource['name']}:")
                data = await server.read_resource(resource['uri'])
                
                if resource['name'] == 'new_channel_posts':
                    posts = data.get('posts', [])
                    print(f"   Found {len(posts)} recent posts")
                elif resource['name'] == 'reactions':
                    reactions = data.get('reactions', [])
                    print(f"   Found {len(reactions)} recent reactions")
                
            except Exception as e:
                print(f"   ❌ Error reading resource: {e}")
            print()
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            
    except Exception as e:
        logger.error("Error in main", error=str(e), exc_info=True)
        print(f"❌ Error: {e}")
        
    finally:
        # Clean shutdown
        await server.stop()
        print("✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
