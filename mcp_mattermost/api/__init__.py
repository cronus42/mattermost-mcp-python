"""
Mattermost API client and HTTP utilities.

This module provides HTTP client functionality for interacting with the
Mattermost API, including authentication, request handling, and error management.
"""

from .client import AsyncHTTPClient, RateLimiter, create_http_client
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ConnectionError,
    HTTPError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
    create_http_exception,
)

__all__ = [
    # HTTP Client
    "AsyncHTTPClient",
    "RateLimiter",
    "create_http_client",
    # Exceptions
    "HTTPError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "ServerError",
    "TimeoutError",
    "ConnectionError",
    "create_http_exception",
]
