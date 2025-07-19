"""
Post-related models for Mattermost.

This module contains Pydantic models for post entities, metadata,
reactions, and post-related data structures.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import Field

from .base import MattermostBase, MattermostResponse

if TYPE_CHECKING:
    # Forward references to avoid circular imports
    pass


class PostMetadata(MattermostBase):
    """Additional metadata for displaying a post."""

    embeds: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Embedded content like OpenGraph previews"
    )
    emojis: Optional[List["Emoji"]] = Field(
        default=None, description="Custom emojis used in the post"
    )
    files: Optional[List["FileInfo"]] = Field(
        default=None, description="File attachments"
    )
    images: Optional[Dict[str, Dict[str, int]]] = Field(
        default=None, description="External image dimensions"
    )
    reactions: Optional[List["Reaction"]] = Field(
        default=None, description="Post reactions"
    )


class Post(MattermostBase):
    """Mattermost post model."""

    user_id: Optional[str] = Field(default=None, description="ID of the post author")
    channel_id: Optional[str] = Field(
        default=None, description="ID of the channel containing the post"
    )
    root_id: Optional[str] = Field(
        default=None, description="ID of the root post (for replies)"
    )
    parent_id: Optional[str] = Field(
        default=None, description="ID of the parent post (deprecated)"
    )
    original_id: Optional[str] = Field(
        default=None, description="ID of the original post (for edits)"
    )
    message: Optional[str] = Field(default=None, description="Post message content")
    type: Optional[str] = Field(default=None, description="Post type")
    props: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional post properties"
    )
    hashtag: Optional[str] = Field(default=None, description="Post hashtags")
    filenames: Optional[List[str]] = Field(
        default=None, description="Deprecated file attachments field"
    )
    file_ids: Optional[List[str]] = Field(
        default=None, description="IDs of attached files"
    )
    pending_post_id: Optional[str] = Field(
        default=None, description="Temporary ID for pending posts"
    )
    edit_at: Optional[int] = Field(
        default=None, description="Timestamp when the post was last edited"
    )
    metadata: Optional[PostMetadata] = Field(
        default=None, description="Additional post metadata"
    )

    @property
    def is_reply(self) -> bool:
        """Check if this post is a reply to another post."""
        return self.root_id is not None

    @property
    def is_edited(self) -> bool:
        """Check if this post has been edited."""
        return self.edit_at is not None and self.edit_at > 0

    @property
    def has_attachments(self) -> bool:
        """Check if this post has file attachments."""
        return bool(self.file_ids)


class PostCreate(MattermostBase):
    """Post creation request."""

    channel_id: str = Field(description="Channel ID")
    message: str = Field(description="Post message")
    root_id: Optional[str] = Field(default=None, description="Root post ID for replies")
    file_ids: Optional[List[str]] = Field(
        default=None, description="List of file IDs to attach"
    )
    props: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional properties"
    )
    type: Optional[str] = Field(default=None, description="Post type")


class PostPatch(MattermostBase):
    """Post update request."""

    message: Optional[str] = Field(default=None, description="Updated message")
    file_ids: Optional[List[str]] = Field(
        default=None, description="Updated file attachments"
    )
    props: Optional[Dict[str, Any]] = Field(
        default=None, description="Updated properties"
    )
    has_reactions: Optional[bool] = Field(
        default=None, description="Whether the post has reactions"
    )


class PostList(MattermostResponse):
    """List of posts with ordering information."""

    order: Optional[List[str]] = Field(
        default=None, description="Post IDs in display order"
    )
    posts: Optional[Dict[str, Post]] = Field(
        default=None, description="Posts mapped by ID"
    )
    next_post_id: Optional[str] = Field(
        default=None, description="ID of the next post"
    )
    prev_post_id: Optional[str] = Field(
        default=None, description="ID of the previous post"
    )


class PostListWithSearchMatches(MattermostResponse):
    """Post list with search match information."""

    order: Optional[List[str]] = Field(
        default=None, description="Post IDs in display order"
    )
    posts: Optional[Dict[str, Post]] = Field(
        default=None, description="Posts mapped by ID"
    )
    matches: Optional[Dict[str, List[str]]] = Field(
        default=None, description="Search matches per post"
    )


class PostSearch(MattermostBase):
    """Post search request."""

    terms: str = Field(description="Search terms")
    is_or_search: Optional[bool] = Field(
        default=None, description="Whether to use OR logic between terms"
    )
    time_zone_offset: Optional[int] = Field(
        default=None, description="Timezone offset in seconds"
    )
    include_deleted_channels: Optional[bool] = Field(
        default=None, description="Include posts from deleted channels"
    )
    page: Optional[int] = Field(default=0, description="Page number")
    per_page: Optional[int] = Field(default=60, description="Posts per page")


class PostAction(MattermostBase):
    """Post action (e.g., pin, unpin, flag)."""

    post_id: str = Field(description="Post ID")
    action: str = Field(description="Action to perform")


class Reaction(MattermostBase):
    """Post reaction model."""

    user_id: Optional[str] = Field(
        default=None, description="ID of the user who made the reaction"
    )
    post_id: Optional[str] = Field(
        default=None, description="ID of the post that was reacted to"
    )
    emoji_name: Optional[str] = Field(
        default=None, description="Name of the emoji used"
    )
    create_at: Optional[int] = Field(
        default=None, description="When the reaction was created"
    )


class FileInfo(MattermostBase):
    """File attachment information."""

    user_id: Optional[str] = Field(
        default=None, description="ID of the user who uploaded the file"
    )
    post_id: Optional[str] = Field(
        default=None, description="ID of the post the file is attached to"
    )
    name: Optional[str] = Field(default=None, description="Original filename")
    extension: Optional[str] = Field(default=None, description="File extension")
    size: Optional[int] = Field(default=None, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    width: Optional[int] = Field(
        default=None, description="Image width (for images)"
    )
    height: Optional[int] = Field(
        default=None, description="Image height (for images)"
    )
    has_preview_image: Optional[bool] = Field(
        default=None, description="Whether a preview image exists"
    )


class Emoji(MattermostBase):
    """Custom emoji model."""

    creator_id: Optional[str] = Field(
        default=None, description="ID of the user who created the emoji"
    )
    name: Optional[str] = Field(default=None, description="Emoji name")


class SlackAttachmentField(MattermostBase):
    """Slack-compatible attachment field."""

    Title: Optional[str] = Field(default=None, description="Field title")
    Value: Optional[str] = Field(default=None, description="Field value")
    Short: Optional[bool] = Field(default=None, description="Whether field is short")


class SlackAttachment(MattermostBase):
    """Slack-compatible message attachment."""

    Id: Optional[str] = Field(default=None, description="Attachment ID")
    Fallback: Optional[str] = Field(default=None, description="Fallback text")
    Color: Optional[str] = Field(default=None, description="Sidebar color")
    Pretext: Optional[str] = Field(default=None, description="Pretext")
    AuthorName: Optional[str] = Field(default=None, description="Author name")
    AuthorLink: Optional[str] = Field(default=None, description="Author link")
    AuthorIcon: Optional[str] = Field(default=None, description="Author icon")
    Title: Optional[str] = Field(default=None, description="Title")
    TitleLink: Optional[str] = Field(default=None, description="Title link")
    Text: Optional[str] = Field(default=None, description="Main text")
    Fields: Optional[List[SlackAttachmentField]] = Field(
        default=None, description="Attachment fields"
    )
    ImageURL: Optional[str] = Field(default=None, description="Image URL")
    ThumbURL: Optional[str] = Field(default=None, description="Thumbnail URL")
    Footer: Optional[str] = Field(default=None, description="Footer")
    FooterIcon: Optional[str] = Field(default=None, description="Footer icon")
    Timestamp: Optional[str] = Field(default=None, description="Timestamp")


class OpenGraphImage(MattermostBase):
    """OpenGraph image metadata."""

    url: Optional[str] = Field(default=None, description="Image URL")
    secure_url: Optional[str] = Field(default=None, description="Secure image URL")
    type: Optional[str] = Field(default=None, description="Image MIME type")
    width: Optional[int] = Field(default=None, description="Image width")
    height: Optional[int] = Field(default=None, description="Image height")


class OpenGraphVideo(MattermostBase):
    """OpenGraph video metadata."""

    url: Optional[str] = Field(default=None, description="Video URL")
    secure_url: Optional[str] = Field(default=None, description="Secure video URL")
    type: Optional[str] = Field(default=None, description="Video MIME type")
    width: Optional[int] = Field(default=None, description="Video width")
    height: Optional[int] = Field(default=None, description="Video height")


class OpenGraphAudio(MattermostBase):
    """OpenGraph audio metadata."""

    url: Optional[str] = Field(default=None, description="Audio URL")
    secure_url: Optional[str] = Field(default=None, description="Secure audio URL")
    type: Optional[str] = Field(default=None, description="Audio MIME type")


class OpenGraph(MattermostBase):
    """OpenGraph metadata for web content."""

    type: Optional[str] = Field(default=None, description="OpenGraph type")
    url: Optional[str] = Field(default=None, description="Canonical URL")
    title: Optional[str] = Field(default=None, description="Page title")
    description: Optional[str] = Field(default=None, description="Page description")
    determiner: Optional[str] = Field(default=None, description="Title determiner")
    site_name: Optional[str] = Field(default=None, description="Site name")
    locale: Optional[str] = Field(default=None, description="Content locale")
    locales_alternate: Optional[List[str]] = Field(
        default=None, description="Alternate locales"
    )
    images: Optional[List[OpenGraphImage]] = Field(
        default=None, description="OpenGraph images"
    )
    videos: Optional[List[OpenGraphVideo]] = Field(
        default=None, description="OpenGraph videos"
    )
    audios: Optional[List[OpenGraphAudio]] = Field(
        default=None, description="OpenGraph audio"
    )
