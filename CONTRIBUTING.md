# Contributing to Plex Releases Summary

Thank you for considering contributing to Plex Releases Summary! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project follows a standard Code of Conduct. Please be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a feature branch for your changes
4. Make your changes and commit them
5. Push to your fork and submit a pull request

## Development Setup

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.12+ (for local development)
- Git

### Option 1: Docker Development Environment (Recommended)

The project includes a hot-reload development environment using Docker Compose:

```bash
# Copy the example environment file
cp docker-compose.dev.local.yml.example docker-compose.dev.local.yml

# Edit docker-compose.dev.local.yml with your Tautulli credentials
# Then start the development environment
docker-compose -f docker-compose.dev.yml -f docker-compose.dev.local.yml up

# The application will automatically reload when you edit source files
```

### Option 2: Local Python Development

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-test.txt

# Copy and configure the config file
cp configs/config.yml configs/config-dev.yml
# Edit configs/config-dev.yml with your settings

# Run the application
cd src
python app.py
```

### Installing Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Run hooks manually (optional)
pre-commit run --all-files
```

## Code Style Guidelines

### Python Style

We follow PEP 8 with some modifications:

- **Line length:** 120 characters maximum
- **Formatting:** Use Black for automatic formatting
- **Linting:** Use Ruff for linting
- **Type hints:** Required for all public functions and methods
- **Docstrings:** Required for all public modules, classes, and functions (Google style)

### Code Organization

- Keep functions focused and single-purpose
- Use meaningful variable and function names
- Prefer explicit over implicit
- Use type hints consistently
- Document complex logic with comments

### Example Function

```python
def calculate_batch_size(days: int, override: Optional[int] = None) -> tuple[int, int]:
    """
    Calculate initial batch size and increment based on time range.

    Args:
        days: Number of days to look back
        override: Optional override value from configuration

    Returns:
        Tuple of (initial_count, increment)
        
    Examples:
        >>> calculate_batch_size(7)
        (100, 100)
        >>> calculate_batch_size(30, override=500)
        (500, 500)
    """
    if override is not None:
        return (override, override)
    # ... implementation
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::TestConfigModel::test_minimal_valid_config

# Run only unit tests
pytest -m unit

# Run tests in verbose mode
pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_<module>.py`
- Use descriptive test names: `test_<function>_<scenario>_<expected_result>`
- Use pytest fixtures for common setup
- Mark tests appropriately: `@pytest.mark.unit`, `@pytest.mark.integration`
- Aim for >80% code coverage for new code

### Test Example

```python
import pytest
from src.config import Config

class TestConfigValidation:
    """Tests for Config validation."""

    @pytest.mark.unit
    def test_minimal_valid_config(self):
        """Test creating config with only required fields."""
        config = Config(
            tautulli_url="http://localhost:8181",
            tautulli_api_key="test_key",
            run_once=True
        )
        assert config.tautulli_url == "http://localhost:8181"
        assert config.days_back == 7  # Default value

    @pytest.mark.unit
    def test_invalid_log_level_raises_error(self):
        """Test that invalid log level raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                tautulli_url="http://localhost:8181",
                tautulli_api_key="test_key",
                log_level="INVALID",
                run_once=True
            )
        assert "log_level" in str(exc_info.value)
```

## Pull Request Process

### Before Submitting

1. **Run tests:** Ensure all tests pass
   ```bash
   pytest
   ```

2. **Run linters:** Fix any linting issues
   ```bash
   ruff check src/ tests/ --fix
   black src/ tests/
   ```

3. **Run type checker:** Address any type errors
   ```bash
   mypy src/
   ```

4. **Update documentation:** Update relevant docs if needed

5. **Add tests:** Include tests for new functionality

### PR Guidelines

1. **Title:** Use a clear, descriptive title
   - Good: "Add retry logic for Discord webhook failures"
   - Bad: "Fix bug"

2. **Description:** Include:
   - What changes were made and why
   - Related issue numbers (if any)
   - Testing performed
   - Breaking changes (if any)

3. **Size:** Keep PRs focused and reasonably sized
   - Prefer smaller, focused PRs over large ones
   - Split large changes into multiple PRs when possible

4. **Commits:** Use clear commit messages
   - Follow [Conventional Commits](https://www.conventionalcommits.org/) format
   - Examples:
     - `feat: add rate limiting between API calls`
     - `fix: escape markdown characters in Discord titles`
     - `docs: update configuration examples`
     - `test: add unit tests for config validation`

### PR Review Process

1. Automated checks must pass (tests, linting)
2. At least one maintainer review required
3. All comments must be addressed
4. Maintainer will merge when approved

## Reporting Bugs

### Before Submitting a Bug Report

- Check the [existing issues](https://github.com/thomas-lg/plex-releases-summary/issues)
- Check the [documentation](docs/CONFIGURATION.md)
- Verify you're using the latest version

### Submitting a Bug Report

Use the bug report issue template and include:

1. **Description:** Clear description of the bug
2. **Expected behavior:** What you expected to happen
3. **Actual behavior:** What actually happened
4. **Steps to reproduce:** Detailed steps to reproduce the issue
5. **Environment:**
   - OS and version
   - Python version
   - Docker version (if applicable)
   - Application version
6. **Logs:** Relevant log output (set `log_level: DEBUG` in config)
7. **Configuration:** Sanitized config.yml (remove credentials!)

## Suggesting Enhancements

### Before Submitting

- Check if the enhancement has already been suggested
- Consider if it fits the project's scope and goals

### Submitting an Enhancement

1. Use the feature request issue template
2. Provide a clear use case
3. Describe the proposed solution
4. Consider alternative solutions
5. Explain benefits to users

## Development Tips

### Useful Commands

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type check
mypy src/

# Run tests with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Run pre-commit hooks manually
pre-commit run --all-files

# Build Docker image locally
docker build -t plex-releases-summary:dev .

# Run Docker container locally
docker run --rm -v $(pwd)/configs:/app/configs plex-releases-summary:dev
```

### Project Structure

```
plex-releases-summary/
├── src/                    # Source code
│   ├── app.py             # Main application logic
│   ├── config.py          # Configuration management
│   ├── discord_client.py  # Discord webhook client
│   ├── tautulli_client.py # Tautulli API client
│   ├── scheduler.py       # CRON scheduler
│   └── logging_config.py  # Logging configuration
├── tests/                  # Test files
│   ├── test_config.py     # Config tests
│   ├── test_app.py        # App tests
│   └── test_discord_client.py  # Discord tests
├── configs/               # Configuration files
├── docs/                  # Documentation
├── .github/               # GitHub Actions workflows
└── docker-compose*.yml    # Docker Compose configurations
```

### Debugging

Enable DEBUG logging for detailed output:

```yaml
# config.yml
log_level: DEBUG
```

For Docker environments:

```bash
# View logs
docker-compose logs -f

# Execute commands in running container
docker-compose exec plex-releases-summary sh

# View configuration
docker-compose exec plex-releases-summary cat /app/configs/config.yml
```

## Questions?

If you have questions not covered here:

1. Check the [documentation](docs/CONFIGURATION.md)
2. Search [existing issues](https://github.com/thomas-lg/plex-releases-summary/issues)
3. Open a new issue with the question label

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).

---

Thank you for contributing to Plex Releases Summary! 🎬📺💿
