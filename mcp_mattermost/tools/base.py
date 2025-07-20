"""
Base classes and decorators for MCP tools.

This module provides the foundation for creating MCP tool definitions
that call the service layer methods.
"""

import asyncio
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class MCPToolDefinition:
    """
    Definition of an MCP tool with JSON schema and handler function.
    """

    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[..., Any]


class MCPToolRegistry:
    """
    Registry for managing MCP tool definitions.
    """

    def __init__(self):
        self._tools: Dict[str, MCPToolDefinition] = {}
        self.logger = logger.bind(component="tool_registry")

    def register(self, tool: MCPToolDefinition) -> None:
        """Register a tool definition."""
        self._tools[tool.name] = tool
        self.logger.info("Registered tool", name=tool.name)

    def get_tool(self, name: str) -> Optional[MCPToolDefinition]:
        """Get a tool definition by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for MCP protocol."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool by name with arguments."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")

        try:
            self.logger.info("Calling tool", name=name, arguments=arguments)

            # Check if the handler is a coroutine function
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                result = tool.handler(**arguments)

            self.logger.info("Tool call completed", name=name)
            return result

        except Exception as e:
            self.logger.error("Tool call failed", name=name, error=str(e))
            raise


# Global tool registry instance
_registry = MCPToolRegistry()


def mcp_tool(
    name: str, description: str, input_schema: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """
    Decorator to register a function as an MCP tool.

    Args:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for input parameters

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        # If no input schema provided, try to infer from function signature
        schema = input_schema or _generate_schema_from_function(func)

        tool_def = MCPToolDefinition(
            name=name, description=description, input_schema=schema, handler=func
        )

        _registry.register(tool_def)

        return func

    return decorator


def _generate_schema_from_function(func: Callable) -> Dict[str, Any]:
    """
    Generate JSON schema from function signature and type hints.

    This is a simplified implementation - a full version would use
    inspect module to analyze the function signature.
    """
    # For now, return a basic schema
    # TODO: Implement full schema generation from type hints
    return {"type": "object", "properties": {}, "required": []}


def get_registry() -> MCPToolRegistry:
    """Get the global tool registry."""
    return _registry


class BaseMCPTool:
    """
    Base class for MCP tools that need service dependencies.

    This class provides a structured way to create tools that depend
    on service layer instances.
    """

    def __init__(self, services: Dict[str, Any]):
        """
        Initialize with service dependencies.

        Args:
            services: Dictionary of service instances
        """
        self.services = services
        self.logger = logger.bind(component=self.__class__.__name__)

    def _get_service(self, service_name: str) -> Any:
        """Get a service by name."""
        service = self.services.get(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not available")
        return service
