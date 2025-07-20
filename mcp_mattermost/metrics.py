"""
Metrics collection and reporting for MCP Mattermost server.

This module provides optional Prometheus metrics integration for monitoring
API latency, error rates, and other operational metrics.
"""

import functools
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast

import structlog

logger = structlog.get_logger(__name__)

# Type hint for decorated functions
F = TypeVar("F", bound=Callable[..., Any])

# Global metrics registry - only initialized if prometheus_client is available
METRICS_ENABLED = False
PROMETHEUS_REGISTRY = None
REQUEST_LATENCY = None
REQUEST_COUNT = None
ERROR_COUNT = None
ACTIVE_CONNECTIONS = None
RESOURCE_UPDATES = None

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    METRICS_ENABLED = True
    PROMETHEUS_REGISTRY = CollectorRegistry()

    # HTTP request metrics
    REQUEST_LATENCY = Histogram(
        "mattermost_mcp_request_duration_seconds",
        "Time spent on HTTP requests to Mattermost API",
        ["method", "endpoint", "status_code"],
        registry=PROMETHEUS_REGISTRY,
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )

    REQUEST_COUNT = Counter(
        "mattermost_mcp_requests_total",
        "Total number of HTTP requests to Mattermost API",
        ["method", "endpoint", "status_code"],
        registry=PROMETHEUS_REGISTRY,
    )

    ERROR_COUNT = Counter(
        "mattermost_mcp_errors_total",
        "Total number of errors by type",
        ["error_type", "endpoint"],
        registry=PROMETHEUS_REGISTRY,
    )

    # Connection metrics
    ACTIVE_CONNECTIONS = Gauge(
        "mattermost_mcp_active_connections",
        "Number of active WebSocket connections",
        registry=PROMETHEUS_REGISTRY,
    )

    # Resource update metrics
    RESOURCE_UPDATES = Counter(
        "mattermost_mcp_resource_updates_total",
        "Total number of resource updates by type",
        ["resource_type", "update_type"],
        registry=PROMETHEUS_REGISTRY,
    )

    logger.info(
        "Prometheus metrics enabled",
        registry_size=len(PROMETHEUS_REGISTRY._collector_to_names),
    )

except ImportError:
    logger.info("Prometheus client not available, metrics disabled")


class MetricsCollector:
    """
    Centralized metrics collection and reporting.

    This class provides methods for recording various metrics and can optionally
    expose Prometheus metrics if the prometheus_client library is available.
    """

    def __init__(self, enable_prometheus: bool = True):
        """
        Initialize metrics collector.

        Args:
            enable_prometheus: Whether to enable Prometheus metrics collection
        """
        self.enabled = METRICS_ENABLED and enable_prometheus
        self.logger = logger.bind(component="metrics")

        if self.enabled:
            self.logger.info("Metrics collection enabled")
        else:
            self.logger.info("Metrics collection disabled")

    def record_request_latency(
        self, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        """
        Record HTTP request latency.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            status_code: HTTP status code
            duration: Request duration in seconds
        """
        if not self.enabled or REQUEST_LATENCY is None:
            return

        try:
            REQUEST_LATENCY.labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).observe(duration)
        except Exception as e:
            self.logger.error("Error recording request latency", error=str(e))

    def record_request_count(
        self, method: str, endpoint: str, status_code: int
    ) -> None:
        """
        Record HTTP request count.

        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code
        """
        if not self.enabled or REQUEST_COUNT is None:
            return

        try:
            REQUEST_COUNT.labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).inc()
        except Exception as e:
            self.logger.error("Error recording request count", error=str(e))

    def record_error(self, error_type: str, endpoint: str = "unknown") -> None:
        """
        Record an error occurrence.

        Args:
            error_type: Type of error (e.g., 'AuthenticationError', 'TimeoutError')
            endpoint: API endpoint where error occurred
        """
        if not self.enabled or ERROR_COUNT is None:
            return

        try:
            ERROR_COUNT.labels(error_type=error_type, endpoint=endpoint).inc()
        except Exception as e:
            self.logger.error("Error recording error metric", error=str(e))

    def set_active_connections(self, count: int) -> None:
        """
        Set the number of active WebSocket connections.

        Args:
            count: Current number of active connections
        """
        if not self.enabled or ACTIVE_CONNECTIONS is None:
            return

        try:
            ACTIVE_CONNECTIONS.set(count)
        except Exception as e:
            self.logger.error("Error setting active connections", error=str(e))

    def record_resource_update(self, resource_type: str, update_type: str) -> None:
        """
        Record a resource update event.

        Args:
            resource_type: Type of resource (e.g., 'posts', 'reactions')
            update_type: Type of update (e.g., 'created', 'updated', 'deleted')
        """
        if not self.enabled or RESOURCE_UPDATES is None:
            return

        try:
            RESOURCE_UPDATES.labels(
                resource_type=resource_type, update_type=update_type
            ).inc()
        except Exception as e:
            self.logger.error("Error recording resource update", error=str(e))

    def get_metrics(self) -> Optional[str]:
        """
        Get Prometheus metrics in text format.

        Returns:
            Metrics in Prometheus text format, or None if metrics disabled
        """
        if not self.enabled or PROMETHEUS_REGISTRY is None:
            return None

        try:
            return generate_latest(PROMETHEUS_REGISTRY).decode("utf-8")
        except Exception as e:
            self.logger.error("Error generating metrics", error=str(e))
            return None

    def get_metrics_content_type(self) -> str:
        """
        Get the content type for Prometheus metrics.

        Returns:
            Content type string for Prometheus metrics
        """
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
metrics = MetricsCollector()


def record_request_metrics(
    method: Optional[str] = None, endpoint: Optional[str] = None
):
    """
    Decorator to automatically record request metrics for async functions.

    Args:
        method: HTTP method (if None, will try to extract from function name)
        endpoint: API endpoint (if None, will try to extract from function args)

    Usage:
        @record_request_metrics(method="GET", endpoint="/api/v4/posts")
        async def get_posts():
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            error_type = None

            # Extract method and endpoint if not provided
            actual_method = method or func.__name__.split("_")[0].upper()
            actual_endpoint = endpoint or kwargs.get("endpoint", "unknown")

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error_type = type(e).__name__
                # Try to extract status code from exception
                if hasattr(e, "status_code") and e.status_code:
                    status_code = e.status_code
                else:
                    status_code = 500
                raise
            finally:
                duration = time.time() - start_time

                # Record metrics
                metrics.record_request_latency(
                    actual_method, actual_endpoint, status_code, duration
                )
                metrics.record_request_count(
                    actual_method, actual_endpoint, status_code
                )

                if error_type:
                    metrics.record_error(error_type, actual_endpoint)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            error_type = None

            # Extract method and endpoint if not provided
            actual_method = method or func.__name__.split("_")[0].upper()
            actual_endpoint = endpoint or kwargs.get("endpoint", "unknown")

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_type = type(e).__name__
                if hasattr(e, "status_code") and e.status_code:
                    status_code = e.status_code
                else:
                    status_code = 500
                raise
            finally:
                duration = time.time() - start_time

                # Record metrics
                metrics.record_request_latency(
                    actual_method, actual_endpoint, status_code, duration
                )
                metrics.record_request_count(
                    actual_method, actual_endpoint, status_code
                )

                if error_type:
                    metrics.record_error(error_type, actual_endpoint)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator


@asynccontextmanager
async def measure_async_duration(metric_name: str, labels: Dict[str, str] = None):
    """
    Async context manager to measure duration of code blocks.

    Args:
        metric_name: Name of the metric to record
        labels: Additional labels for the metric

    Usage:
        async with measure_async_duration("api_call", {"endpoint": "/posts"}):
            await some_api_call()
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"{metric_name} completed", duration=duration, **(labels or {}))


@contextmanager
def measure_duration(metric_name: str, labels: Dict[str, str] = None):
    """
    Context manager to measure duration of code blocks.

    Args:
        metric_name: Name of the metric to record
        labels: Additional labels for the metric

    Usage:
        with measure_duration("database_query", {"table": "posts"}):
            execute_query()
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"{metric_name} completed", duration=duration, **(labels or {}))


def increment_counter(metric_name: str, labels: Dict[str, str] = None) -> None:
    """
    Increment a named counter metric.

    Args:
        metric_name: Name of the counter to increment
        labels: Labels to apply to the metric
    """
    logger.info(f"{metric_name} incremented", **(labels or {}))


def set_gauge(
    metric_name: str, value: Union[int, float], labels: Dict[str, str] = None
) -> None:
    """
    Set a gauge metric value.

    Args:
        metric_name: Name of the gauge to set
        value: Value to set
        labels: Labels to apply to the metric
    """
    logger.info(f"{metric_name} set", value=value, **(labels or {}))
