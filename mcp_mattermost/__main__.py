"""
Main entry point for the Mattermost MCP server.
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

import structlog
from dotenv import load_dotenv

from .server import MattermostMCPServer

# Load environment variables
load_dotenv()


def configure_logging(log_format: str = "console", log_level: str = "INFO") -> None:
    """
    Configure structured logging with the specified format and level.

    Args:
        log_format: Logging format ("console" or "json")
        log_level: Logging level
    """
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add appropriate renderer based on format
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logger level
    import logging

    logging.basicConfig(level=getattr(logging, log_level.upper()))


logger = structlog.get_logger(__name__)


class ServerConfig:
    """
    Configuration class for the Mattermost MCP server.
    """

    def __init__(
        self,
        mattermost_url: str,
        mattermost_token: str,
        team_id: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        ws_url: Optional[str] = None,
        default_channel: Optional[str] = None,
        host: str = "localhost",
        port: int = 8000,
        log_level: str = "INFO",
        log_format: str = "console",
        enable_streaming: bool = True,
        enable_polling: bool = True,
        polling_interval: float = 30.0,
    ):
        self.mattermost_url = mattermost_url
        self.mattermost_token = mattermost_token
        self.team_id = team_id
        self.webhook_secret = webhook_secret
        self.ws_url = ws_url
        self.default_channel = default_channel
        self.host = host
        self.port = port
        self.log_level = log_level
        self.log_format = log_format
        self.enable_streaming = enable_streaming
        self.enable_polling = enable_polling
        self.polling_interval = polling_interval


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Mattermost MCP Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Mattermost configuration
    parser.add_argument(
        "--mattermost-url",
        help="Mattermost server URL (overrides MATTERMOST_URL env var)",
    )
    parser.add_argument(
        "--mattermost-token",
        help="Mattermost API token (overrides MATTERMOST_TOKEN env var)",
    )
    parser.add_argument(
        "--team-id",
        help="Mattermost team ID (overrides MATTERMOST_TEAM_ID env var)",
    )
    parser.add_argument(
        "--webhook-secret",
        help="Webhook secret for validation (overrides WEBHOOK_SECRET env var)",
    )
    parser.add_argument(
        "--ws-url",
        help="WebSocket URL (overrides WS_URL env var)",
    )
    parser.add_argument(
        "--default-channel",
        help="Default channel ID (overrides DEFAULT_CHANNEL env var)",
    )

    # Server configuration
    parser.add_argument(
        "--host",
        default="localhost",
        help="Server host (overrides MCP_SERVER_HOST env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (overrides MCP_SERVER_PORT env var)",
    )

    # Logging configuration
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (overrides LOG_LEVEL env var)",
    )
    parser.add_argument(
        "--log-format",
        choices=["console", "json"],
        help="Logging format (overrides LOG_FORMAT env var)",
    )

    # Feature configuration
    parser.add_argument(
        "--no-streaming",
        action="store_true",
        help="Disable WebSocket streaming",
    )
    parser.add_argument(
        "--no-polling",
        action="store_true",
        help="Disable REST API polling",
    )
    parser.add_argument(
        "--polling-interval",
        type=float,
        default=30.0,
        help="Polling interval in seconds",
    )

    return parser.parse_args()


def get_config_from_env_and_args(args: argparse.Namespace) -> ServerConfig:
    """
    Get configuration from environment variables and command-line arguments.
    Command-line arguments take precedence over environment variables.

    Args:
        args: Parsed command-line arguments

    Returns:
        ServerConfig instance with resolved configuration

    Raises:
        ValueError: If required configuration is missing
    """
    # Get values with CLI args taking precedence over env vars
    mattermost_url = args.mattermost_url or os.getenv("MATTERMOST_URL")
    mattermost_token = args.mattermost_token or os.getenv("MATTERMOST_TOKEN")
    team_id = args.team_id or os.getenv("MATTERMOST_TEAM_ID")
    webhook_secret = args.webhook_secret or os.getenv("WEBHOOK_SECRET")
    ws_url = args.ws_url or os.getenv("WS_URL")
    default_channel = args.default_channel or os.getenv("DEFAULT_CHANNEL")

    host = args.host or os.getenv("MCP_SERVER_HOST", "localhost")
    port = args.port or int(os.getenv("MCP_SERVER_PORT", "8000"))

    log_level = args.log_level or os.getenv("LOG_LEVEL", "INFO")
    log_format = args.log_format or os.getenv("LOG_FORMAT", "console")

    enable_streaming = not args.no_streaming
    enable_polling = not args.no_polling
    polling_interval = args.polling_interval

    # Validate required configuration
    if not mattermost_url:
        raise ValueError(
            "MATTERMOST_URL is required (set via env var or --mattermost-url)"
        )

    if not mattermost_token:
        raise ValueError(
            "MATTERMOST_TOKEN is required (set via env var or --mattermost-token)"
        )

    return ServerConfig(
        mattermost_url=mattermost_url,
        mattermost_token=mattermost_token,
        team_id=team_id,
        webhook_secret=webhook_secret,
        ws_url=ws_url,
        default_channel=default_channel,
        host=host,
        port=port,
        log_level=log_level,
        log_format=log_format,
        enable_streaming=enable_streaming,
        enable_polling=enable_polling,
        polling_interval=polling_interval,
    )


async def main() -> None:
    """Main entry point."""
    try:
        # Parse command-line arguments
        args = parse_args()

        # Get configuration from environment and CLI args
        config = get_config_from_env_and_args(args)

        # Configure logging
        configure_logging(config.log_format, config.log_level)

        logger.info(
            "Starting Mattermost MCP server with configuration",
            mattermost_url=config.mattermost_url,
            team_id=config.team_id,
            webhook_secret_set=bool(config.webhook_secret),
            ws_url=config.ws_url,
            default_channel=config.default_channel,
            host=config.host,
            port=config.port,
            streaming_enabled=config.enable_streaming,
            polling_enabled=config.enable_polling,
            polling_interval=config.polling_interval,
        )

        # Create and start the server
        server = MattermostMCPServer(
            mattermost_url=config.mattermost_url,
            mattermost_token=config.mattermost_token,
            team_id=config.team_id,
            enable_streaming=config.enable_streaming,
            enable_polling=config.enable_polling,
            polling_interval=config.polling_interval,
            # Pass additional config for future use
            webhook_secret=config.webhook_secret,
            ws_url=config.ws_url,
            default_channel=config.default_channel,
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
        logger.error("Failed to start server", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
