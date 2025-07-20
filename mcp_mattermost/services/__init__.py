"""
Domain services for Mattermost MCP integration.

This package contains high-level service classes that provide
async methods mapped to REST endpoints and return typed models.
"""

from .channels import ChannelsService
from .files import FilesService
from .posts import PostsService
from .teams import TeamsService
from .users import UsersService

__all__ = [
    "UsersService",
    "TeamsService",
    "ChannelsService",
    "PostsService",
    "FilesService",
]
