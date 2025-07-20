"""
Base service class for Mattermost API services.

This module provides a common base class with HTTP client functionality
that all domain service classes inherit from.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar

import structlog

from ..api.client import AsyncHTTPClient
from ..api.exceptions import AuthenticationError, HTTPError, RateLimitError

logger = structlog.get_logger(__name__)

# More flexible type variable that can handle any type, not just MattermostBase
T = TypeVar("T")


class BaseService:
    """
    Base service class providing common HTTP client functionality.

    All domain services inherit from this class to get consistent
    error handling, logging, and response parsing.
    """

    def __init__(self, client: AsyncHTTPClient):
        """
        Initialize the base service.

        Args:
            client: Configured AsyncHTTPClient instance
        """
        self.client = client
        self.logger = logger.bind(service=self.__class__.__name__)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        response_model: Type[T],
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Make an HTTP request and parse the response into a model.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint
            response_model: Pydantic model to parse response into
            data: Request body data
            params: Query parameters
            headers: Additional headers

        Returns:
            Parsed response model instance

        Raises:
            HTTPError: For HTTP errors
            AuthenticationError: For authentication failures
            RateLimitError: For rate limiting
        """
        try:
            self.logger.info(
                "Making API request",
                method=method,
                endpoint=endpoint,
                has_data=data is not None,
            )

            response_data = await self.client.request(
                method=method,
                endpoint=endpoint,
                data=data,
                params=params,
                headers=headers,
            )

            # Handle special cases for response parsing
            return self._parse_response(response_data, response_model)

        except (HTTPError, AuthenticationError, RateLimitError) as e:
            self.logger.error(
                "API request failed",
                method=method,
                endpoint=endpoint,
                error=str(e),
                status_code=getattr(e, "status_code", None),
            )
            raise
        except Exception as e:
            self.logger.error(
                "Unexpected error in API request",
                method=method,
                endpoint=endpoint,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPError(f"Unexpected error: {e}")

    def _parse_response(self, response_data: Any, response_model: Type[T]) -> Any:
        """Parse response data based on response model type."""
        # Handle None responses
        if response_data is None:
            if hasattr(response_model, "model_validate"):
                return response_model()
            return None

        # Handle List[Model] types - check for typing generics
        if hasattr(response_model, "__origin__"):
            origin = getattr(response_model, "__origin__", None)
            if origin is list:
                item_type = getattr(response_model, "__args__", [None])[0]
                if item_type and isinstance(response_data, list):
                    return [item_type.model_validate(item) for item in response_data]
                else:
                    raise ValueError(
                        f"Expected list response, got {type(response_data)}"
                    )
            elif origin is dict:
                # For Dict[str, Model] types
                args = getattr(response_model, "__args__", [])
                if len(args) == 2:
                    _, value_type = args
                    if hasattr(value_type, "model_validate") and isinstance(
                        response_data, dict
                    ):
                        return {
                            k: value_type.model_validate(v)
                            for k, v in response_data.items()
                        }
                return response_data

        # Handle regular Pydantic models
        if hasattr(response_model, "model_validate"):
            # type: ignore[attr-defined]
            return response_model.model_validate(response_data)

        # For non-pydantic types, return as-is
        return response_data

    async def _make_list_request(
        self,
        method: str,
        endpoint: str,
        item_model: Type[T],
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[T]:
        """
        Make an HTTP request expecting a list response.

        Args:
            method: HTTP method
            endpoint: API endpoint
            item_model: Pydantic model for list items
            data: Request body data
            params: Query parameters
            headers: Additional headers

        Returns:
            List of parsed model instances
        """
        try:
            response_data = await self.client.request(
                method=method,
                endpoint=endpoint,
                data=data,
                params=params,
                headers=headers,
            )

            if not isinstance(response_data, list):
                raise ValueError(f"Expected list response, got {type(response_data)}")

            # type: ignore[attr-defined]
            return [item_model.model_validate(item) for item in response_data]

        except (HTTPError, AuthenticationError, RateLimitError):
            raise
        except Exception as e:
            self.logger.error(
                "Error parsing list response",
                method=method,
                endpoint=endpoint,
                error=str(e),
            )
            raise HTTPError(f"Error parsing list response: {e}")

    async def _get(
        self,
        endpoint: str,
        response_model: Type[T],
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> T:
        """Make a GET request."""
        return await self._make_request(
            "GET", endpoint, response_model, params=params, headers=headers
        )

    async def _get_list(
        self,
        endpoint: str,
        item_model: Type[T],
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[T]:
        """Make a GET request expecting a list response."""
        return await self._make_list_request(
            "GET", endpoint, item_model, params=params, headers=headers
        )

    async def _post(
        self,
        endpoint: str,
        response_model: Type[T],
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> T:
        """Make a POST request."""
        return await self._make_request(
            "POST", endpoint, response_model, data=data, params=params, headers=headers
        )

    async def _put(
        self,
        endpoint: str,
        response_model: Type[T],
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> T:
        """Make a PUT request."""
        return await self._make_request(
            "PUT", endpoint, response_model, data=data, params=params, headers=headers
        )

    async def _patch(
        self,
        endpoint: str,
        response_model: Type[T],
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> T:
        """Make a PATCH request."""
        return await self._make_request(
            "PATCH", endpoint, response_model, data=data, params=params, headers=headers
        )

    async def _delete(
        self,
        endpoint: str,
        response_model: Type[T],
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> T:
        """Make a DELETE request."""
        return await self._make_request(
            "DELETE", endpoint, response_model, params=params, headers=headers
        )

    def _build_query_params(self, **kwargs) -> Dict[str, Any]:
        """
        Build query parameters from keyword arguments, filtering out None values.

        Args:
            **kwargs: Query parameter values

        Returns:
            Dictionary of non-None query parameters
        """
        return {k: v for k, v in kwargs.items() if v is not None}
