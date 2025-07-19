"""
Main entry point for the Mattermost MCP server.
"""

import asyncio
import os
import sys
from typing import Optional

import structlog
from dotenv import load_dotenv

from .server import MattermostMCPServer

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if os.getenv("LOG_FORMAT") == "json" 
        else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def get_config() -> tuple[str, str, Optional[str]]:
    """
    Get configuration from environment variables.
    
    Returns:
        Tuple of (mattermost_url, mattermost_token, team_id)
        
    Raises:
        ValueError: If required environment variables are missing
    """
    mattermost_url = os.getenv("MATTERMOST_URL")
    mattermost_token = os.getenv("MATTERMOST_TOKEN")
    team_id = os.getenv("MATTERMOST_TEAM_ID")
    
    if not mattermost_url:
        raise ValueError("MATTERMOST_URL environment variable is required")
    
    if not mattermost_token:
        raise ValueError("MATTERMOST_TOKEN environment variable is required")
    
    return mattermost_url, mattermost_token, team_id


async def main() -> None:
    """Main entry point."""
    try:
        # Get configuration
        mattermost_url, mattermost_token, team_id = get_config()
        
        # Create and start the server
        server = MattermostMCPServer(
            mattermost_url=mattermost_url,
            mattermost_token=mattermost_token,
            team_id=team_id,
        )
        
        logger.info("Starting Mattermost MCP server")
        await server.start()
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await server.stop()
            
    except Exception as e:
        logger.error("Failed to start server", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
