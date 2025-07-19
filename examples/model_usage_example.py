#!/usr/bin/env python3
"""
Example demonstrating practical usage of Mattermost Pydantic models.

This example shows how to use the models for common Mattermost operations
like creating users, teams, channels, and posts with proper type safety.
"""

from datetime import datetime
from mcp_mattermost.models import (
    # User models
    User, UserCreate, UserNotifyProps, Timezone,
    # Team models  
    Team, TeamCreate, TeamMember,
    # Channel models
    Channel, ChannelCreate, ChannelMember, ChannelNotifyProps,
    # Post models
    Post, PostCreate, Reaction, FileInfo,
    # Response models
    StatusOK, ErrorResponse,
    # Auth models
    LoginRequest, Session, AccessToken,
)


def demonstrate_user_operations():
    """Demonstrate user-related model operations."""
    print("=== User Operations ===")
    
    # Create a new user request
    user_request = UserCreate(
        username="alice_cooper",
        email="alice@example.com", 
        password="secure_password_123",
        first_name="Alice",
        last_name="Cooper",
        locale="en-US"
    )
    print(f"✓ User creation request: {user_request.username}")
    
    # Simulate API response for created user
    user_data = {
        "id": "user_alice_123",
        "username": "alice_cooper",
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Cooper",
        "create_at": int(datetime.now().timestamp() * 1000),
        "update_at": int(datetime.now().timestamp() * 1000),
        "email_verified": True,
        "mfa_active": False,
        "locale": "en-US",
        "timezone": {
            "use_auto_timezone": True,
            "auto_timezone": "America/New_York"
        },
        "notify_props": {
            "email": "true",
            "desktop": "mention",
            "push": "mention",
            "first_name": "true"
        }
    }
    
    user = User(**user_data)
    print(f"✓ User created: {user.display_name}")
    print(f"  - Full name: {user.full_name}")
    print(f"  - Created: {user.created_datetime()}")
    print(f"  - Email verified: {user.email_verified}")
    print()


def demonstrate_team_operations():
    """Demonstrate team-related model operations."""
    print("=== Team Operations ===")
    
    # Create a new team
    team_request = TeamCreate(
        name="engineering-team",
        display_name="Engineering Team", 
        type="O",  # Open team
        description="Software engineering team workspace",
        allow_open_invite=True
    )
    print(f"✓ Team creation request: {team_request.display_name}")
    
    # Simulate team API response
    team_data = {
        "id": "team_eng_456",
        "name": "engineering-team",
        "display_name": "Engineering Team",
        "type": "O",
        "description": "Software engineering team workspace", 
        "create_at": int(datetime.now().timestamp() * 1000),
        "allow_open_invite": True,
        "email": "eng-team@example.com"
    }
    
    team = Team(**team_data)
    print(f"✓ Team created: {team.display_name}")
    
    # Team member
    member_data = {
        "team_id": "team_eng_456",
        "user_id": "user_alice_123", 
        "roles": "team_user team_admin",
        "scheme_admin": True,
        "scheme_user": True
    }
    
    member = TeamMember(**member_data)
    print(f"✓ Team member added: {member.user_id}")
    print()


def demonstrate_channel_operations():
    """Demonstrate channel-related model operations.""" 
    print("=== Channel Operations ===")
    
    # Create a new channel
    channel_request = ChannelCreate(
        team_id="team_eng_456",
        name="backend-dev",
        display_name="Backend Development",
        type="O",  # Public channel
        purpose="Backend development discussions",
        header="🚀 Backend Development Team"
    )
    print(f"✓ Channel creation request: {channel_request.display_name}")
    
    # Simulate channel API response
    channel_data = {
        "id": "channel_backend_789",
        "team_id": "team_eng_456",
        "name": "backend-dev",
        "display_name": "Backend Development",
        "type": "O",
        "purpose": "Backend development discussions",
        "header": "🚀 Backend Development Team",
        "create_at": int(datetime.now().timestamp() * 1000),
        "creator_id": "user_alice_123",
        "last_post_at": int(datetime.now().timestamp() * 1000),
        "total_msg_count": 0
    }
    
    channel = Channel(**channel_data)
    print(f"✓ Channel created: {channel.display_name}")
    print(f"  - Type: {'Public' if channel.is_public else 'Private'}")
    print(f"  - Purpose: {channel.purpose}")
    print()


def demonstrate_post_operations():
    """Demonstrate post-related model operations."""
    print("=== Post Operations ===")
    
    # Create a new post
    post_request = PostCreate(
        channel_id="channel_backend_789",
        message="Welcome to the backend development channel! 👋\n\nLet's build amazing things together.",
        props={"from_webhook": "false", "mentions": []}
    )
    print(f"✓ Post creation request: {post_request.message[:50]}...")
    
    # Simulate post API response
    post_data = {
        "id": "post_welcome_101",
        "user_id": "user_alice_123",
        "channel_id": "channel_backend_789", 
        "message": "Welcome to the backend development channel! 👋\n\nLet's build amazing things together.",
        "create_at": int(datetime.now().timestamp() * 1000),
        "update_at": int(datetime.now().timestamp() * 1000),
        "edit_at": 0,
        "type": "",
        "props": {"from_webhook": "false"},
        "hashtag": "",
        "file_ids": []
    }
    
    post = Post(**post_data)
    print(f"✓ Post created: {post.message[:50]}...")
    print(f"  - Author: {post.user_id}")
    print(f"  - Is reply: {post.is_reply}")
    print(f"  - Has attachments: {post.has_attachments}")
    print(f"  - Created: {post.created_datetime()}")
    
    # Add a reaction
    reaction_data = {
        "user_id": "user_bob_456",
        "post_id": "post_welcome_101",
        "emoji_name": "thumbs_up",
        "create_at": int(datetime.now().timestamp() * 1000)
    }
    
    reaction = Reaction(**reaction_data)
    print(f"✓ Reaction added: {reaction.emoji_name} by {reaction.user_id}")
    print()


def demonstrate_authentication():
    """Demonstrate authentication model operations."""
    print("=== Authentication ===")
    
    # Login request
    login_request = LoginRequest(
        login_id="alice@example.com",
        password="secure_password_123",
        device_id="web_browser_chrome"
    )
    print(f"✓ Login request: {login_request.login_id}")
    
    # Session response (without team_members to avoid forward reference)
    session_data = {
        "id": "session_abc_789",
        "user_id": "user_alice_123",
        "device_id": "web_browser_chrome",
        "create_at": int(datetime.now().timestamp() * 1000),
        "expires_at": int((datetime.now().timestamp() + 86400) * 1000),  # 24 hours
        "last_activity_at": int(datetime.now().timestamp() * 1000),
        "is_oauth": False,
        "token": "session_token_xyz_123",
        "roles": "system_user"
    }
    
    session = Session(**session_data)
    print(f"✓ Session created: {session.id}")
    print(f"  - Expires at: {session.expires_at}")
    print(f"  - Is expired: {session.is_expired}")
    
    # Personal access token
    token_data = {
        "id": "token_personal_456",
        "user_id": "user_alice_123", 
        "description": "API access for development",
        "token": "mmp_xxxxxxxxxxxxxxxxxxxx",
        "is_active": True,
        "create_at": int(datetime.now().timestamp() * 1000)
    }
    
    access_token = AccessToken(**token_data)
    print(f"✓ Access token: {access_token.description}")
    print()


def demonstrate_serialization():
    """Demonstrate JSON serialization/deserialization."""
    print("=== JSON Serialization ===")
    
    # Create a user with nested objects
    user_data = {
        "id": "user_complex_999",
        "username": "complex_user",
        "email": "complex@example.com",
        "first_name": "Complex",
        "last_name": "User", 
        "create_at": int(datetime.now().timestamp() * 1000),
        "timezone": {
            "use_auto_timezone": False,
            "manual_timezone": "Europe/London",
            "auto_timezone": "America/New_York"
        },
        "notify_props": {
            "email": "true",
            "desktop": "all",
            "push": "none",
            "mention_keys": "complex,@complex"
        }
    }
    
    user = User(**user_data)
    print(f"✓ Complex user created: {user.display_name}")
    
    # Serialize to JSON
    user_json = user.model_dump_json(indent=2)
    print(f"✓ Serialized to JSON ({len(user_json)} chars)")
    
    # Deserialize back
    user_restored = User.model_validate_json(user_json)
    print(f"✓ Restored from JSON: {user_restored.username}")
    
    # Verify data integrity
    assert user.username == user_restored.username
    assert user.timezone.manual_timezone == user_restored.timezone.manual_timezone
    print("✓ Data integrity verified")
    print()


def demonstrate_error_handling():
    """Demonstrate error handling and validation."""
    print("=== Error Handling ===")
    
    # Valid response
    ok_response = StatusOK(status="OK")
    print(f"✓ Success response: {ok_response.status}")
    
    # Error response
    error_data = {
        "id": "app.user.save.email_exists.app_error",
        "message": "An account with that email already exists.",
        "detailed_error": "Email: alice@example.com",
        "status_code": 400,
        "is_oauth": False,
        "request_id": "req_123_abc"
    }
    
    error = ErrorResponse(**error_data)
    print(f"✓ Error response: {error.message}")
    print(f"  - Status code: {error.status_code}")
    print(f"  - Request ID: {error.request_id}")
    print()


def main():
    """Run all demonstrations."""
    print("🚀 Mattermost Pydantic Models - Usage Examples")
    print("=" * 60)
    print()
    
    demonstrate_user_operations()
    demonstrate_team_operations() 
    demonstrate_channel_operations()
    demonstrate_post_operations()
    demonstrate_authentication()
    demonstrate_serialization()
    demonstrate_error_handling()
    
    print("=" * 60)
    print("✅ All examples completed successfully!")
    print()
    print("Key Benefits:")
    print("- ✨ Full type safety with Pydantic validation")
    print("- 🔄 Seamless JSON serialization/deserialization") 
    print("- 📅 Built-in datetime conversion utilities")
    print("- 🛡️ Robust error handling and validation")
    print("- 🔮 Forward compatibility with extra field support")
    print("- 🎯 Rich property methods for common operations")


if __name__ == "__main__":
    main()
