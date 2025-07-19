"""
Teams service for Mattermost API operations.

This module provides high-level async methods for team-related operations
mapped to REST endpoints, returning typed models.
"""

from typing import List, Optional, Dict, Any

from .base import BaseService
from ..models.teams import (
    Team,
    TeamCreate,
    TeamPatch,
    TeamStats,
    TeamExists,
    TeamMember,
    TeamMemberWithTeam,
    TeamUnread,
    TeamInvite,
    TeamSearch,
    TeamMembersGetByIds,
)
from ..models.users import User
from ..models.base import MattermostResponse


class TeamsService(BaseService):
    """
    Service for team-related operations.
    
    Provides high-level async methods for:
    - Creating, updating, and deleting teams
    - Getting team information and lists
    - Team membership management
    - Team search and statistics
    - Team invitations
    """
    
    async def create_team(self, team_data: TeamCreate) -> Team:
        """
        Create a new team.
        
        Args:
            team_data: Team creation data
            
        Returns:
            Created team
        """
        return await self._post(
            "teams",
            Team,
            data=team_data.model_dump(exclude_none=True)
        )
    
    async def get_team(self, team_id: str) -> Team:
        """
        Get a team by ID.
        
        Args:
            team_id: Team ID
            
        Returns:
            Team information
        """
        return await self._get(f"teams/{team_id}", Team)
    
    async def get_team_by_name(self, name: str) -> Team:
        """
        Get a team by name.
        
        Args:
            name: Team name
            
        Returns:
            Team information
        """
        return await self._get(f"teams/name/{name}", Team)
    
    async def update_team(self, team_id: str, team_patch: TeamPatch) -> Team:
        """
        Update a team's information.
        
        Args:
            team_id: Team ID
            team_patch: Team update data
            
        Returns:
            Updated team
        """
        return await self._put(
            f"teams/{team_id}",
            Team,
            data=team_patch.model_dump(exclude_none=True)
        )
    
    async def patch_team(self, team_id: str, team_patch: TeamPatch) -> Team:
        """
        Partially update a team's information.
        
        Args:
            team_id: Team ID
            team_patch: Team patch data
            
        Returns:
            Updated team
        """
        return await self._patch(
            f"teams/{team_id}/patch",
            Team,
            data=team_patch.model_dump(exclude_none=True)
        )
    
    async def delete_team(self, team_id: str, permanent: bool = False) -> MattermostResponse:
        """
        Delete a team.
        
        Args:
            team_id: Team ID
            permanent: Whether to permanently delete (vs soft delete)
            
        Returns:
            Response indicating success
        """
        params = {"permanent": permanent} if permanent else None
        return await self._delete(f"teams/{team_id}", MattermostResponse, params=params)
    
    async def get_teams(
        self,
        page: int = 0,
        per_page: int = 60,
        include_total_count: bool = False,
    ) -> List[Team]:
        """
        Get a list of teams.
        
        Args:
            page: Page number (0-based)
            per_page: Number of teams per page
            include_total_count: Include total count in response headers
            
        Returns:
            List of teams
        """
        params = self._build_query_params(
            page=page,
            per_page=per_page,
            include_total_count=include_total_count,
        )
        
        return await self._get_list("teams", Team, params=params)
    
    async def search_teams(self, search_data: TeamSearch) -> List[Team]:
        """
        Search for teams.
        
        Args:
            search_data: Team search criteria
            
        Returns:
            List of matching teams
        """
        return await self._post(
            "teams/search",
            List[Team],
            data=search_data.model_dump(exclude_none=True)
        )
    
    async def add_team_member(self, team_id: str, user_id: str) -> TeamMember:
        """
        Add a user to a team.
        
        Args:
            team_id: Team ID
            user_id: User ID to add
            
        Returns:
            Team membership information
        """
        data = {"team_id": team_id, "user_id": user_id}
        return await self._post(f"teams/{team_id}/members", TeamMember, data=data)
    
    async def get_team_member(self, team_id: str, user_id: str) -> TeamMember:
        """
        Get team membership for a user.
        
        Args:
            team_id: Team ID
            user_id: User ID
            
        Returns:
            Team membership information
        """
        return await self._get(f"teams/{team_id}/members/{user_id}", TeamMember)
    
    async def remove_team_member(self, team_id: str, user_id: str) -> MattermostResponse:
        """
        Remove a user from a team.
        
        Args:
            team_id: Team ID
            user_id: User ID to remove
            
        Returns:
            Response indicating success
        """
        return await self._delete(f"teams/{team_id}/members/{user_id}", MattermostResponse)
