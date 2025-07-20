# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-01-XX

### Added
- Complete CI/CD pipeline with GitHub Actions
  - Automated linting with flake8, black, and isort
  - Type checking with mypy across Python 3.8-3.12
  - Testing with pytest and coverage reporting
  - Automated package building and PyPI publishing on releases/tags
- Pre-commit hooks configuration for local development
- Dependabot configuration for automated dependency updates
- PEP 561 type information marker (`py.typed`)
- MIT License file
- Package manifest for proper distribution

### Changed
- Version bumped to 0.2.0
- Updated license configuration to use modern SPDX expression
- Improved package metadata and classifiers

### Fixed
- Resolved setuptools deprecation warnings
- Proper package structure for distribution

## [0.1.0] - 2024-01-XX

### Added
- Initial MCP Mattermost server implementation
- Core API client and models
- WebSocket event handling
- Streaming resources support
- Basic testing framework
- Documentation and examples
