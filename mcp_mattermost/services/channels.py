"""
Channels service for Mattermost API operations.

This module provides high-level async methods for channel-related operations
mapped to REST endpoints, returning typed models.
"""

from typing import Any, Dict, List, Optional

from ..models.base import MattermostResponse
from ..models.channels import (
    Channel,
    ChannelCreate,
    ChannelData,
    ChannelList,
    ChannelMember,
    ChannelMemberPatch,
    ChannelMembersGetByIds,
    ChannelMemberWithTeamData,
    ChannelPatch,
    ChannelSearch,
    ChannelStats,
    ChannelUnread,
)
from .base import BaseService


class ChannelsService(BaseService):
    """
    Service for channel-related operations.

    Provides high-level async methods for:
    - Creating, updating, and deleting channels
    - Getting channel information and lists
    - Channel membership management
    - Channel search and statistics
    """

    async def create_channel(self, channel_data: ChannelCreate) -> Channel:
        """
        Create a new channel.

        Args:
            channel_data: Channel creation data

        Returns:
            Created channel
        """
        return await self._post(
            "channels", Channel, data=channel_data.model_dump(exclude_none=True)
        )

    async def get_channel(self, channel_id: str) -> Channel:
        """
        Get a channel by ID.

        Args:
            channel_id: Channel ID

        Returns:
            Channel information
        """
        return await self._get(f"channels/{channel_id}", Channel)

    async def get_channel_by_name(self, team_id: str, channel_name: str) -> Channel:
        """
        Get a channel by name within a team.

        Args:
            team_id: Team ID
            channel_name: Channel name

        Returns:
            Channel information
        """
        return await self._get(f"teams/{team_id}/channels/name/{channel_name}", Channel)

    async def update_channel(
        self, channel_id: str, channel_patch: ChannelPatch
    ) -> Channel:
        """
        Update a channel's information.

        Args:
            channel_id: Channel ID
            channel_patch: Channel update data

        Returns:
            Updated channel
        """
        return await self._put(
            f"channels/{channel_id}",
            Channel,
            data=channel_patch.model_dump(exclude_none=True),
        )

    async def patch_channel(
        self, channel_id: str, channel_patch: ChannelPatch
    ) -> Channel:
        """
        Partially update a channel's information.

        Args:
            channel_id: Channel ID
            channel_patch: Channel patch data

        Returns:
            Updated channel
        """
        return await self._patch(
            f"channels/{channel_id}/patch",
            Channel,
            data=channel_patch.model_dump(exclude_none=True),
        )

    async def delete_channel(self, channel_id: str) -> MattermostResponse:
        """
        Delete a channel.

        Args:
            channel_id: Channel ID

        Returns:
            Response indicating success
        """
        return await self._delete(f"channels/{channel_id}", MattermostResponse)

    async def get_channels_for_team(
        self,
        team_id: str,
        page: int = 0,
        per_page: int = 60,
        include_deleted: bool = False,
    ) -> List[Channel]:
        """
        Get channels for a team.

        Args:
            team_id: Team ID
            page: Page number (0-based)
            per_page: Number of channels per page
            include_deleted: Include deleted channels

        Returns:
            List of channels
        """
        params = self._build_query_params(
            page=page,
            per_page=per_page,
            include_deleted=include_deleted,
        )

        return await self._get_list(f"teams/{team_id}/channels", Channel, params=params)

    async def get_public_channels_for_team(
        self,
        team_id: str,
        page: int = 0,
        per_page: int = 60,
    ) -> List[Channel]:
        """
        Get public channels for a team.

        Args:
            team_id: Team ID
            page: Page number (0-based)
            per_page: Number of channels per page

        Returns:
            List of public channels
        """
        params = self._build_query_params(page=page, per_page=per_page)
        return await self._get_list(
            f"teams/{team_id}/channels/public", Channel, params=params
        )

    async def search_channels(
        self, team_id: str, search_data: ChannelSearch
    ) -> List[Channel]:
        """
        Search for channels in a team.

        Args:
            team_id: Team ID
            search_data: Channel search criteria

        Returns:
            List of matching channels
        """
        return await self._post(
            f"teams/{team_id}/channels/search",
            List[Channel],
            data=search_data.model_dump(exclude_none=True),
        )

    async def get_channel_stats(self, channel_id: str) -> ChannelStats:
        """
        Get channel statistics.

        Args:
            channel_id: Channel ID

        Returns:
            Channel statistics
        """
        return await self._get(f"channels/{channel_id}/stats", ChannelStats)

    # Channel Membership Methods

    async def add_channel_member(self, channel_id: str, user_id: str) -> ChannelMember:
        """
        Add a user to a channel.

        Args:
            channel_id: Channel ID
            user_id: User ID to add

        Returns:
            Channel membership information
        """
        data = {"user_id": user_id}
        return await self._post(
            f"channels/{channel_id}/members", ChannelMember, data=data
        )

    async def get_channel_member(self, channel_id: str, user_id: str) -> ChannelMember:
        """
        Get channel membership for a user.

        Args:
            channel_id: Channel ID
            user_id: User ID

        Returns:
            Channel membership information
        """
        return await self._get(
            f"channels/{channel_id}/members/{user_id}", ChannelMember
        )

    async def get_channel_members(
        self,
        channel_id: str,
        page: int = 0,
        per_page: int = 60,
    ) -> List[ChannelMember]:
        """
        Get channel members.

        Args:
            channel_id: Channel ID
            page: Page number (0-based)
            per_page: Number of members per page

        Returns:
            List of channel members
        """
        params = self._build_query_params(page=page, per_page=per_page)
        return await self._get_list(
            f"channels/{channel_id}/members", ChannelMember, params=params
        )

    async def remove_channel_member(
        self, channel_id: str, user_id: str
    ) -> MattermostResponse:
        """
        Remove a user from a channel.

        Args:
            channel_id: Channel ID
            user_id: User ID to remove

        Returns:
            Response indicating success
        """
        return await self._delete(
            f"channels/{channel_id}/members/{user_id}", MattermostResponse
        )

    async def update_channel_member_roles(
        self,
        channel_id: str,
        user_id: str,
        roles: List[str],
    ) -> MattermostResponse:
        """
        Update channel member roles.

        Args:
            channel_id: Channel ID
            user_id: User ID
            roles: List of role names

        Returns:
            Response indicating success
        """
        data = {"roles": " ".join(roles)}
        return await self._put(
            f"channels/{channel_id}/members/{user_id}/roles",
            MattermostResponse,
            data=data,
        )

    async def get_channel_unread(self, user_id: str, channel_id: str) -> ChannelUnread:
        """
        Get unread message count for a channel.

        Args:
            user_id: User ID
            channel_id: Channel ID

        Returns:
            Channel unread count
        """
        return await self._get(
            f"users/{user_id}/channels/{channel_id}/unread", ChannelUnread
        )
