"""
Tests for API exception classes and error handling.

This module tests the custom exception hierarchy, error context,
structured logging, and exception creation utilities.
"""

from unittest.mock import Mock, patch

import httpx
import pytest

from mcp_mattermost.api.exceptions import (
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


class TestHTTPError:
    """Test the base HTTPError class."""

    def test_basic_initialization(self):
        """Test basic HTTPError initialization."""
        error = HTTPError("Test error", status_code=500)

        assert str(error) == "Test error (HTTP 500)"
        assert error.status_code == 500
        assert error.response is None
        assert error.context == {}

    def test_initialization_with_response(self):
        """Test HTTPError with response object."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.url = "https://api.example.com/test"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"error": "test"}'

        mock_request = Mock()
        mock_request.method = "GET"
        mock_response.request = mock_request

        with patch("structlog.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            error = HTTPError("Test error", status_code=500, response=mock_response)

            assert error.status_code == 500
            assert error.response == mock_response

            # Check error context
            context = error.get_error_context()
            assert context["error_type"] == "HTTPError"
            assert context["message"] == "Test error"
            assert context["status_code"] == 500
            assert context["url"] == "https://api.example.com/test"
            assert context["method"] == "GET"

            # Verify logging was called
            mock_log.error.assert_called_once()

    def test_initialization_with_context(self):
        """Test HTTPError with additional context."""
        context = {"user_id": "123", "endpoint": "/api/test"}
        error = HTTPError("Test error", context=context)

        error_context = error.get_error_context()
        assert error_context["user_id"] == "123"
        assert error_context["endpoint"] == "/api/test"

    def test_string_representation_without_status(self):
        """Test string representation without status code."""
        error = HTTPError("Test error")
        assert str(error) == "Test error"


class TestSpecificExceptions:
    """Test specific exception subclasses."""

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid token", status_code=401)
        assert isinstance(error, HTTPError)
        assert error.status_code == 401

    def test_authorization_error(self):
        """Test AuthorizationError."""
        error = AuthorizationError("Access denied", status_code=403)
        assert isinstance(error, HTTPError)
        assert error.status_code == 403

    def test_rate_limit_error(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError("Rate limited", status_code=429, retry_after=60.0)
        assert isinstance(error, HTTPError)
        assert error.status_code == 429
        assert error.retry_after == 60.0

    def test_rate_limit_error_without_retry_after(self):
        """Test RateLimitError without retry_after."""
        error = RateLimitError("Rate limited", status_code=429)
        assert error.retry_after is None

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid data", status_code=400)
        assert isinstance(error, HTTPError)
        assert error.status_code == 400

    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError("Resource not found", status_code=404)
        assert isinstance(error, HTTPError)
        assert error.status_code == 404

    def test_conflict_error(self):
        """Test ConflictError."""
        error = ConflictError("Resource conflict", status_code=409)
        assert isinstance(error, HTTPError)
        assert error.status_code == 409

    def test_server_error(self):
        """Test ServerError."""
        error = ServerError("Internal server error", status_code=500)
        assert isinstance(error, HTTPError)
        assert error.status_code == 500

    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError("Request timeout")
        assert isinstance(error, HTTPError)

    def test_connection_error(self):
        """Test ConnectionError."""
        error = ConnectionError("Connection failed")
        assert isinstance(error, HTTPError)


class TestCreateHttpException:
    """Test the create_http_exception utility function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_response = Mock(spec=httpx.Response)
        self.mock_response.headers = {"Content-Type": "application/json"}

    def test_create_validation_error(self):
        """Test creation of ValidationError for 400 status."""
        self.mock_response.status_code = 400
        self.mock_response.json.return_value = {"message": "Invalid input"}

        error = create_http_exception(self.mock_response)

        assert isinstance(error, ValidationError)
        assert error.status_code == 400
        assert "Invalid input" in str(error)

    def test_create_authentication_error(self):
        """Test creation of AuthenticationError for 401 status."""
        self.mock_response.status_code = 401
        self.mock_response.json.return_value = {"message": "Unauthorized"}

        error = create_http_exception(self.mock_response)

        assert isinstance(error, AuthenticationError)
        assert error.status_code == 401

    def test_create_authorization_error(self):
        """Test creation of AuthorizationError for 403 status."""
        self.mock_response.status_code = 403
        self.mock_response.json.return_value = {"message": "Forbidden"}

        error = create_http_exception(self.mock_response)

        assert isinstance(error, AuthorizationError)
        assert error.status_code == 403

    def test_create_not_found_error(self):
        """Test creation of NotFoundError for 404 status."""
        self.mock_response.status_code = 404
        self.mock_response.json.return_value = {"message": "Not found"}

        error = create_http_exception(self.mock_response)

        assert isinstance(error, NotFoundError)
        assert error.status_code == 404

    def test_create_conflict_error(self):
        """Test creation of ConflictError for 409 status."""
        self.mock_response.status_code = 409
        self.mock_response.json.return_value = {"message": "Conflict"}

        error = create_http_exception(self.mock_response)

        assert isinstance(error, ConflictError)
        assert error.status_code == 409

    def test_create_rate_limit_error_with_retry_after(self):
        """Test creation of RateLimitError with Retry-After header."""
        self.mock_response.status_code = 429
        self.mock_response.headers = {
            "Content-Type": "application/json",
            "Retry-After": "120",
        }
        self.mock_response.json.return_value = {"message": "Rate limited"}

        error = create_http_exception(self.mock_response)

        assert isinstance(error, RateLimitError)
        assert error.status_code == 429
        assert error.retry_after == 120.0

    def test_create_rate_limit_error_invalid_retry_after(self):
        """Test creation of RateLimitError with invalid Retry-After header."""
        self.mock_response.status_code = 429
        self.mock_response.headers = {
            "Content-Type": "application/json",
            "Retry-After": "invalid",
        }
        self.mock_response.json.return_value = {"message": "Rate limited"}

        error = create_http_exception(self.mock_response)

        assert isinstance(error, RateLimitError)
        assert error.retry_after is None

    def test_create_server_error(self):
        """Test creation of ServerError for 5xx status."""
        self.mock_response.status_code = 500
        self.mock_response.json.return_value = {"message": "Internal error"}

        error = create_http_exception(self.mock_response)

        assert isinstance(error, ServerError)
        assert error.status_code == 500

    def test_create_generic_http_error(self):
        """Test creation of generic HTTPError for unknown status."""
        self.mock_response.status_code = 418  # I'm a teapot
        self.mock_response.json.return_value = {"message": "I'm a teapot"}

        error = create_http_exception(self.mock_response)

        assert isinstance(error, HTTPError)
        assert type(error) == HTTPError  # Not a subclass
        assert error.status_code == 418

    def test_error_message_extraction_variants(self):
        """Test extraction of error messages from different response formats."""
        test_cases = [
            ({"message": "Test message"}, "Test message"),
            ({"error": "Test error"}, "Test error"),
            ({"detail": "Test detail"}, "Test detail"),
            ({"error_description": "Test description"}, "Test description"),
            ({"unknown_field": "Unknown"}, "HTTP 400"),  # Falls back to default
            ({}, "HTTP 400"),  # Empty response
        ]

        for response_data, expected_message in test_cases:
            self.mock_response.status_code = 400
            self.mock_response.json.return_value = response_data

            error = create_http_exception(self.mock_response)
            assert expected_message in str(error)

    def test_json_parsing_error(self):
        """Test handling of JSON parsing errors."""
        self.mock_response.status_code = 400
        self.mock_response.json.side_effect = ValueError("Invalid JSON")

        error = create_http_exception(self.mock_response, "Custom default")

        assert isinstance(error, ValidationError)
        assert "Custom default" in str(error)

    def test_non_json_response(self):
        """Test handling of non-JSON responses."""
        self.mock_response.status_code = 400
        self.mock_response.headers = {"Content-Type": "text/plain"}

        error = create_http_exception(self.mock_response)

        assert isinstance(error, ValidationError)
        assert "HTTP 400" in str(error)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
