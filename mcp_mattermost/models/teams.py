"""
Team-related models for Mattermost.

This module contains Pydantic models for team entities, memberships,
statistics, and team-related data structures.
"""

from typing import Dict, List, Optional

from pydantic import Field

from .base import MattermostBase, MattermostResponse


class Team(MattermostBase):
    """Mattermost team model."""

    display_name: Optional[str] = Field(
        default=None, description="Team's display name"
    )
    name: Optional[str] = Field(default=None, description="Team's unique name")
    description: Optional[str] = Field(default=None, description="Team description")
    email: Optional[str] = Field(default=None, description="Team email")
    type: Optional[str] = Field(default=None, description="Team type (O=open, I=invite)")
    allowed_domains: Optional[str] = Field(
        default=None, description="Comma-separated list of allowed domains"
    )
    invite_id: Optional[str] = Field(default=None, description="Team invite ID")
    allow_open_invite: Optional[bool] = Field(
        default=None, description="Whether the team allows open invitations"
    )


class TeamCreate(MattermostBase):
    """Team creation request."""

    name: str = Field(description="Team name")
    display_name: str = Field(description="Team display name")
    type: str = Field(description="Team type (O=open, I=invite)")
    description: Optional[str] = Field(default=None, description="Team description")
    allowed_domains: Optional[str] = Field(
        default=None, description="Comma-separated list of allowed domains"
    )
    allow_open_invite: Optional[bool] = Field(
        default=None, description="Whether to allow open invitations"
    )


class TeamPatch(MattermostBase):
    """Team update request."""

    display_name: Optional[str] = None
    description: Optional[str] = None
    allowed_domains: Optional[str] = None
    allow_open_invite: Optional[bool] = None


class TeamStats(MattermostResponse):
    """Team statistics."""

    team_id: Optional[str] = Field(default=None, description="Team ID")
    total_member_count: Optional[int] = Field(
        default=None, description="Total number of members"
    )
    active_member_count: Optional[int] = Field(
        default=None, description="Number of active members"
    )


class TeamExists(MattermostResponse):
    """Team existence check response."""

    exists: Optional[bool] = Field(
        default=None, description="Whether the team exists"
    )


class TeamMember(MattermostBase):
    """Team membership model."""

    team_id: Optional[str] = Field(
        default=None, description="ID of the team this member belongs to"
    )
    user_id: Optional[str] = Field(
        default=None, description="ID of the user this member relates to"
    )
    roles: Optional[str] = Field(
        default=None, description="Space-separated list of role names"
    )
    delete_at: Optional[int] = Field(
        default=None, description="When this team member was deleted"
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


class TeamMemberWithTeam(MattermostBase):
    """Team member with team information."""

    team_id: Optional[str] = None
    user_id: Optional[str] = None
    roles: Optional[str] = None
    delete_at: Optional[int] = None
    scheme_user: Optional[bool] = None
    scheme_admin: Optional[bool] = None
    explicit_roles: Optional[str] = None
    team: Optional[Team] = Field(default=None, description="Team information")


class TeamUnread(MattermostResponse):
    """Team unread messages count."""

    team_id: Optional[str] = Field(default=None, description="Team ID")
    msg_count: Optional[int] = Field(
        default=None, description="Number of unread messages"
    )
    mention_count: Optional[int] = Field(
        default=None, description="Number of unread mentions"
    )


class TeamInvite(MattermostBase):
    """Team invitation model."""

    email: str = Field(description="Email address to invite")
    team_id: str = Field(description="Team ID")


class TeamMap(MattermostResponse):
    """A mapping of team IDs to teams."""

    # This is a dynamic dictionary structure
    # Key is team_id, value is Team object
    # We'll use model_validate to handle this dynamically


class TeamSearch(MattermostBase):
    """Team search request."""

    term: str = Field(description="Search term")
    page: Optional[int] = Field(default=0, description="Page number")
    per_page: Optional[int] = Field(default=60, description="Results per page")
    allow_open_invite: Optional[bool] = Field(
        default=None, description="Filter by open invite policy"
    )
    group_constrained: Optional[bool] = Field(
        default=None, description="Filter by group constraints"
    )


class TeamMembersGetByIds(MattermostBase):
    """Request to get team members by user IDs."""

    user_ids: List[str] = Field(description="List of user IDs")
