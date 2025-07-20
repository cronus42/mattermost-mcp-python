"""
Authentication and session-related models for Mattermost.

This module contains Pydantic models for authentication, sessions,
tokens, and security-related data structures.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import Field

from .base import MattermostBase, MattermostResponse

if TYPE_CHECKING:
    from .teams import TeamMember


class Session(MattermostBase):
    """User session model."""

    device_id: Optional[str] = Field(default=None, description="Device identifier")
    expires_at: Optional[int] = Field(
        default=None, description="Session expiration timestamp"
    )
    is_oauth: Optional[bool] = Field(
        default=None, description="Whether this is an OAuth session"
    )
    last_activity_at: Optional[int] = Field(
        default=None, description="Last activity timestamp"
    )
    props: Optional[Dict[str, Any]] = Field(
        default=None, description="Session properties"
    )
    roles: Optional[str] = Field(default=None, description="User roles")
    token: Optional[str] = Field(default=None, description="Session token")
    user_id: Optional[str] = Field(default=None, description="User ID")

    @property
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        if not self.expires_at:
            return False
        import time

        return self.expires_at < int(time.time() * 1000)


class LoginRequest(MattermostBase):
    """User login request."""

    login_id: str = Field(description="Login ID (username, email, or LDAP ID)")
    password: str = Field(description="User password")
    token: Optional[str] = Field(default=None, description="MFA token")
    device_id: Optional[str] = Field(default=None, description="Device ID")
    ldap_only: Optional[bool] = Field(
        default=None, description="Use LDAP authentication only"
    )


class LoginResponse(MattermostResponse):
    """Login response containing user and session info."""

    # The response body contains the User model
    # Headers contain the session token


class LogoutRequest(MattermostBase):
    """Logout request."""

    # Usually just uses the session token in headers


class AccessToken(MattermostBase):
    """Personal access token model."""

    user_id: Optional[str] = Field(
        default=None, description="ID of the user who owns this token"
    )
    description: Optional[str] = Field(
        default=None, description="Description of the token"
    )
    token: Optional[str] = Field(default=None, description="The actual token value")
    is_active: Optional[bool] = Field(
        default=None, description="Whether the token is active"
    )


class AccessTokenRequest(MattermostBase):
    """Request to create a personal access token."""

    description: str = Field(description="Token description")


class RevokeSessionRequest(MattermostBase):
    """Request to revoke a session."""

    session_id: str = Field(description="Session ID to revoke")


class RevokeAllSessionsRequest(MattermostBase):
    """Request to revoke all sessions for a user."""

    # Usually just requires authentication


class PasswordResetRequest(MattermostBase):
    """Password reset request."""

    email: str = Field(description="Email address for password reset")


class PasswordResetComplete(MattermostBase):
    """Complete password reset."""

    code: str = Field(description="Reset code from email")
    new_password: str = Field(description="New password")


class ChangePasswordRequest(MattermostBase):
    """Change password request."""

    current_password: str = Field(description="Current password")
    new_password: str = Field(description="New password")


class MfaSetupRequest(MattermostBase):
    """MFA setup request."""

    code: str = Field(description="MFA verification code")
    secret: str = Field(description="MFA secret")


class MfaUpdateRequest(MattermostBase):
    """MFA update request."""

    activate: bool = Field(description="Whether to activate or deactivate MFA")
    code: Optional[str] = Field(default=None, description="MFA code for activation")


class OAuthApp(MattermostBase):
    """OAuth application model."""

    client_id: Optional[str] = Field(default=None, description="OAuth client ID")
    client_secret: Optional[str] = Field(
        default=None, description="OAuth client secret"
    )
    name: Optional[str] = Field(default=None, description="Application name")
    description: Optional[str] = Field(
        default=None, description="Application description"
    )
    homepage: Optional[str] = Field(default=None, description="Application homepage")
    callback_urls: Optional[List[str]] = Field(
        default=None, description="OAuth callback URLs"
    )
    trusted: Optional[bool] = Field(
        default=None, description="Whether the app is trusted"
    )
    icon_url: Optional[str] = Field(default=None, description="Application icon URL")


class OAuthAppRequest(MattermostBase):
    """OAuth application creation/update request."""

    name: str = Field(description="Application name")
    description: str = Field(description="Application description")
    homepage: str = Field(description="Application homepage")
    callback_urls: List[str] = Field(description="OAuth callback URLs")
    trusted: Optional[bool] = Field(
        default=False, description="Whether the app is trusted"
    )
    icon_url: Optional[str] = Field(default=None, description="Application icon URL")


class OAuthAuthorizeRequest(MattermostBase):
    """OAuth authorization request."""

    client_id: str = Field(description="OAuth client ID")
    response_type: str = Field(description="OAuth response type")
    redirect_uri: str = Field(description="Redirect URI")
    scope: Optional[str] = Field(default=None, description="OAuth scope")
    state: Optional[str] = Field(default=None, description="OAuth state parameter")


class OAuthTokenRequest(MattermostBase):
    """OAuth token exchange request."""

    grant_type: str = Field(description="OAuth grant type")
    client_id: str = Field(description="OAuth client ID")
    client_secret: str = Field(description="OAuth client secret")
    redirect_uri: str = Field(description="Redirect URI")
    code: Optional[str] = Field(default=None, description="Authorization code")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token")


class OAuthTokenResponse(MattermostResponse):
    """OAuth token response."""

    access_token: Optional[str] = Field(default=None, description="Access token")
    token_type: Optional[str] = Field(default=None, description="Token type")
    expires_in: Optional[int] = Field(
        default=None, description="Token expiration in seconds"
    )
    refresh_token: Optional[str] = Field(default=None, description="Refresh token")
    scope: Optional[str] = Field(default=None, description="Token scope")


class SamlRequest(MattermostBase):
    """SAML authentication request."""

    # Usually handled via redirects
    relay_state: Optional[str] = Field(default=None, description="SAML relay state")


class LdapSyncRequest(MattermostBase):
    """LDAP synchronization request."""

    # Usually just triggers a sync operation
    include_removed_members: Optional[bool] = Field(
        default=None, description="Whether to include removed members in sync"
    )


class SamlCertificateRequest(MattermostBase):
    """SAML certificate upload request."""

    certificate: str = Field(description="PEM encoded certificate")


class AuthTestRequest(MattermostBase):
    """Authentication test request."""

    # Used for testing authentication endpoints
