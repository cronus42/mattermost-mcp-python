"""
Webhook and integration-related models for Mattermost.

This module contains Pydantic models for webhooks, slash commands,
and other integration-related data structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import MattermostBase, MattermostResponse
from .posts import SlackAttachment


class IncomingWebhook(MattermostBase):
    """Incoming webhook model."""

    channel_id: Optional[str] = Field(
        default=None, description="ID of the channel that receives webhook payloads"
    )
    description: Optional[str] = Field(
        default=None, description="Description of the webhook"
    )
    display_name: Optional[str] = Field(
        default=None, description="Display name of the webhook"
    )
    team_id: Optional[str] = Field(default=None, description="ID of the team")
    user_id: Optional[str] = Field(
        default=None, description="ID of the user who created the webhook"
    )


class IncomingWebhookRequest(MattermostBase):
    """Request to create an incoming webhook."""

    channel_id: str = Field(description="Channel ID")
    description: Optional[str] = Field(default=None, description="Webhook description")
    display_name: Optional[str] = Field(
        default=None, description="Webhook display name"
    )


class OutgoingWebhook(MattermostBase):
    """Outgoing webhook model."""

    creator_id: Optional[str] = Field(
        default=None, description="ID of the user who created the webhook"
    )
    team_id: Optional[str] = Field(
        default=None, description="ID of the team the webhook watches"
    )
    channel_id: Optional[str] = Field(
        default=None, description="ID of the channel the webhook watches"
    )
    description: Optional[str] = Field(
        default=None, description="Description of the webhook"
    )
    display_name: Optional[str] = Field(
        default=None, description="Display name of the webhook"
    )
    trigger_words: Optional[List[str]] = Field(
        default=None, description="Words that trigger the webhook"
    )
    trigger_when: Optional[int] = Field(
        default=None,
        description="When to trigger: 0=anywhere in message, 1=start of message",
    )
    callback_urls: Optional[List[str]] = Field(
        default=None, description="URLs to POST the payload to"
    )
    content_type: Optional[str] = Field(
        default="application/x-www-form-urlencoded",
        description="Content type for the payload",
    )


class OutgoingWebhookRequest(MattermostBase):
    """Request to create an outgoing webhook."""

    team_id: str = Field(description="Team ID")
    channel_id: str = Field(description="Channel ID")
    display_name: str = Field(description="Webhook display name")
    description: Optional[str] = Field(default=None, description="Webhook description")
    trigger_words: List[str] = Field(description="Trigger words")
    trigger_when: Optional[int] = Field(
        default=0, description="When to trigger the webhook"
    )
    callback_urls: List[str] = Field(description="Callback URLs")
    content_type: Optional[str] = Field(
        default="application/x-www-form-urlencoded", description="Content type"
    )


class Command(MattermostBase):
    """Slash command model."""

    token: Optional[str] = Field(
        default=None, description="Token for verifying the payload source"
    )
    creator_id: Optional[str] = Field(
        default=None, description="ID of the user who created the command"
    )
    team_id: Optional[str] = Field(
        default=None, description="ID of the team the command is configured for"
    )
    trigger: Optional[str] = Field(
        default=None, description="String that triggers the command"
    )
    method: Optional[str] = Field(
        default=None, description="HTTP method (GET or POST)"
    )
    username: Optional[str] = Field(
        default=None, description="Username for the response post"
    )
    icon_url: Optional[str] = Field(
        default=None, description="Icon URL for the response post"
    )
    auto_complete: Optional[bool] = Field(
        default=None, description="Whether to use autocomplete"
    )
    auto_complete_desc: Optional[str] = Field(
        default=None, description="Autocomplete description"
    )
    auto_complete_hint: Optional[str] = Field(
        default=None, description="Autocomplete hint"
    )
    display_name: Optional[str] = Field(
        default=None, description="Display name for the command"
    )
    description: Optional[str] = Field(
        default=None, description="Description of the command"
    )
    url: Optional[str] = Field(default=None, description="URL that is triggered")


class CommandRequest(MattermostBase):
    """Request to create a slash command."""

    team_id: str = Field(description="Team ID")
    trigger: str = Field(description="Command trigger")
    url: str = Field(description="Command URL")
    method: str = Field(description="HTTP method")
    username: Optional[str] = Field(default=None, description="Response username")
    icon_url: Optional[str] = Field(default=None, description="Response icon URL")
    auto_complete: Optional[bool] = Field(
        default=False, description="Enable autocomplete"
    )
    auto_complete_desc: Optional[str] = Field(
        default=None, description="Autocomplete description"
    )
    auto_complete_hint: Optional[str] = Field(
        default=None, description="Autocomplete hint"
    )
    display_name: Optional[str] = Field(
        default=None, description="Command display name"
    )
    description: Optional[str] = Field(default=None, description="Command description")


class CommandResponse(MattermostResponse):
    """Response from a slash command."""

    ResponseType: Optional[str] = Field(
        default=None, description="Response type (in_channel or ephemeral)"
    )
    Text: Optional[str] = Field(default=None, description="Response text")
    Username: Optional[str] = Field(default=None, description="Response username")
    IconURL: Optional[str] = Field(default=None, description="Response icon URL")
    GotoLocation: Optional[str] = Field(
        default=None, description="URL to navigate to"
    )
    Attachments: Optional[List[SlackAttachment]] = Field(
        default=None, description="Message attachments"
    )


class Bot(MattermostBase):
    """Bot user model."""

    user_id: Optional[str] = Field(default=None, description="Bot user ID")
    username: Optional[str] = Field(default=None, description="Bot username")
    display_name: Optional[str] = Field(default=None, description="Bot display name")
    description: Optional[str] = Field(default=None, description="Bot description")
    owner_id: Optional[str] = Field(
        default=None, description="ID of the user who owns the bot"
    )


class BotRequest(MattermostBase):
    """Request to create a bot."""

    username: str = Field(description="Bot username")
    display_name: Optional[str] = Field(default=None, description="Bot display name")
    description: Optional[str] = Field(default=None, description="Bot description")


class BotPatch(MattermostBase):
    """Request to update a bot."""

    username: Optional[str] = Field(default=None, description="Updated username")
    display_name: Optional[str] = Field(
        default=None, description="Updated display name"
    )
    description: Optional[str] = Field(
        default=None, description="Updated description"
    )


class WebhookPayload(MattermostBase):
    """Generic webhook payload."""

    text: Optional[str] = Field(default=None, description="Message text")
    username: Optional[str] = Field(default=None, description="Override username")
    icon_url: Optional[str] = Field(default=None, description="Override icon URL")
    icon_emoji: Optional[str] = Field(default=None, description="Override icon emoji")
    channel: Optional[str] = Field(
        default=None, description="Override channel (name or ID)"
    )
    attachments: Optional[List[SlackAttachment]] = Field(
        default=None, description="Message attachments"
    )
    type: Optional[str] = Field(default=None, description="Message type")
    props: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional properties"
    )


class IntegrationAction(MattermostBase):
    """Integration action model."""

    id: Optional[str] = Field(default=None, description="Action ID")
    name: Optional[str] = Field(default=None, description="Action name")
    integration: Optional[Dict[str, Any]] = Field(
        default=None, description="Integration details"
    )


class DialogRequest(MattermostBase):
    """Interactive dialog request."""

    trigger_id: str = Field(description="Trigger ID from the original interaction")
    url: str = Field(description="App's request URL")
    dialog: Dict[str, Any] = Field(description="Dialog definition")


class DialogResponse(MattermostResponse):
    """Response to a dialog submission."""

    errors: Optional[Dict[str, str]] = Field(
        default=None, description="Validation errors"
    )


class MessageAttachment(MattermostBase):
    """Message attachment for interactive messages."""

    # Inherits from SlackAttachment but adds interactive elements
    actions: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Interactive actions"
    )


class PostActionIntegrationRequest(MattermostBase):
    """Post action integration request."""

    user_id: Optional[str] = Field(default=None, description="User ID")
    user_name: Optional[str] = Field(default=None, description="Username")
    channel_id: Optional[str] = Field(default=None, description="Channel ID")
    channel_name: Optional[str] = Field(default=None, description="Channel name")
    team_id: Optional[str] = Field(default=None, description="Team ID")
    team_domain: Optional[str] = Field(default=None, description="Team domain")
    post_id: Optional[str] = Field(default=None, description="Post ID")
    trigger_id: Optional[str] = Field(default=None, description="Trigger ID")
    type: Optional[str] = Field(default=None, description="Action type")
    data_source: Optional[str] = Field(default=None, description="Data source")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context"
    )


class PostActionIntegrationResponse(MattermostResponse):
    """Response to a post action integration."""

    update: Optional[Dict[str, Any]] = Field(
        default=None, description="Post update data"
    )
    ephemeral_text: Optional[str] = Field(
        default=None, description="Ephemeral response text"
    )
