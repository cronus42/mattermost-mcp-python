"""
Channel-related models for Mattermost.

This module contains Pydantic models for channel entities, memberships,
statistics, and channel-related data structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import MattermostBase, MattermostResponse


class ChannelNotifyProps(MattermostBase):
    """Channel notification properties for a member."""

    desktop: Optional[str] = Field(
        default=None, description="Desktop notification level"
    )
    email: Optional[str] = Field(default=None, description="Email notification level")
    push: Optional[str] = Field(default=None, description="Push notification level")
    mark_unread: Optional[str] = Field(
        default=None, description="Mark unread setting"
    )
    ignore_channel_mentions: Optional[str] = Field(
        default=None, description="Whether to ignore channel mentions"
    )


class Channel(MattermostBase):
    """Mattermost channel model."""

    team_id: Optional[str] = Field(default=None, description="ID of the team")
    type: Optional[str] = Field(
        default=None, description="Channel type (O=public, P=private, D=direct, G=group)"
    )
    display_name: Optional[str] = Field(
        default=None, description="Channel display name"
    )
    name: Optional[str] = Field(default=None, description="Channel name")
    header: Optional[str] = Field(default=None, description="Channel header")
    purpose: Optional[str] = Field(default=None, description="Channel purpose")
    last_post_at: Optional[int] = Field(
        default=None, description="Timestamp of last post in the channel"
    )
    total_msg_count: Optional[int] = Field(
        default=None, description="Total message count in the channel"
    )
    extra_update_at: Optional[int] = Field(
        default=None, description="Deprecated field from Mattermost 5.0"
    )
    creator_id: Optional[str] = Field(
        default=None, description="ID of the user who created the channel"
    )

    @property
    def is_private(self) -> bool:
        """Check if the channel is private."""
        return self.type == "P"

    @property
    def is_public(self) -> bool:
        """Check if the channel is public."""
        return self.type == "O"

    @property
    def is_direct_message(self) -> bool:
        """Check if the channel is a direct message."""
        return self.type == "D"

    @property
    def is_group_message(self) -> bool:
        """Check if the channel is a group message."""
        return self.type == "G"


class ChannelCreate(MattermostBase):
    """Channel creation request."""

    team_id: str = Field(description="Team ID")
    name: str = Field(description="Channel name")
    display_name: str = Field(description="Channel display name")
    type: str = Field(description="Channel type (O=public, P=private)")
    purpose: Optional[str] = Field(default=None, description="Channel purpose")
    header: Optional[str] = Field(default=None, description="Channel header")


class ChannelPatch(MattermostBase):
    """Channel update request."""

    name: Optional[str] = None
    display_name: Optional[str] = None
    purpose: Optional[str] = None
    header: Optional[str] = None


class ChannelStats(MattermostResponse):
    """Channel statistics."""

    channel_id: Optional[str] = Field(default=None, description="Channel ID")
    member_count: Optional[int] = Field(
        default=None, description="Number of members in the channel"
    )


class ChannelMember(MattermostBase):
    """Channel membership model."""

    channel_id: Optional[str] = Field(default=None, description="Channel ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    roles: Optional[str] = Field(default=None, description="Member roles")
    last_viewed_at: Optional[int] = Field(
        default=None, description="Last time the channel was viewed"
    )
    msg_count: Optional[int] = Field(
        default=None, description="Message count for this member"
    )
    mention_count: Optional[int] = Field(
        default=None, description="Mention count for this member"
    )
    notify_props: Optional[ChannelNotifyProps] = Field(
        default=None, description="Notification properties"
    )
    last_update_at: Optional[int] = Field(
        default=None, description="Last update timestamp"
    )
    scheme_user: Optional[bool] = Field(
        default=None, description="Whether this member has the default user role"
    )
    scheme_admin: Optional[bool] = Field(
        default=None, description="Whether this member has the default admin role"
    )
    explicit_roles: Optional[str] = Field(
        default=None, description="Explicitly assigned roles"
    )


class ChannelMemberWithTeamData(MattermostBase):
    """Channel member with team data."""

    channel_id: Optional[str] = None
    user_id: Optional[str] = None
    roles: Optional[str] = None
    last_viewed_at: Optional[int] = None
    msg_count: Optional[int] = None
    mention_count: Optional[int] = None
    notify_props: Optional[ChannelNotifyProps] = None
    last_update_at: Optional[int] = None
    scheme_user: Optional[bool] = None
    scheme_admin: Optional[bool] = None
    explicit_roles: Optional[str] = None
    team_display_name: Optional[str] = Field(
        default=None, description="Display name of the team"
    )
    team_name: Optional[str] = Field(default=None, description="Name of the team")
    team_update_at: Optional[int] = Field(
        default=None, description="Team last update timestamp"
    )


class ChannelData(MattermostResponse):
    """Channel data with member information."""

    channel: Optional[Channel] = Field(default=None, description="Channel information")
    member: Optional[ChannelMember] = Field(
        default=None, description="Channel member information"
    )


class ChannelUnread(MattermostResponse):
    """Channel unread messages count."""

    team_id: Optional[str] = Field(default=None, description="Team ID")
    channel_id: Optional[str] = Field(default=None, description="Channel ID")
    msg_count: Optional[int] = Field(
        default=None, description="Number of unread messages"
    )
    mention_count: Optional[int] = Field(
        default=None, description="Number of unread mentions"
    )
    last_viewed_at: Optional[int] = Field(
        default=None, description="Last viewed timestamp"
    )


class ChannelSearch(MattermostBase):
    """Channel search request."""

    term: str = Field(description="Search term")
    not_associated_to_group: Optional[str] = Field(
        default=None, description="Exclude channels associated with this group"
    )
    team_ids: Optional[List[str]] = Field(
        default=None, description="List of team IDs to search in"
    )
    group_constrained: Optional[bool] = Field(
        default=None, description="Filter by group constraints"
    )
    public: Optional[bool] = Field(
        default=None, description="Filter public channels only"
    )
    private: Optional[bool] = Field(
        default=None, description="Filter private channels only"
    )
    deleted: Optional[bool] = Field(
        default=None, description="Include deleted channels"
    )
    page: Optional[int] = Field(default=0, description="Page number")
    per_page: Optional[int] = Field(default=60, description="Results per page")


class ChannelMembersGetByIds(MattermostBase):
    """Request to get channel members by user IDs."""

    user_ids: List[str] = Field(description="List of user IDs")


class ChannelMemberPatch(MattermostBase):
    """Channel member update request."""

    roles: Optional[str] = Field(default=None, description="Updated roles")
    notify_props: Optional[ChannelNotifyProps] = Field(
        default=None, description="Updated notification properties"
    )


class ChannelList(MattermostResponse):
    """List of channels."""

    channels: Optional[List[Channel]] = Field(
        default=None, description="List of channels"
    )
