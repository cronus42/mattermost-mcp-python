"""
Asynchronous HTTP client wrapper for Mattermost API interactions.

This module provides a comprehensive HTTP client built on httpx.AsyncClient with
support for token authentication, automatic retries, rate limiting, and JSON parsing.
"""

import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
import structlog

from ..metrics import metrics
from .exceptions import (
    AuthenticationError,
    HTTPError,
    RateLimitError,
)

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_second: float = 10.0, burst: int = 20):
        self.requests_per_second = requests_per_second
        self.burst = burst
        self.tokens = float(burst)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token for making a request."""
        async with self._lock:
            now = time.monotonic()
            # Add tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(
                float(self.burst), self.tokens + elapsed * self.requests_per_second
            )
            self.last_refill = now

            if self.tokens >= 1:
                self.tokens -= 1
                return

            # Wait for token to become available
            wait_time = (1 - self.tokens) / self.requests_per_second
            await asyncio.sleep(wait_time)
            self.tokens = 0


class AsyncHTTPClient:
    """
    Asynchronous HTTP client wrapper with advanced features.

    Features:
    - Token-based authentication
    - Automatic retries with exponential backoff
    - Rate limiting
    - JSON parsing and serialization
    - Request/response logging
    - Proper error handling
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 1.0,
        retry_on_status: Optional[List[int]] = None,
        rate_limit_requests_per_second: float = 10.0,
        rate_limit_burst: int = 20,
        headers: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True,
    ):
        """
        Initialize the HTTP client.

        Args:
            base_url: Base URL for all requests
            token: Authentication token
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff_factor: Multiplier for retry delays
            retry_on_status: HTTP status codes to retry on
            rate_limit_requests_per_second: Rate limit threshold
            rate_limit_burst: Maximum burst requests
            headers: Default headers for all requests
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.retry_on_status = retry_on_status or [429, 500, 502, 503, 504]
        self.verify_ssl = verify_ssl

        # Rate limiter
        self.rate_limiter = RateLimiter(
            requests_per_second=rate_limit_requests_per_second, burst=rate_limit_burst
        )

        # Default headers
        self.default_headers = {
            "User-Agent": "mattermost-mcp-client/0.1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if headers:
            self.default_headers.update(headers)

        # Add authorization header if token is provided
        if self.token:
            self.default_headers["Authorization"] = f"Bearer {self.token}"

        # HTTP client (will be initialized in async context)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                verify=self.verify_ssl,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith(("http://", "https://")):
            return endpoint
        return urljoin(f"{self.base_url}/", endpoint.lstrip("/"))

    def _prepare_headers(
        self, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Prepare request headers by merging defaults with provided headers."""
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        return request_headers

    def _prepare_data(self, data: Any) -> Tuple[Optional[str], Dict[str, str]]:
        """
        Prepare request data and update headers accordingly.

        Returns:
            Tuple of (serialized_data, updated_headers)
        """
        headers: Dict[str, str] = {}

        if data is None:
            return None, headers

        if isinstance(data, (dict, list)):
            # JSON data
            serialized = json.dumps(data, separators=(",", ":"))
            headers["Content-Type"] = "application/json"
            return serialized, headers
        elif isinstance(data, str):
            # String data
            return data, headers
        else:
            # Try to serialize as JSON
            try:
                serialized = json.dumps(data, separators=(",", ":"))
                headers["Content-Type"] = "application/json"
                return serialized, headers
            except (TypeError, ValueError):
                # Fall back to string representation
                return str(data), headers

    def _parse_response_data(self, response: httpx.Response) -> Any:
        """Parse response data, attempting JSON first."""
        content_type = response.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            try:
                return response.json()
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("Failed to parse JSON response", error=str(e))
                return response.text

        return response.text

    async def _handle_response(self, response: httpx.Response) -> Any:
        """Handle response and check for errors."""
        # Handle rate limiting
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    wait_time = float(retry_after)
                    logger.warning("Rate limited, waiting", wait_time=wait_time)
                    await asyncio.sleep(wait_time)
                except ValueError:
                    pass

            raise RateLimitError(
                f"Rate limit exceeded: {response.status_code}",
                status_code=response.status_code,
                response=response,
            )

        # Handle authentication errors
        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed",
                status_code=response.status_code,
                response=response,
            )

        # Handle other client/server errors
        if response.status_code >= 400:
            from .exceptions import create_http_exception

            raise create_http_exception(response)

        return self._parse_response_data(response)

    async def _make_request_with_retries(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        client = await self._ensure_client()
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting
                await self.rate_limiter.acquire()

                # Make the request
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    content=data,
                    params=params,
                )

                # Check if we should retry based on status code
                if (
                    attempt < self.max_retries
                    and response.status_code in self.retry_on_status
                ):
                    wait_time = self.retry_backoff_factor * (2**attempt)
                    logger.warning(
                        "Request failed, retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        status_code=response.status_code,
                        wait_time=wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue

                return response

            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e

                if attempt < self.max_retries:
                    wait_time = self.retry_backoff_factor * (2**attempt)
                    logger.warning(
                        "Request failed with exception, retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        error=str(e),
                        wait_time=wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue

                break

        # If we get here, all retries failed
        if last_exception:
            raise HTTPError(
                f"Request failed after {self.max_retries} retries: {last_exception}"
            )
        else:
            raise HTTPError(f"Request failed after {self.max_retries} retries")

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Make an HTTP request with comprehensive metrics collection and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint or full URL
            data: Request data (will be JSON-serialized if dict/list)
            json: JSON data (alternative to data parameter)
            params: URL parameters
            headers: Additional headers

        Returns:
            Parsed response data
        """
        start_time = time.time()
        status_code = 200
        error_type = None

        # Use json parameter if provided, otherwise use data
        request_data = json if json is not None else data

        # Prepare URL and headers
        url = self._build_url(endpoint)
        request_headers = self._prepare_headers(headers)

        # Prepare data
        serialized_data, data_headers = self._prepare_data(request_data)
        request_headers.update(data_headers)

        # Log request with structured context
        logger.info(
            "Making HTTP request",
            method=method,
            url=url,
            endpoint=endpoint,
            has_data=serialized_data is not None,
            params=params,
            request_id=id(self),  # Simple request correlation ID
        )

        try:
            # Make request with retries
            response = await self._make_request_with_retries(
                method=method,
                url=url,
                headers=request_headers,
                data=serialized_data,
                params=params,
            )

            status_code = response.status_code

            # Handle response
            result = await self._handle_response(response)

            logger.info(
                "HTTP request completed successfully",
                method=method,
                url=url,
                endpoint=endpoint,
                status_code=status_code,
                request_id=id(self),
            )

            return result

        except Exception as e:
            error_type = type(e).__name__

            # Extract status code from exception if available
            if hasattr(e, "status_code") and e.status_code:
                status_code = e.status_code
            else:
                status_code = 500

            # Log error with comprehensive context
            logger.error(
                "HTTP request failed",
                method=method,
                url=url,
                endpoint=endpoint,
                error_type=error_type,
                error=str(e),
                status_code=status_code,
                request_id=id(self),
                exc_info=True,
            )

            # Re-raise the original exception
            raise

        finally:
            # Always record metrics regardless of success/failure
            duration = time.time() - start_time

            # Record comprehensive metrics
            metrics.record_request_latency(method, endpoint, status_code, duration)
            metrics.record_request_count(method, endpoint, status_code)

            # Record error metrics if applicable
            if error_type:
                metrics.record_error(error_type, endpoint)

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a GET request."""
        return await self.request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        data: Any = None,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a POST request."""
        return await self.request(
            "POST", endpoint, data=data, json=json, params=params, headers=headers
        )

    async def put(
        self,
        endpoint: str,
        data: Any = None,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a PUT request."""
        return await self.request(
            "PUT", endpoint, data=data, json=json, params=params, headers=headers
        )

    async def patch(
        self,
        endpoint: str,
        data: Any = None,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a PATCH request."""
        return await self.request(
            "PATCH", endpoint, data=data, json=json, params=params, headers=headers
        )

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a DELETE request."""
        return await self.request("DELETE", endpoint, params=params, headers=headers)

    async def head(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a HEAD request."""
        return await self.request("HEAD", endpoint, params=params, headers=headers)

    async def options(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an OPTIONS request."""
        return await self.request("OPTIONS", endpoint, params=params, headers=headers)


@asynccontextmanager
async def create_http_client(
    base_url: str, token: Optional[str] = None, **kwargs
) -> AsyncIterator[AsyncHTTPClient]:
    """
    Context manager for creating and properly closing an HTTP client.

    Args:
        base_url: Base URL for the API
        token: Authentication token
        **kwargs: Additional arguments passed to AsyncHTTPClient

    Yields:
        Configured AsyncHTTPClient instance
    """
    client = AsyncHTTPClient(base_url=base_url, token=token, **kwargs)
    try:
        async with client:
            yield client
    finally:
        await client.close()
