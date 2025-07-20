#!/usr/bin/env python3
"""
Script to validate the generated Pydantic models.

This script tests the models by creating sample instances and validating
they work correctly with various data types and edge cases.
"""

import json
from datetime import datetime
from typing import Any, Dict

# Import models directly to avoid server dependency issues
from mcp_mattermost.models.base import ErrorResponse, StatusOK
from mcp_mattermost.models.channels import Channel, ChannelCreate
from mcp_mattermost.models.posts import Post, PostCreate
from mcp_mattermost.models.teams import Team, TeamCreate
from mcp_mattermost.models.users import User, UserCreate


def test_user_model():
    """Test User model creation and validation."""
    print("Testing User model...")

    # Test with minimal data
    user_data = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "create_at": 1609459200000,  # 2021-01-01T00:00:00Z
    }

    user = User(**user_data)
    print(f"✓ User created: {user.display_name}")

    # Test datetime conversion
    created_dt = user.created_datetime()
    assert isinstance(created_dt, datetime)
    print(f"✓ Created datetime: {created_dt}")

    # Test property methods
    print(f"✓ Display name: '{user.display_name}'")
    print(f"✓ Is deleted: {user.is_deleted()}")

    # Test with full data
    full_user_data = {
        "id": "user456",
        "username": "fulluser",
        "email": "full@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "nickname": "Johnny",
        "create_at": 1609459200000,
        "update_at": 1609545600000,
        "email_verified": True,
        "mfa_active": False,
    }

    full_user = User(**full_user_data)
    print(f"✓ Full user created: {full_user.display_name}")
    print(f"✓ Full name: {full_user.full_name}")


def test_team_model():
    """Test Team model creation and validation."""
    print("\nTesting Team model...")

    team_data = {
        "id": "team123",
        "name": "test-team",
        "display_name": "Test Team",
        "type": "O",
        "create_at": 1609459200000,
        "allow_open_invite": True,
    }

    team = Team(**team_data)
    print(f"✓ Team created: {team.display_name}")

    # Test team creation request
    team_create = TeamCreate(
        name="new-team",
        display_name="New Team",
        type="O",
        description="A new test team",
    )
    print(f"✓ Team creation request: {team_create.name}")


def test_channel_model():
    """Test Channel model creation and validation."""
    print("\nTesting Channel model...")

    channel_data = {
        "id": "channel123",
        "team_id": "team123",
        "name": "test-channel",
        "display_name": "Test Channel",
        "type": "O",
        "create_at": 1609459200000,
        "creator_id": "user123",
    }

    channel = Channel(**channel_data)
    print(f"✓ Channel created: {channel.display_name}")
    print(f"✓ Is public: {channel.is_public}")
    print(f"✓ Is private: {channel.is_private}")
    print(f"✓ Is DM: {channel.is_direct_message}")

    # Test channel creation request
    channel_create = ChannelCreate(
        team_id="team123",
        name="new-channel",
        display_name="New Channel",
        type="P",
        purpose="Testing channel creation",
    )
    print(f"✓ Channel creation request: {channel_create.name}")


def test_post_model():
    """Test Post model creation and validation."""
    print("\nTesting Post model...")

    post_data = {
        "id": "post123",
        "user_id": "user123",
        "channel_id": "channel123",
        "message": "Hello, world!",
        "create_at": 1609459200000,
        "edit_at": 0,
        "file_ids": ["file1", "file2"],
    }

    post = Post(**post_data)
    print(f"✓ Post created: {post.message[:20]}...")
    print(f"✓ Is reply: {post.is_reply}")
    print(f"✓ Is edited: {post.is_edited}")
    print(f"✓ Has attachments: {post.has_attachments}")

    # Test post creation request
    post_create = PostCreate(
        channel_id="channel123",
        message="New post content",
        file_ids=["file3"],
    )
    print(f"✓ Post creation request: {post_create.message[:20]}...")


def test_response_models():
    """Test response models."""
    print("\nTesting Response models...")

    # Test StatusOK
    ok_response = StatusOK()
    print(f"✓ StatusOK: {ok_response.status}")

    # Test ErrorResponse
    error_data = {
        "id": "api.error.generic",
        "message": "Something went wrong",
        "status_code": 400,
        "is_oauth": False,
    }

    error_response = ErrorResponse(**error_data)
    print(f"✓ Error response: {error_response.message}")


def test_json_serialization():
    """Test JSON serialization and deserialization."""
    print("\nTesting JSON serialization...")

    user_data = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "create_at": 1609459200000,
    }

    # Create user from dict
    user = User(**user_data)

    # Serialize to JSON
    user_json = user.model_dump_json()
    print(f"✓ User serialized to JSON: {len(user_json)} chars")

    # Deserialize from JSON
    user_dict = json.loads(user_json)
    user_restored = User(**user_dict)
    print(f"✓ User restored from JSON: {user_restored.username}")

    assert user.username == user_restored.username
    assert user.email == user_restored.email


def test_validation_errors():
    """Test model validation with invalid data."""
    print("\nTesting validation...")

    try:
        # This should work fine
        UserCreate(
            username="valid_user", email="valid@example.com", password="password123"
        )
        print("✓ Valid UserCreate model accepted")

        # This should fail validation (missing required fields)
        try:
            UserCreate(username="invalid_user")  # Missing email and password
            print("✗ Should have failed validation")
        except Exception as e:
            print(f"✓ Validation error caught: {type(e).__name__}")

    except Exception as e:
        print(f"Unexpected error: {e}")


def main():
    """Run all tests."""
    print("=" * 50)
    print("Validating Mattermost Pydantic Models")
    print("=" * 50)

    try:
        test_user_model()
        test_team_model()
        test_channel_model()
        test_post_model()
        test_response_models()
        test_json_serialization()
        test_validation_errors()

        print("\n" + "=" * 50)
        print("✅ All model validation tests passed!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
