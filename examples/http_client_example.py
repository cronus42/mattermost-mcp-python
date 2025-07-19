#!/usr/bin/env python3
"""
Example usage of the AsyncHTTPClient for Mattermost API interactions.

This example demonstrates how to use the HTTP client with various features
including authentication, error handling, and different HTTP methods.
"""

import asyncio
import os
from mcp_mattermost.api import AsyncHTTPClient, create_http_client
from mcp_mattermost.api.exceptions import (
    HTTPError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
)


async def basic_usage_example():
    """Demonstrate basic HTTP client usage."""
    print("=== Basic Usage Example ===")
    
    # Initialize client with token authentication
    base_url = "https://your-mattermost-server.com/api/v4"
    token = os.getenv("MATTERMOST_TOKEN", "your-token-here")
    
    async with AsyncHTTPClient(base_url, token=token) as client:
        try:
            # GET request example
            print("Fetching user information...")
            user_info = await client.get("/users/me")
            print(f"User: {user_info.get('username', 'Unknown')}")
            
            # POST request with JSON data
            print("Creating a new post...")
            post_data = {
                "channel_id": "channel-id-here",
                "message": "Hello from the HTTP client!"
            }
            new_post = await client.post("/posts", json=post_data)
            print(f"Created post with ID: {new_post.get('id')}")
            
        except AuthenticationError:
            print("Authentication failed - check your token")
        except NotFoundError as e:
            print(f"Resource not found: {e}")
        except HTTPError as e:
            print(f"HTTP error occurred: {e}")


async def advanced_features_example():
    """Demonstrate advanced HTTP client features."""
    print("\n=== Advanced Features Example ===")
    
    # Create client with custom configuration
    client = AsyncHTTPClient(
        base_url="https://api.example.com",
        token="your-token",
        timeout=45.0,                    # 45-second timeout
        max_retries=5,                   # Retry up to 5 times
        retry_backoff_factor=2.0,        # Exponential backoff
        rate_limit_requests_per_second=5,  # Rate limiting
        rate_limit_burst=10,             # Burst capacity
        verify_ssl=True,                 # SSL verification
    )
    
    async with client:
        try:
            # The client will automatically:
            # - Add authentication headers
            # - Retry failed requests with exponential backoff
            # - Apply rate limiting
            # - Parse JSON responses
            # - Handle various error types
            
            print("Making requests with advanced features...")
            
            # Multiple requests will be rate-limited automatically
            for i in range(3):
                try:
                    response = await client.get(f"/test-endpoint/{i}")
                    print(f"Request {i+1} completed successfully")
                except RateLimitError as e:
                    print(f"Rate limited on request {i+1}: {e}")
                    # Client will automatically handle retry-after headers
                    
        except Exception as e:
            print(f"Error in advanced example: {e}")


async def convenience_context_manager_example():
    """Demonstrate the convenience context manager."""
    print("\n=== Convenience Context Manager Example ===")
    
    base_url = "https://api.example.com"
    token = "your-token"
    
    # Use the convenience function for simple cases
    async with create_http_client(base_url, token, timeout=30.0) as client:
        try:
            # All HTTP methods are available
            await client.get("/users")
            await client.post("/posts", json={"message": "Hello!"})
            await client.put("/posts/123", json={"message": "Updated!"})
            await client.patch("/posts/123", json={"message": "Patched!"})
            await client.delete("/posts/123")
            
            print("All HTTP methods demonstrated successfully")
            
        except HTTPError as e:
            print(f"HTTP error: {e}")


async def error_handling_example():
    """Demonstrate comprehensive error handling."""
    print("\n=== Error Handling Example ===")
    
    async with create_http_client("https://api.example.com", "invalid-token") as client:
        # Different types of errors that might occur
        error_scenarios = [
            ("/unauthorized", "This should trigger AuthenticationError"),
            ("/not-found", "This should trigger NotFoundError"),
            ("/rate-limited", "This should trigger RateLimitError"),
            ("/server-error", "This should trigger ServerError"),
        ]
        
        for endpoint, description in error_scenarios:
            try:
                print(f"\nTesting: {description}")
                await client.get(endpoint)
                
            except AuthenticationError as e:
                print(f"Authentication error: {e}")
                print(f"Status code: {e.status_code}")
                
            except NotFoundError as e:
                print(f"Not found error: {e}")
                print(f"Status code: {e.status_code}")
                
            except RateLimitError as e:
                print(f"Rate limit error: {e}")
                print(f"Retry after: {e.retry_after} seconds")
                
            except HTTPError as e:
                print(f"General HTTP error: {e}")
                print(f"Status code: {e.status_code}")
                
            except Exception as e:
                print(f"Unexpected error: {e}")


async def rate_limiting_example():
    """Demonstrate rate limiting functionality."""
    print("\n=== Rate Limiting Example ===")
    
    # Client with aggressive rate limiting for demonstration
    async with AsyncHTTPClient(
        "https://httpbin.org",  # Using httpbin for testing
        rate_limit_requests_per_second=2,  # Only 2 requests per second
        rate_limit_burst=3,                 # Allow 3 initial requests
    ) as client:
        print("Making rapid requests (should be rate limited)...")
        
        import time
        start_time = time.time()
        
        # Make 5 requests rapidly
        for i in range(5):
            try:
                request_start = time.time()
                response = await client.get(f"/delay/0?request={i}")
                request_end = time.time()
                
                elapsed_total = request_end - start_time
                elapsed_request = request_end - request_start
                
                print(f"Request {i+1}: completed in {elapsed_request:.2f}s "
                      f"(total elapsed: {elapsed_total:.2f}s)")
                
            except Exception as e:
                print(f"Request {i+1} failed: {e}")
        
        total_time = time.time() - start_time
        print(f"\nTotal time for 5 requests: {total_time:.2f}s")
        print("Notice how requests were automatically rate-limited!")


async def main():
    """Run all examples."""
    print("AsyncHTTPClient Examples")
    print("=" * 50)
    
    # Note: Most of these examples will fail with real requests
    # since we're using placeholder URLs and tokens.
    # They're meant to demonstrate the client's interface and features.
    
    try:
        await basic_usage_example()
    except Exception as e:
        print(f"Basic example error (expected): {e}")
    
    try:
        await advanced_features_example()
    except Exception as e:
        print(f"Advanced example error (expected): {e}")
    
    try:
        await convenience_context_manager_example()
    except Exception as e:
        print(f"Context manager example error (expected): {e}")
    
    try:
        await error_handling_example()
    except Exception as e:
        print(f"Error handling example error (expected): {e}")
    
    # This one might actually work since it uses httpbin.org
    try:
        await rate_limiting_example()
    except Exception as e:
        print(f"Rate limiting example error: {e}")
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo use with a real Mattermost server:")
    print("1. Set MATTERMOST_TOKEN environment variable")
    print("2. Update base_url to your Mattermost server")
    print("3. Replace placeholder channel IDs and other values")


if __name__ == "__main__":
    asyncio.run(main())
