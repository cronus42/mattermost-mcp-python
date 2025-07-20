# Contributing to MCP Mattermost Python

Thank you for your interest in contributing to the MCP Mattermost Python project! This guide will help you get started with development and understand our CI/CD processes.

## 🚀 Quick Setup

1. **Fork and clone** the repository
2. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev,test,metrics]"
   ```

4. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## 🛠️ Development Workflow

### Code Quality Tools

We use several tools to maintain high code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

### Running Tests Locally

```bash
# Run all tests with coverage
pytest --cov=mcp_mattermost --cov-report=term-missing

# Run specific test file
pytest tests/test_server.py

# Run with verbose output
pytest -v
```

### Code Formatting and Linting

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy mcp_mattermost/

# Run all checks (what CI runs)
black --check .
isort --check-only .
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
mypy mcp_mattermost/
```

### Pre-commit Hooks

Pre-commit hooks automatically run before each commit to ensure code quality:

```bash
# Install hooks (one time setup)
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

## 🔄 CI/CD Pipeline

### Automated Workflows

Our CI/CD pipeline includes several automated workflows:

#### 1. Main CI Workflow (`.github/workflows/ci.yml`)

Runs on every push and PR:
- **Linting**: flake8, black, isort across Python 3.8-3.12
- **Type Checking**: mypy across all supported Python versions
- **Testing**: pytest with coverage reporting
- **Building**: Package building and validation
- **Publishing**: Automatic PyPI publishing on GitHub releases

#### 2. Release Workflow (`.github/workflows/release.yml`)

Runs on tag creation (`v*.*.*`):
- Full test suite across all Python versions
- Package building and PyPI publishing
- Automatic GitHub release creation

#### 3. Dependency Updates (`.github/dependabot.yml`)

- Weekly dependency updates for Python packages
- Weekly GitHub Actions version updates
- Automatic PR creation with changelogs

### Making a Release

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.3.0"  # Increment version
   ```

2. **Update CHANGELOG.md** with release notes

3. **Create and push a tag**:
   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```

4. **GitHub Actions will automatically**:
   - Run the full test suite
   - Build packages
   - Publish to PyPI
   - Create a GitHub release

### Publishing to PyPI

Publishing happens automatically via GitHub Actions using trusted publishing:

- **On Release**: When you publish a GitHub release
- **On Tag**: When you push a version tag (v*.*.*)

No manual PyPI tokens needed - GitHub Actions uses OIDC trusted publishing.

## 📝 Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Run tests locally**:
   ```bash
   pytest
   black --check .
   isort --check-only .
   flake8 .
   mypy mcp_mattermost/
   ```

4. **Commit with conventional commits**:
   ```bash
   git commit -m "feat: add new messaging tool"
   git commit -m "fix: resolve connection timeout issue"
   git commit -m "docs: update API documentation"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

### PR Requirements

- ✅ All CI checks must pass
- ✅ Code coverage should not decrease significantly
- ✅ Include tests for new functionality
- ✅ Update documentation if needed
- ✅ Follow conventional commit messages

## 🏗️ Package Structure

```
mcp_mattermost/
├── api/              # HTTP client and API interactions
├── events/           # WebSocket and event handling
├── models/           # Pydantic data models
├── resources/        # MCP streaming resources
├── services/         # Business logic services
├── tools/            # MCP tools implementation
└── utils/            # Utility functions
```

## 🐛 Testing

### Test Structure

```
tests/
├── test_server.py           # MCP server tests
├── test_api_exceptions.py   # API error handling
├── test_integration.py      # Integration tests
├── test_services.py         # Service layer tests
└── test_streaming_resources.py  # Real-time feature tests
```

### Writing Tests

```python
import pytest
from mcp_mattermost.services import UsersService

@pytest.mark.asyncio
async def test_user_search():
    """Test user search functionality."""
    service = UsersService(base_url="http://test", token="test")
    # Your test implementation
```

## 📚 Documentation

- Update docstrings for new functions/classes
- Add examples to `examples/` directory
- Update `docs/` for architectural changes
- Keep `README.md` current with new features

## 🔍 Code Review Guidelines

### For Contributors
- Write clear, self-documenting code
- Include comprehensive tests
- Follow existing patterns and conventions
- Update documentation accordingly

### For Reviewers
- Focus on code quality, maintainability, and correctness
- Ensure proper error handling and logging
- Verify test coverage for new functionality
- Check for security implications

## 🚨 Security

- Never commit secrets, tokens, or sensitive data
- Use environment variables for configuration
- Follow secure coding practices
- Report security issues privately to maintainers

## 📞 Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time community support (link in README)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to MCP Mattermost Python! 🎉
