#!/usr/bin/env python3
"""
Example demonstrating error handling, structured logging, and metrics collection
in the Mattermost MCP server.

This example shows:
1. How to enable and use Prometheus metrics
2. Structured error logging with context
3. Error handling best practices
4. Metrics endpoint exposure
"""

import asyncio
import os
from typing import Optional
import structlog

# Configure structured logging for the example
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
        structlog.dev.ConsoleRenderer(),  # Pretty console output for examples
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def example_with_metrics_and_error_handling():
    """
    Example demonstrating comprehensive error handling and metrics collection.
    """
    from mcp_mattermost.server import MattermostMCPServer
    from mcp_mattermost.metrics import metrics, measure_async_duration
    from mcp_mattermost.api.exceptions import HTTPError, AuthenticationError
    
    # Configuration from environment
    mattermost_url = os.getenv("MATTERMOST_URL", "https://your-mattermost.example.com")
    mattermost_token = os.getenv("MATTERMOST_TOKEN", "your-token-here")
    team_id = os.getenv("MATTERMOST_TEAM_ID")
    
    logger.info(
        "Starting Mattermost MCP example",
        url=mattermost_url,
        team_id=team_id,
        metrics_enabled=metrics.enabled,
    )
    
    # Create server with comprehensive configuration
    server = MattermostMCPServer(
        mattermost_url=mattermost_url,
        mattermost_token=mattermost_token,
        team_id=team_id,
        enable_streaming=True,
        enable_polling=True,
        polling_interval=30.0,
        channel_ids=None,  # Monitor all channels
    )
    
    try:
        # Demonstrate error handling during server startup
        logger.info("Attempting to start MCP server")
        
        async with measure_async_duration("server_startup"):
            await server.start()
        
        logger.info(
            "Server started successfully",
            is_running=server.is_running,
            is_connected=server.is_connected,
        )
        
        # Demonstrate metrics collection
        if metrics.enabled:
            logger.info("Metrics collection is enabled")
            
            # Record some example metrics
            metrics.record_resource_update("posts", "created")
            metrics.record_resource_update("reactions", "added")
            metrics.set_active_connections(1)
            
            # Get metrics in Prometheus format
            prometheus_metrics = server.get_metrics()
            if prometheus_metrics:
                logger.info(
                    "Metrics collected",
                    metrics_lines=len(prometheus_metrics.split('\n')),
                    content_type=server.get_metrics_content_type(),
                )
                
                # You could expose these metrics via HTTP endpoint:
                # Example: serve metrics at /metrics endpoint
                print("\n=== Sample Prometheus Metrics ===")
                print(prometheus_metrics[:500] + "..." if len(prometheus_metrics) > 500 else prometheus_metrics)
                print("=================================\n")
        else:
            logger.info("Metrics collection is disabled (prometheus-client not available)")
        
        # Demonstrate resource operations with error handling
        try:
            resources = server.get_resources()
            logger.info("Retrieved resources", count=len(resources))
            
            for resource in resources:
                logger.info(
                    "Resource available",
                    uri=resource.get('uri'),
                    name=resource.get('name'),
                    mime_type=resource.get('mimeType'),
                )
        
        except Exception as e:
            # Demonstrate structured error logging
            logger.error(
                "Failed to retrieve resources",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            
            # Record error metrics
            metrics.record_error(type(e).__name__, "resources")
        
        # Simulate some operations and error scenarios
        await simulate_operations_with_error_handling(server)
        
        # Keep server running for a short time to demonstrate metrics
        logger.info("Server running, waiting for events...")
        await asyncio.sleep(5)
        
    except AuthenticationError as e:
        logger.error(
            "Authentication failed",
            url=mattermost_url,
            error=str(e),
            status_code=getattr(e, 'status_code', None),
            error_context=getattr(e, 'get_error_context', lambda: {})(),
        )
        metrics.record_error("AuthenticationError", "server_startup")
        
    except HTTPError as e:
        logger.error(
            "HTTP error during server operation",
            url=mattermost_url,
            error=str(e),
            status_code=getattr(e, 'status_code', None),
            error_context=getattr(e, 'get_error_context', lambda: {})(),
        )
        metrics.record_error("HTTPError", "server_startup")
        
    except Exception as e:
        logger.error(
            "Unexpected error during server operation",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        metrics.record_error(type(e).__name__, "server_startup")
        
    finally:
        # Always cleanup gracefully
        try:
            logger.info("Shutting down server")
            await server.stop()
            logger.info("Server shutdown completed")
            
        except Exception as e:
            logger.error(
                "Error during server shutdown",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )


async def simulate_operations_with_error_handling(server: 'MattermostMCPServer'):
    """
    Simulate various operations to demonstrate error handling and metrics.
    """
    from mcp_mattermost.metrics import measure_async_duration
    
    logger.info("Simulating operations with error handling")
    
    # Simulate reading resources with error handling
    try:
        async with measure_async_duration("resource_read_simulation", {"operation": "list_resources"}):
            resources = server.get_resources()
            
            for resource in resources:
                resource_uri = resource.get('uri')
                if resource_uri:
                    try:
                        logger.info("Attempting to read resource", uri=resource_uri)
                        
                        # This would normally read actual resource data
                        # For demo purposes, we'll just simulate the operation
                        await asyncio.sleep(0.1)  # Simulate work
                        
                        logger.info("Resource read successful", uri=resource_uri)
                        
                    except Exception as e:
                        logger.error(
                            "Failed to read resource",
                            uri=resource_uri,
                            error=str(e),
                            error_type=type(e).__name__,
                            exc_info=True,
                        )
                        
    except Exception as e:
        logger.error(
            "Failed to simulate resource operations",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )


def start_metrics_http_server(server: 'MattermostMCPServer', port: int = 8080):
    """
    Example of how to start a simple HTTP server to expose metrics.
    
    In a real application, you might integrate this with your existing HTTP server
    or use a dedicated metrics server like prometheus_client.start_http_server().
    """
    import http.server
    import socketserver
    from urllib.parse import urlparse
    
    class MetricsHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/metrics':
                metrics_data = server.get_metrics()
                if metrics_data:
                    self.send_response(200)
                    self.send_header('Content-Type', server.get_metrics_content_type())
                    self.end_headers()
                    self.wfile.write(metrics_data.encode('utf-8'))
                else:
                    self.send_response(503)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Metrics not available\n')
            elif parsed_path.path == '/health':
                status = 200 if server.is_running else 503
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                health_data = {
                    "status": "healthy" if server.is_running else "unhealthy",
                    "running": server.is_running,
                    "connected": server.is_connected
                }
                import json
                self.wfile.write(json.dumps(health_data).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found\n')
        
        def log_message(self, format, *args):
            # Use structured logger instead of default logging
            logger.info("HTTP request", method=self.command, path=self.path, 
                       client=self.client_address[0])
    
    try:
        with socketserver.TCPServer(("", port), MetricsHandler) as httpd:
            logger.info("Metrics HTTP server started", port=port, 
                       endpoints=["/metrics", "/health"])
            httpd.serve_forever()
    except Exception as e:
        logger.error("Failed to start metrics HTTP server", 
                    port=port, error=str(e), exc_info=True)


if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = ["MATTERMOST_URL", "MATTERMOST_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(
            "Required environment variables not set",
            missing_variables=missing_vars,
            required_variables=required_vars,
        )
        logger.info(
            "Please set the following environment variables:",
            example_commands=[
                f"export {var}=your_value_here" for var in missing_vars
            ]
        )
        exit(1)
    
    # Run the example
    try:
        asyncio.run(example_with_metrics_and_error_handling())
    except KeyboardInterrupt:
        logger.info("Example interrupted by user")
    except Exception as e:
        logger.error(
            "Example failed with unexpected error",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        exit(1)
