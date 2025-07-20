"""
Users service for Mattermost API operations.

This module provides high-level async methods for user-related operations
mapped to REST endpoints, returning typed models.
"""

from typing import Any, Dict, List, Optional

from ..models.base import MattermostResponse
from ..models.users import (
    User,
    UserAuthData,
    UserAutocomplete,
    UserAutocompleteInChannel,
    UserAutocompleteInTeam,
    UserCreate,
    UserLogin,
    UserPatch,
    UsersStats,
)
from .base import BaseService


class UsersService(BaseService):
    """
    Service for user-related operations.

    Provides high-level async methods for:
    - Creating, updating, and deleting users
    - Getting user information and lists
    - User authentication and authorization
    - User search and autocomplete
    - User statistics
    """

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user
        """
        return await self._post(
            "users", User, data=user_data.model_dump(exclude_none=True)
        )

    async def get_user(self, user_id: str) -> User:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User information
        """
        return await self._get(f"users/{user_id}", User)

    async def get_user_by_username(self, username: str) -> User:
        """
        Get a user by username.

        Args:
            username: Username

        Returns:
            User information
        """
        return await self._get(f"users/username/{username}", User)

    async def get_user_by_email(self, email: str) -> User:
        """
        Get a user by email.

        Args:
            email: Email address

        Returns:
            User information
        """
        return await self._get(f"users/email/{email}", User)

    async def update_user(self, user_id: str, user_patch: UserPatch) -> User:
        """
        Update a user's information.

        Args:
            user_id: User ID
            user_patch: User update data

        Returns:
            Updated user
        """
        return await self._put(
            f"users/{user_id}", User, data=user_patch.model_dump(exclude_none=True)
        )

    async def patch_user(self, user_id: str, user_patch: UserPatch) -> User:
        """
        Partially update a user's information.

        Args:
            user_id: User ID
            user_patch: User patch data

        Returns:
            Updated user
        """
        return await self._patch(
            f"users/{user_id}/patch",
            User,
            data=user_patch.model_dump(exclude_none=True),
        )

    async def delete_user(self, user_id: str) -> MattermostResponse:
        """
        Delete a user (deactivate).

        Args:
            user_id: User ID

        Returns:
            Response indicating success
        """
        return await self._delete(f"users/{user_id}", MattermostResponse)

    async def get_users(
        self,
        page: int = 0,
        per_page: int = 60,
        in_team: Optional[str] = None,
        not_in_team: Optional[str] = None,
        in_channel: Optional[str] = None,
        not_in_channel: Optional[str] = None,
        group_constrained: Optional[bool] = None,
        without_team: Optional[bool] = None,
        active: Optional[bool] = None,
        inactive: Optional[bool] = None,
        role: Optional[str] = None,
        sort: Optional[str] = None,
        roles: Optional[List[str]] = None,
        channel_roles: Optional[List[str]] = None,
        team_roles: Optional[List[str]] = None,
    ) -> List[User]:
        """
        Get a list of users.

        Args:
            page: Page number (0-based)
            per_page: Number of users per page
            in_team: Filter users in specific team
            not_in_team: Filter users not in specific team
            in_channel: Filter users in specific channel
            not_in_channel: Filter users not in specific channel
            group_constrained: Filter group-constrained users
            without_team: Filter users without team
            active: Filter active users
            inactive: Filter inactive users
            role: Filter by role
            sort: Sort option
            roles: Filter by system roles
            channel_roles: Filter by channel roles
            team_roles: Filter by team roles

        Returns:
            List of users
        """
        params = self._build_query_params(
            page=page,
            per_page=per_page,
            in_team=in_team,
            not_in_team=not_in_team,
            in_channel=in_channel,
            not_in_channel=not_in_channel,
            group_constrained=group_constrained,
            without_team=without_team,
            active=active,
            inactive=inactive,
            role=role,
            sort=sort,
            roles=",".join(roles) if roles else None,
            channel_roles=",".join(channel_roles) if channel_roles else None,
            team_roles=",".join(team_roles) if team_roles else None,
        )

        return await self._get_list("users", User, params=params)

    async def get_users_by_ids(self, user_ids: List[str]) -> List[User]:
        """
        Get users by a list of user IDs.

        Args:
            user_ids: List of user IDs

        Returns:
            List of users
        """
        return await self._post("users/ids", List[User], data=user_ids)

    async def get_users_by_usernames(self, usernames: List[str]) -> List[User]:
        """
        Get users by a list of usernames.

        Args:
            usernames: List of usernames

        Returns:
            List of users
        """
        return await self._post("users/usernames", List[User], data=usernames)

    async def search_users(
        self,
        term: str,
        team_id: Optional[str] = None,
        not_in_team_id: Optional[str] = None,
        in_channel_id: Optional[str] = None,
        not_in_channel_id: Optional[str] = None,
        group_constrained: Optional[bool] = None,
        allow_inactive: Optional[bool] = None,
        without_team: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[User]:
        """
        Search for users.

        Args:
            term: Search term
            team_id: Filter users in specific team
            not_in_team_id: Filter users not in specific team
            in_channel_id: Filter users in specific channel
            not_in_channel_id: Filter users not in specific channel
            group_constrained: Filter group-constrained users
            allow_inactive: Include inactive users
            without_team: Filter users without team
            limit: Maximum number of results

        Returns:
            List of matching users
        """
        data = self._build_query_params(
            term=term,
            team_id=team_id,
            not_in_team_id=not_in_team_id,
            in_channel_id=in_channel_id,
            not_in_channel_id=not_in_channel_id,
            group_constrained=group_constrained,
            allow_inactive=allow_inactive,
            without_team=without_team,
            limit=limit,
        )

        return await self._post("users/search", List[User], data=data)

    async def autocomplete_users(
        self,
        name: str,
        team_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> UserAutocomplete:
        """
        Autocomplete users by name.

        Args:
            name: Partial name to search
            team_id: Team ID context
            channel_id: Channel ID context
            limit: Maximum number of results

        Returns:
            Autocomplete results
        """
        params = self._build_query_params(
            name=name,
            team_id=team_id,
            channel_id=channel_id,
            limit=limit,
        )

        return await self._get("users/autocomplete", UserAutocomplete, params=params)

    async def get_user_stats(self) -> UsersStats:
        """
        Get user statistics.

        Returns:
            User statistics
        """
        return await self._get("users/stats", UsersStats)

    async def get_me(self) -> User:
        """
        Get the current user.

        Returns:
            Current user information
        """
        return await self._get("users/me", User)

    async def update_me(self, user_patch: UserPatch) -> User:
        """
        Update the current user.

        Args:
            user_patch: User update data

        Returns:
            Updated user
        """
        return await self._put(
            "users/me", User, data=user_patch.model_dump(exclude_none=True)
        )

    async def get_user_image(self, user_id: str) -> bytes:
        """
        Get a user's profile image.

        Args:
            user_id: User ID

        Returns:
            Profile image data
        """
        # Note: This returns raw image data, not a model
        response = await self.client.get(f"users/{user_id}/image")
        return response

    async def set_user_image(
        self, user_id: str, image_data: bytes
    ) -> MattermostResponse:
        """
        Set a user's profile image.

        Args:
            user_id: User ID
            image_data: Image file data

        Returns:
            Response indicating success
        """
        headers = {"Content-Type": "multipart/form-data"}
        return await self._post(
            f"users/{user_id}/image",
            MattermostResponse,
            data=image_data,
            headers=headers,
        )

    async def update_user_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> MattermostResponse:
        """
        Update a user's password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            Response indicating success
        """
        data = {
            "current_password": current_password,
            "new_password": new_password,
        }

        return await self._put(
            f"users/{user_id}/password", MattermostResponse, data=data
        )

    async def send_password_reset_email(self, email: str) -> MattermostResponse:
        """
        Send a password reset email to a user.

        Args:
            email: User's email address

        Returns:
            Response indicating success
        """
        data = {"email": email}
        return await self._post(
            "users/password/reset/send", MattermostResponse, data=data
        )

    async def activate_user(
        self, user_id: str, active: bool = True
    ) -> MattermostResponse:
        """
        Activate or deactivate a user.

        Args:
            user_id: User ID
            active: Whether to activate (True) or deactivate (False)

        Returns:
            Response indicating success
        """
        data = {"active": active}
        return await self._put(f"users/{user_id}/active", MattermostResponse, data=data)
