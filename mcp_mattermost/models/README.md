# Mattermost Pydantic Models

This directory contains comprehensive Pydantic models for all major Mattermost API entities. These models provide type-safe data validation, serialization, and deserialization for interacting with the Mattermost API.

## Overview

The models are organized into several modules based on functionality:

- **`base.py`** - Base classes and common response types
- **`users.py`** - User entities and authentication
- **`teams.py`** - Team entities and memberships  
- **`channels.py`** - Channel entities and memberships
- **`posts.py`** - Posts, reactions, and file attachments
- **`auth.py`** - Authentication, sessions, and tokens
- **`webhooks.py`** - Webhooks, bots, and integrations

## Key Features

### Type Safety
All models use Pydantic v2 for robust type validation:

```python
from mcp_mattermost.models import User

# Automatic validation of data types
user = User(
    id="user123",
    username="john_doe",
    email="john@example.com",
    create_at=1609459200000
)
```

### Datetime Utilities
Base models include convenient datetime conversion methods:

```python
user = User(create_at=1609459200000)
created_dt = user.created_datetime()  # Returns datetime object
print(f"User created: {created_dt}")
```

### JSON Serialization
Full support for JSON serialization and deserialization:

```python
# Serialize to JSON
user_json = user.model_dump_json()

# Deserialize from JSON
user_restored = User.model_validate_json(user_json)
```

### Flexible Configuration
Models support extra fields for forward compatibility:

```python
# Will accept unknown fields without errors
user = User(**api_response_data)
```

## Core Models

### Base Models

- **`MattermostBase`** - Base class for all Mattermost entities
- **`MattermostResponse`** - Base class for API responses
- **`StatusOK`** - Standard success response
- **`ErrorResponse`** - Standard error response

### User Models

- **`User`** - Complete user entity
- **`UserCreate`** - User creation request
- **`UserPatch`** - User update request
- **`UserNotifyProps`** - User notification settings
- **`Timezone`** - User timezone information

### Team Models

- **`Team`** - Team entity
- **`TeamMember`** - Team membership
- **`TeamCreate`** - Team creation request
- **`TeamStats`** - Team statistics

### Channel Models

- **`Channel`** - Channel entity
- **`ChannelMember`** - Channel membership
- **`ChannelCreate`** - Channel creation request
- **`ChannelNotifyProps`** - Channel notification settings

### Post Models

- **`Post`** - Post entity with metadata
- **`PostCreate`** - Post creation request
- **`Reaction`** - Post reaction
- **`FileInfo`** - File attachment information
- **`OpenGraph`** - OpenGraph metadata for links

### Authentication Models

- **`Session`** - User session
- **`LoginRequest`** - Login request
- **`AccessToken`** - Personal access token
- **`OAuthApp`** - OAuth application

### Integration Models

- **`IncomingWebhook`** - Incoming webhook
- **`OutgoingWebhook`** - Outgoing webhook
- **`Command`** - Slash command
- **`Bot`** - Bot user

## Usage Examples

### Creating a New User

```python
from mcp_mattermost.models import UserCreate

user_request = UserCreate(
    username="new_user",
    email="user@example.com",
    password="secure_password",
    first_name="John",
    last_name="Doe"
)
```

### Working with Posts

```python
from mcp_mattermost.models import Post, PostCreate

# Creating a post
post_request = PostCreate(
    channel_id="channel123",
    message="Hello, world!",
    file_ids=["file1", "file2"]
)

# Working with existing post
post = Post(**api_response)
print(f"Post by user {post.user_id}: {post.message}")
print(f"Has attachments: {post.has_attachments}")
print(f"Is reply: {post.is_reply}")
```

### Channel Management

```python
from mcp_mattermost.models import Channel, ChannelCreate

# Create a new channel
channel_request = ChannelCreate(
    team_id="team123",
    name="general",
    display_name="General Discussion",
    type="O",  # Open/Public
    purpose="Team-wide discussions"
)

# Work with existing channel
channel = Channel(**api_response)
print(f"Channel: {channel.display_name}")
print(f"Is public: {channel.is_public}")
print(f"Is DM: {channel.is_direct_message}")
```

### Authentication

```python
from mcp_mattermost.models import LoginRequest, Session

# Login request
login = LoginRequest(
    login_id="user@example.com",
    password="password123",
    device_id="mobile_device"
)

# Working with session
session = Session(**api_response)
print(f"Session expires: {session.expires_at}")
print(f"Is expired: {session.is_expired}")
```

## Validation

All models include comprehensive validation:

```python
from mcp_mattermost.models import User
from pydantic import ValidationError

try:
    user = User(
        username="valid_user",
        email="not-an-email"  # Invalid email format
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Timestamps

Mattermost uses millisecond timestamps. The base model includes utilities:

```python
user = User(create_at=1609459200000)

# Convert to Python datetime
created = user.created_datetime()

# Check if entity is deleted
is_deleted = user.is_deleted()
```

## Forward Compatibility

Models are configured to accept extra fields, ensuring compatibility with new Mattermost versions:

```python
# Will work even if API returns new fields
user = User(**api_response_with_new_fields)

# Extra fields are preserved
extra_data = user.model_dump()
```

## Development

To add new models:

1. Create the model class inheriting from `MattermostBase` or `MattermostResponse`
2. Add appropriate field definitions with types and descriptions
3. Include any custom validation or utility methods
4. Export the model in `__init__.py`
5. Add tests to validate the model works correctly

## Testing

Run the validation script to test all models:

```bash
python validate_models.py
```

This will test model creation, validation, serialization, and edge cases.
