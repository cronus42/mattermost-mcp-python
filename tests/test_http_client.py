"""
Tests for the AsyncHTTPClient implementation.

This module tests the HTTP client functionality including authentication,
retry logic, rate limiting, and error handling.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from mcp_mattermost.api.client import AsyncHTTPClient, RateLimiter, create_http_client
from mcp_mattermost.api.exceptions import (
    HTTPError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError,
)


class TestRateLimiter:
    """Test the RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiting functionality."""
        limiter = RateLimiter(requests_per_second=2.0, burst=3)
        
        # Should allow burst requests immediately
        for _ in range(3):
            await limiter.acquire()
        
        # Next request should be delayed
        import time
        start_time = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start_time
        
        # Should have waited approximately 0.5 seconds (1/2 requests per second)
        assert elapsed >= 0.4  # Allow some tolerance for timing
    
    @pytest.mark.asyncio
    async def test_rate_limiter_refill(self):
        """Test that tokens are refilled over time."""
        limiter = RateLimiter(requests_per_second=10.0, burst=1)
        
        # Use the single token
        await limiter.acquire()
        
        # Wait for refill
        await asyncio.sleep(0.2)
        
        # Should be able to acquire again without significant delay
        start_time = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start_time
        
        # Should be nearly instantaneous
        assert elapsed < 0.1


class TestAsyncHTTPClient:
    """Test the AsyncHTTPClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.base_url = "https://api.example.com"
        self.token = "test-token-123"
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization."""
        client = AsyncHTTPClient(
            base_url=self.base_url,
            token=self.token,
            timeout=60.0,
            max_retries=5,
        )
        
        assert client.base_url == self.base_url
        assert client.token == self.token
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.default_headers['Authorization'] == f'Bearer {self.token}'
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        async with AsyncHTTPClient(self.base_url, self.token) as client:
            assert client._client is not None
        
        # Client should be closed after exiting context
        assert client._client is None
    
    @pytest.mark.asyncio
    async def test_url_building(self):
        """Test URL building functionality."""
        client = AsyncHTTPClient(self.base_url)
        
        # Test relative endpoint
        url = client._build_url("/api/v4/users")
        assert url == "https://api.example.com/api/v4/users"
        
        # Test endpoint without leading slash
        url = client._build_url("api/v4/users")
        assert url == "https://api.example.com/api/v4/users"
        
        # Test absolute URL (should be unchanged)
        absolute_url = "https://other.example.com/api"
        url = client._build_url(absolute_url)
        assert url == absolute_url
    
    def test_data_preparation(self):
        """Test request data preparation."""
        client = AsyncHTTPClient(self.base_url)
        
        # Test None data
        data, headers = client._prepare_data(None)
        assert data is None
        assert headers == {}
        
        # Test dict data (should be JSON serialized)
        test_dict = {"key": "value", "number": 42}
        data, headers = client._prepare_data(test_dict)
        assert data == json.dumps(test_dict, separators=(',', ':'))
        assert headers['Content-Type'] == 'application/json'
        
        # Test string data
        test_string = "plain text"
        data, headers = client._prepare_data(test_string)
        assert data == test_string
        assert headers == {}
    
    def test_response_parsing(self):
        """Test response data parsing."""
        client = AsyncHTTPClient(self.base_url)
        
        # Mock JSON response
        json_response = MagicMock()
        json_response.headers = {'content-type': 'application/json'}
        json_response.json.return_value = {"result": "success"}
        json_response.text = '{"result": "success"}'
        
        result = client._parse_response_data(json_response)
        assert result == {"result": "success"}
        
        # Mock text response
        text_response = MagicMock()
        text_response.headers = {'content-type': 'text/plain'}
        text_response.text = "plain text response"
        
        result = client._parse_response_data(text_response)
        assert result == "plain text response"
    
    @pytest.mark.asyncio
    async def test_successful_request(self):
        """Test successful HTTP request."""
        client = AsyncHTTPClient(self.base_url, self.token)
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {"data": "test"}
        
        with patch.object(client, '_make_request_with_retries') as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.get("/test")
            
            assert result == {"data": "test"}
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """Test authentication error handling."""
        client = AsyncHTTPClient(self.base_url, self.token)
        
        # Mock 401 response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {"message": "Unauthorized"}
        
        with patch.object(client, '_make_request_with_retries') as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(AuthenticationError):
                await client.get("/test")
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test rate limit error handling."""
        client = AsyncHTTPClient(self.base_url, self.token)
        
        # Mock 429 response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60', 'content-type': 'application/json'}
        mock_response.json.return_value = {"message": "Rate limited"}
        
        with patch.object(client, '_make_request_with_retries') as mock_request:
            mock_request.return_value = mock_response
            
            with patch('asyncio.sleep') as mock_sleep:
                with pytest.raises(RateLimitError):
                    await client.get("/test")
                
                # Should have tried to wait for retry-after period
                mock_sleep.assert_called_once_with(60.0)
    
    @pytest.mark.asyncio
    async def test_http_methods(self):
        """Test all HTTP methods."""
        client = AsyncHTTPClient(self.base_url, self.token)
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {"success": True}
        
        with patch.object(client, '_make_request_with_retries') as mock_request:
            mock_request.return_value = mock_response
            
            # Test GET
            await client.get("/test")
            mock_request.assert_called_with(
                method='GET',
                url=f"{self.base_url}/test",
                headers=client._prepare_headers(),
                data=None,
                params=None,
            )
            
            # Test POST with JSON data
            test_data = {"key": "value"}
            await client.post("/test", json=test_data)
            expected_data, _ = client._prepare_data(test_data)
            mock_request.assert_called_with(
                method='POST',
                url=f"{self.base_url}/test",
                headers=client._prepare_headers({'Content-Type': 'application/json'}),
                data=expected_data,
                params=None,
            )
            
            # Test PUT
            await client.put("/test", data="test data")
            mock_request.assert_called_with(
                method='PUT',
                url=f"{self.base_url}/test",
                headers=client._prepare_headers(),
                data="test data",
                params=None,
            )
            
            # Test DELETE
            await client.delete("/test")
            mock_request.assert_called_with(
                method='DELETE',
                url=f"{self.base_url}/test",
                headers=client._prepare_headers(),
                data=None,
                params=None,
            )
    
    @pytest.mark.asyncio
    async def test_retry_logic(self):
        """Test retry logic for failed requests."""
        client = AsyncHTTPClient(
            self.base_url,
            self.token,
            max_retries=2,
            retry_backoff_factor=0.1,  # Short delays for testing
        )
        
        # Mock httpx client
        mock_httpx_client = AsyncMock()
        client._client = mock_httpx_client
        
        # First two calls fail with 500, third succeeds
        mock_responses = [
            MagicMock(status_code=500),
            MagicMock(status_code=500),
            MagicMock(status_code=200),
        ]
        mock_httpx_client.request.side_effect = mock_responses
        
        with patch('asyncio.sleep') as mock_sleep:
            with patch.object(client.rate_limiter, 'acquire') as mock_acquire:
                result = await client._make_request_with_retries(
                    method='GET',
                    url=f"{self.base_url}/test",
                    headers={},
                )
                
                # Should have made 3 requests total
                assert mock_httpx_client.request.call_count == 3
                
                # Should have slept between retries
                assert mock_sleep.call_count == 2
                
                # Should return the successful response
                assert result == mock_responses[2]
    
    @pytest.mark.asyncio
    async def test_request_timeout_retry(self):
        """Test retry logic for timeout errors."""
        client = AsyncHTTPClient(
            self.base_url,
            self.token,
            max_retries=1,
            retry_backoff_factor=0.1,
        )
        
        # Mock httpx client
        mock_httpx_client = AsyncMock()
        client._client = mock_httpx_client
        
        # First call times out, second succeeds
        mock_httpx_client.request.side_effect = [
            httpx.TimeoutException("Request timed out"),
            MagicMock(status_code=200),
        ]
        
        with patch('asyncio.sleep'):
            with patch.object(client.rate_limiter, 'acquire'):
                result = await client._make_request_with_retries(
                    method='GET',
                    url=f"{self.base_url}/test",
                    headers={},
                )
                
                # Should have made 2 requests
                assert mock_httpx_client.request.call_count == 2
                
                # Should return the successful response
                assert result.status_code == 200


class TestCreateHttpClient:
    """Test the create_http_client context manager."""
    
    @pytest.mark.asyncio
    async def test_create_http_client_context_manager(self):
        """Test the convenience context manager function."""
        base_url = "https://api.example.com"
        token = "test-token"
        
        async with create_http_client(base_url, token) as client:
            assert isinstance(client, AsyncHTTPClient)
            assert client.base_url == base_url
            assert client.token == token
            assert client._client is not None
        
        # Client should be closed after exiting
        assert client._client is None


class TestErrorHandling:
    """Test error handling and exception creation."""
    
    @pytest.mark.asyncio
    async def test_various_http_errors(self):
        """Test handling of various HTTP error status codes."""
        client = AsyncHTTPClient("https://api.example.com")
        
        error_cases = [
            (400, ValidationError),
            (401, AuthenticationError),
            (404, NotFoundError),
            (429, RateLimitError),
            (500, HTTPError),
            (502, HTTPError),
        ]
        
        for status_code, expected_exception in error_cases:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.json.return_value = {"message": f"Error {status_code}"}
            
            with patch.object(client, '_make_request_with_retries') as mock_request:
                mock_request.return_value = mock_response
                
                with pytest.raises(expected_exception):
                    await client.get("/test")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
