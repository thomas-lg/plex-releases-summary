# Contributing to Plex Releases Summary

Thank you for contributing to Plex Releases Summary.

## Table of Contents

- [Contributing to Plex Releases Summary](#contributing-to-plex-releases-summary)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
  - [Development Setup](#development-setup)
    - [Prerequisites](#prerequisites)
    - [Canonical Workflow (Devcontainer)](#canonical-workflow-devcontainer)
    - [Optional Host Workflow](#optional-host-workflow)
  - [Code Style](#code-style)
  - [Testing](#testing)
  - [Pull Request Process](#pull-request-process)
  - [Production Image and Deployment](#production-image-and-deployment)

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch
4. Make your changes and open a pull request

## Development Setup

### Prerequisites

- Docker
- VS Code + Dev Containers extension
- Git

### Canonical Workflow (Devcontainer)

Open the project in the devcontainer:

```text
Command Palette → Dev Containers: Reopen in Container
```

Inside the devcontainer, run checks with either direct commands or helper scripts:

```bash
./scripts/format.sh
./scripts/typecheck.sh
./scripts/test.sh
```

Equivalent direct commands:

```bash
black src tests
ruff check --fix src tests
PYTHONPATH=src mypy src
PYTHONPATH=src pytest --cov=src --cov-report=xml --cov-report=term
```

### Optional Host Workflow

Host-native development is optional and not the primary workflow. If you use it, mirror the same Python/tool versions as the devcontainer.

## Code Style

- Python 3.12
- Black for formatting
- Ruff for linting
- mypy for type checking
- Type hints for public functions/methods

## Testing

Run all tests:

```bash
./scripts/test.sh
```

Run a subset:

```bash
./scripts/test.sh tests/test_config.py
./scripts/test.sh -k "test_config"
```

## Pull Request Process

Before submitting:

1. Run formatting/lint checks

   ```bash
   ./scripts/format.sh --check src tests
   ```

2. Run type checks

   ```bash
   ./scripts/typecheck.sh
   ```

3. Run tests

   ```bash
   ./scripts/test.sh
   ```

4. Update docs when behavior/configuration changes

PR expectations:

- Keep PRs focused
- Use descriptive commit messages
- Ensure CI passes

## Production Image and Deployment

This repository keeps a production Docker image workflow:

- Production build definition: `Dockerfile`
- Publish pipeline: `.github/workflows/docker-publish.yml`
- Deployment example: `docker-compose.yml`

Contributors should not use production compose files as the day-to-day development environment.
