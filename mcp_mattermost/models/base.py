"""
Base models and common types for Mattermost entities.

This module provides base classes and common types used across
all Mattermost data models.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MattermostBase(BaseModel):
    """Base class for all Mattermost models with common configuration."""

    model_config = ConfigDict(
        # Allow extra fields for forward compatibility
        extra="allow",
        # Use enum values instead of enum objects
        use_enum_values=True,
        # Validate assignment
        validate_assignment=True,
        # Populate by name (allows field aliases)
        populate_by_name=True,
    )

    id: Optional[str] = Field(default=None, description="Unique identifier")
    create_at: Optional[int] = Field(
        default=None, description="The time in milliseconds when the entity was created"
    )
    update_at: Optional[int] = Field(
        default=None,
        description="The time in milliseconds when the entity was last updated",
    )
    delete_at: Optional[int] = Field(
        default=None, description="The time in milliseconds when the entity was deleted"
    )

    @field_validator("create_at", "update_at", "delete_at", mode="before")
    @classmethod
    def validate_timestamp(cls, v: Any) -> Optional[int]:
        """Validate timestamp fields."""
        if v is None or v == 0:
            return None
        if isinstance(v, (int, float)):
            return int(v)
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v

    def created_datetime(self) -> Optional[datetime]:
        """Convert create_at timestamp to datetime."""
        if self.create_at:
            return datetime.fromtimestamp(self.create_at / 1000.0)
        return None

    def updated_datetime(self) -> Optional[datetime]:
        """Convert update_at timestamp to datetime."""
        if self.update_at:
            return datetime.fromtimestamp(self.update_at / 1000.0)
        return None

    def deleted_datetime(self) -> Optional[datetime]:
        """Convert delete_at timestamp to datetime."""
        if self.delete_at:
            return datetime.fromtimestamp(self.delete_at / 1000.0)
        return None

    def is_deleted(self) -> bool:
        """Check if the entity is deleted."""
        return self.delete_at is not None and self.delete_at > 0


class MattermostResponse(BaseModel):
    """Base class for Mattermost API responses."""

    model_config = ConfigDict(extra="allow")


class StatusOK(MattermostResponse):
    """Standard OK response."""

    status: str = Field(default="OK", description="Response status")


class ErrorResponse(MattermostResponse):
    """Standard error response."""

    id: Optional[str] = Field(default=None, description="Error identifier")
    message: Optional[str] = Field(default=None, description="Error message")
    detailed_error: Optional[str] = Field(
        default=None, description="Detailed error description"
    )
    request_id: Optional[str] = Field(default=None, description="Request identifier")
    status_code: Optional[int] = Field(default=None, description="HTTP status code")
    is_oauth: Optional[bool] = Field(
        default=None, description="Whether the error is OAuth specific"
    )
