"""
Exception classes for HTTP client operations.

This module defines custom exception classes used throughout the HTTP client
for different types of errors that can occur during API interactions.
"""

from typing import Optional, Dict, Any
import httpx
import structlog


class HTTPError(Exception):
    """
    Base exception for HTTP-related errors.
    
    This is the base class for all HTTP client exceptions. It provides
    access to the HTTP status code and the original response object
    for detailed error handling, plus structured error context for logging.
    """
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None, 
        response: Optional[httpx.Response] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize HTTPError.
        
        Args:
            message: Error message describing what went wrong
            status_code: HTTP status code from the response
            response: Original httpx.Response object
            context: Additional error context for structured logging
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response
        self.context = context or {}
        
        # Build comprehensive error context
        self.error_context = {
            "error_type": self.__class__.__name__,
            "message": message,
            "status_code": status_code,
            **self.context
        }
        
        if response is not None:
            self.error_context.update({
                "url": str(response.url),
                "method": response.request.method if response.request else None,
                "headers": dict(response.headers),
                "response_size": len(response.content) if response.content else 0,
            })
        
        # Log the error with structured context
        logger = structlog.get_logger(__name__)
        logger.error(
            "HTTP error occurred",
            **self.error_context
        )
    
    def get_error_context(self) -> Dict[str, Any]:
        """Get structured error context for logging and debugging."""
        return self.error_context.copy()
    
    def __str__(self) -> str:
        """String representation with context information."""
        base_msg = super().__str__()
        if self.status_code:
            return f"{base_msg} (HTTP {self.status_code})"
        return base_msg


class AuthenticationError(HTTPError):
    """
    Exception raised for authentication-related errors.
    
    This exception is raised when:
    - Invalid or expired authentication tokens are used
    - Authentication is required but not provided
    - 401 Unauthorized responses are received
    """
    pass


class AuthorizationError(HTTPError):
    """
    Exception raised for authorization-related errors.
    
    This exception is raised when:
    - The authenticated user lacks permission for the requested resource
    - 403 Forbidden responses are received
    """
    pass


class RateLimitError(HTTPError):
    """
    Exception raised when rate limits are exceeded.
    
    This exception is raised when:
    - 429 Too Many Requests responses are received
    - API rate limits have been exceeded
    """
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None, 
        response: Optional[httpx.Response] = None,
        retry_after: Optional[float] = None
    ):
        """
        Initialize RateLimitError.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response: Original response object
            retry_after: Number of seconds to wait before retrying
        """
        super().__init__(message, status_code, response)
        self.retry_after = retry_after


class ValidationError(HTTPError):
    """
    Exception raised for request validation errors.
    
    This exception is raised when:
    - 400 Bad Request responses are received
    - Request data fails validation
    - Required parameters are missing
    """
    pass


class NotFoundError(HTTPError):
    """
    Exception raised when requested resources are not found.
    
    This exception is raised when:
    - 404 Not Found responses are received
    - Requested resources do not exist
    """
    pass


class ConflictError(HTTPError):
    """
    Exception raised for resource conflict errors.
    
    This exception is raised when:
    - 409 Conflict responses are received
    - Resource conflicts occur (e.g., duplicate creation)
    """
    pass


class ServerError(HTTPError):
    """
    Exception raised for server-side errors.
    
    This exception is raised when:
    - 5xx Server Error responses are received
    - Internal server errors occur
    """
    pass


class TimeoutError(HTTPError):
    """
    Exception raised when requests time out.
    
    This exception is raised when:
    - Requests exceed the configured timeout period
    - Connection timeouts occur
    """
    pass


class ConnectionError(HTTPError):
    """
    Exception raised for connection-related errors.
    
    This exception is raised when:
    - Network connectivity issues occur
    - DNS resolution fails
    - Connection cannot be established
    """
    pass


def create_http_exception(
    response: httpx.Response, 
    default_message: Optional[str] = None
) -> HTTPError:
    """
    Create appropriate HTTP exception based on response status code.
    
    This function examines the HTTP response and creates the most appropriate
    exception type based on the status code.
    
    Args:
        response: The HTTP response object
        default_message: Default error message if none can be extracted
        
    Returns:
        Appropriate HTTPError subclass instance
    """
    status_code = response.status_code
    
    # Try to extract error message from response
    message = default_message or f"HTTP {status_code}"
    
    try:
        if 'application/json' in response.headers.get('content-type', ''):
            error_data = response.json()
            if isinstance(error_data, dict):
                # Try different common error message fields
                for field in ['message', 'error', 'detail', 'error_description']:
                    if field in error_data:
                        message = f"HTTP {status_code}: {error_data[field]}"
                        break
    except Exception:
        # If we can't parse the error response, use the default message
        pass
    
    # Create appropriate exception based on status code
    if status_code == 400:
        return ValidationError(message, status_code, response)
    elif status_code == 401:
        return AuthenticationError(message, status_code, response)
    elif status_code == 403:
        return AuthorizationError(message, status_code, response)
    elif status_code == 404:
        return NotFoundError(message, status_code, response)
    elif status_code == 409:
        return ConflictError(message, status_code, response)
    elif status_code == 429:
        # Extract retry-after header if present
        retry_after = None
        retry_after_header = response.headers.get('Retry-After')
        if retry_after_header:
            try:
                retry_after = float(retry_after_header)
            except ValueError:
                pass
        return RateLimitError(message, status_code, response, retry_after)
    elif 500 <= status_code < 600:
        return ServerError(message, status_code, response)
    else:
        return HTTPError(message, status_code, response)
