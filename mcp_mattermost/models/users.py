"""
User-related models for Mattermost.

This module contains Pydantic models for user entities, profiles,
authentication, and user-related data structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import MattermostBase, MattermostResponse


class Timezone(MattermostBase):
    """User timezone information."""

    auto_timezone: Optional[str] = Field(
        default=None, description="Automatically detected timezone"
    )
    manual_timezone: Optional[str] = Field(
        default=None, description="Manually set timezone"
    )
    use_auto_timezone: Optional[bool] = Field(
        default=None, description="Whether to use automatic timezone detection"
    )


class UserNotifyProps(MattermostBase):
    """User notification properties."""

    email: Optional[str] = Field(default=None, description="Email notification setting")
    push: Optional[str] = Field(default=None, description="Push notification setting")
    desktop: Optional[str] = Field(
        default=None, description="Desktop notification setting"
    )
    desktop_sound: Optional[str] = Field(
        default=None, description="Desktop sound notification setting"
    )
    mention_keys: Optional[str] = Field(
        default=None, description="Custom mention keywords"
    )
    channel: Optional[str] = Field(
        default=None, description="Channel-wide notification setting"
    )
    first_name: Optional[str] = Field(
        default=None, description="First name mention notification setting"
    )


class User(MattermostBase):
    """Mattermost user model."""

    username: Optional[str] = Field(default=None, description="User's username")
    first_name: Optional[str] = Field(default=None, description="User's first name")
    last_name: Optional[str] = Field(default=None, description="User's last name")
    nickname: Optional[str] = Field(default=None, description="User's nickname")
    email: Optional[str] = Field(default=None, description="User's email address")
    email_verified: Optional[bool] = Field(
        default=None, description="Whether the email is verified"
    )
    auth_service: Optional[str] = Field(
        default=None, description="Authentication service used"
    )
    roles: Optional[str] = Field(default=None, description="User roles")
    locale: Optional[str] = Field(default=None, description="User's locale")
    notify_props: Optional[UserNotifyProps] = Field(
        default=None, description="Notification properties"
    )
    props: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional user properties"
    )
    last_password_update: Optional[int] = Field(
        default=None, description="Last password update timestamp"
    )
    last_picture_update: Optional[int] = Field(
        default=None, description="Last profile picture update timestamp"
    )
    failed_attempts: Optional[int] = Field(
        default=None, description="Number of failed login attempts"
    )
    mfa_active: Optional[bool] = Field(
        default=None, description="Whether MFA is active"
    )
    timezone: Optional[Timezone] = Field(default=None, description="User timezone")
    terms_of_service_id: Optional[str] = Field(
        default=None, description="ID of accepted terms of service"
    )
    terms_of_service_create_at: Optional[int] = Field(
        default=None, description="When the terms of service were accepted"
    )

    @property
    def display_name(self) -> str:
        """Get the user's display name."""
        if self.nickname:
            return self.nickname
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.username:
            return self.username
        return "Unknown User"

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name


class UserPatch(MattermostBase):
    """Model for updating user properties."""

    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[Timezone] = None
    notify_props: Optional[UserNotifyProps] = None
    props: Optional[Dict[str, Any]] = None


class UsersStats(MattermostResponse):
    """User statistics."""

    total_users_count: Optional[int] = Field(
        default=None, description="Total number of users"
    )


class UserAuthData(MattermostBase):
    """User authentication data."""

    auth_data: Optional[str] = Field(
        default=None, description="Service-specific authentication data"
    )
    auth_service: Optional[str] = Field(
        default=None, description="Authentication service (email, gitlab, ldap, etc.)"
    )
    password: Optional[str] = Field(
        default=None, description="Password for email authentication"
    )


class UserAutocomplete(MattermostResponse):
    """User autocomplete response."""

    users: Optional[List[User]] = Field(
        default=None, description="Main autocomplete results"
    )
    out_of_channel: Optional[List[User]] = Field(
        default=None, description="Users not in the current channel"
    )


class UserAutocompleteInTeam(MattermostResponse):
    """User autocomplete within a team."""

    in_team: Optional[List[User]] = Field(
        default=None, description="Users in the team"
    )


class UserAutocompleteInChannel(MattermostResponse):
    """User autocomplete within a channel."""

    in_channel: Optional[List[User]] = Field(
        default=None, description="Users in the channel"
    )
    out_of_channel: Optional[List[User]] = Field(
        default=None, description="Users not in the channel"
    )


class UserLogin(MattermostBase):
    """User login request."""

    login_id: str = Field(description="Login ID (username, email, or AD/LDAP ID)")
    password: str = Field(description="User password")
    token: Optional[str] = Field(default=None, description="MFA token")
    device_id: Optional[str] = Field(default=None, description="Device identifier")


class UserCreate(MattermostBase):
    """User creation request."""

    username: str = Field(description="Username")
    email: str = Field(description="Email address")
    password: str = Field(description="Password")
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    nickname: Optional[str] = Field(default=None, description="Nickname")
    locale: Optional[str] = Field(default=None, description="User locale")
    props: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional properties"
    )
