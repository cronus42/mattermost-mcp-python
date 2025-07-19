"""
Domain services for Mattermost MCP integration.

This package contains high-level service classes that provide
async methods mapped to REST endpoints and return typed models.
"""

from .users import UsersService
from .teams import TeamsService
from .channels import ChannelsService
from .posts import PostsService
from .files import FilesService

__all__ = [
    "UsersService",
    "TeamsService", 
    "ChannelsService",
    "PostsService",
    "FilesService",
]
