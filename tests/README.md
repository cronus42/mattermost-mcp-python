# Test Suite Documentation

This directory contains comprehensive tests for the Mattermost MCP Python client, covering unit tests, integration tests, and live tests against real Mattermost instances.

## Test Structure

### Unit Tests
- **`test_api_exceptions.py`** - Tests for exception classes and error handling
- **`test_http_client.py`** - Tests for the HTTP client including httpx-mock integration
- **`test_services.py`** - Tests for service layer classes (Posts, Channels, etc.)
- **`test_server.py`** - Basic server tests

### Integration Tests
- **`test_integration.py`** - Contains both mocked integration tests and live tests
- **`test_streaming_resources.py`** - Tests for streaming resources (existing)

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -e ".[test]"
```

### Basic Unit Tests

Run all unit tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_http_client.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=mcp_mattermost --cov-report=html
```

### Mocked Integration Tests

The mocked integration tests run by default and don't require any external services:

```bash
pytest tests/test_integration.py::TestMockIntegration -v
```

These tests use `httpx-mock` to simulate realistic HTTP interactions without requiring a real Mattermost server.

### Live Integration Tests

Live integration tests run against a real Mattermost instance and are disabled by default.

#### Setup

1. Set up a test Mattermost instance (can be a sandbox or development instance)
2. Create a bot user and get a personal access token
3. Get the team ID you want to test with
4. Optionally, create a test channel for post operations

#### Configuration

Set the following environment variables:

```bash
# Required
export MATTERMOST_INTEGRATION_TESTS=true
export MATTERMOST_URL=https://your-mattermost-instance.com
export MATTERMOST_TOKEN=your-bot-token
export MATTERMOST_TEAM_ID=your-team-id

# Optional - for post creation/deletion tests
export MATTERMOST_TEST_CHANNEL_ID=your-test-channel-id
```

#### Running Live Tests

```bash
# Run all integration tests (mocked + live)
pytest tests/test_integration.py -v -s

# Run only live tests
pytest tests/test_integration.py::TestLiveIntegration -v -s
```

**⚠️ WARNING**: Live tests will make real API calls to your Mattermost instance and may create/delete test data.

## Test Categories

### HTTP Client Tests (`test_http_client.py`)

- **Basic functionality**: URL building, data preparation, response parsing
- **Authentication**: Token handling, auth errors
- **Rate limiting**: Token bucket algorithm, request throttling
- **Retry logic**: Exponential backoff, timeout handling
- **Error handling**: Various HTTP status codes
- **httpx-mock integration**: Realistic HTTP response mocking

### Service Layer Tests (`test_services.py`)

- **Base service**: Common functionality, error handling
- **Posts service**: CRUD operations, reactions, file attachments
- **Channels service**: Channel management, membership
- **Integration scenarios**: End-to-end workflows with mocked responses

### Exception Tests (`test_api_exceptions.py`)

- **Exception hierarchy**: All exception types and inheritance
- **Error context**: Structured logging and debugging information
- **Exception creation**: Automatic exception type selection based on HTTP status
- **Response parsing**: Error message extraction from various formats

### Integration Tests (`test_integration.py`)

#### Mocked Integration Tests
- **Complete workflows**: Post lifecycle, channel management
- **Error scenarios**: Authentication failures, 404s, server errors
- **Concurrent operations**: Multiple simultaneous API calls
- **Edge cases**: Empty responses, malformed JSON

#### Live Integration Tests
- **Authentication verification**: Real credential validation
- **Channel operations**: Listing, retrieving channel information
- **Post operations**: Creating, updating, deleting posts (if test channel configured)
- **Rate limiting**: Real rate limit behavior
- **Error handling**: Real server error responses

## Test Configuration

### pytest.ini Options

The test suite supports the following pytest configuration (defined in `pyproject.toml`):

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=mcp_mattermost --cov-report=term-missing"
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Environment Variables

- `MATTERMOST_INTEGRATION_TESTS` - Enable/disable live tests
- `MATTERMOST_URL` - Mattermost instance URL
- `MATTERMOST_TOKEN` - Bot authentication token
- `MATTERMOST_TEAM_ID` - Team ID for testing
- `MATTERMOST_TEST_CHANNEL_ID` - Optional channel for post tests

## Test Data Management

### Mocked Tests
- Use realistic but fake data
- No cleanup required
- Fast execution
- No external dependencies

### Live Tests
- Create minimal test data
- Automatic cleanup where possible
- Clear test data identification (marked with 🤖 emoji)
- Graceful failure handling

## Coverage Goals

- **Unit tests**: >90% code coverage
- **Integration tests**: Cover major user workflows
- **Error scenarios**: All exception types and HTTP status codes
- **Edge cases**: Empty responses, malformed data, network issues

## Best Practices

1. **Use httpx-mock for HTTP testing** - Provides realistic mocking without external dependencies
2. **Separate unit and integration tests** - Keep them in different test classes/files
3. **Mock external dependencies** - Use AsyncMock for service dependencies
4. **Test error conditions** - Verify proper exception handling
5. **Clean up test data** - Especially important for live tests
6. **Use descriptive test names** - Make test purpose clear
7. **Test concurrent operations** - Verify thread safety and async behavior

## Troubleshooting

### Common Issues

1. **ImportError** - Install test dependencies with `pip install -e ".[test]"`
2. **Connection errors** - Check Mattermost URL and network connectivity
3. **Authentication errors** - Verify token has proper permissions
4. **Rate limiting** - Use appropriate rate limits for your instance
5. **Test data pollution** - Ensure proper cleanup or use isolated test environments

### Debug Options

```bash
# Verbose output with print statements
pytest tests/ -v -s

# Show local variables on failure
pytest tests/ -v -l

# Drop into debugger on failure
pytest tests/ -v --pdb

# Run only failed tests from last run
pytest tests/ --lf
```

## Contributing

When adding new tests:

1. Follow existing patterns and naming conventions
2. Add both unit and integration test coverage for new features
3. Mock external dependencies appropriately
4. Include error condition testing
5. Update this documentation if needed
6. Ensure tests pass in both mocked and live modes (where applicable)

## Security Notes

- Never commit real credentials to version control
- Use environment variables for sensitive configuration
- Test with sandbox/development instances only
- Be cautious with live test data creation/deletion
- Review test output for sensitive information leakage
