# Scripts Directory

These scripts are thin wrappers for contributor workflows and are intended to run inside the devcontainer.

## Available Scripts

### 🧪 `test.sh` - Run Tests

Run pytest with coverage.

```bash
./scripts/test.sh                           # Run default test suite + coverage
./scripts/test.sh tests/test_config.py      # Run specific test file
./scripts/test.sh -k "test_config"          # Run tests matching pattern
```

### 🎨 `format.sh` - Format and Lint

Run Black and Ruff.

```bash
./scripts/format.sh                          # Black + Ruff --fix (default: src tests)
./scripts/format.sh src                      # Format/lint src only
./scripts/format.sh --check src tests        # Check mode (no writes)
```

### 🧠 `typecheck.sh` - Type Checking

Run mypy.

```bash
./scripts/typecheck.sh                       # Type check default target: src
./scripts/typecheck.sh src                   # Type check src explicitly
./scripts/typecheck.sh src/config.py         # Type check specific file
```

### 🧹 `clean.sh` - Clean Local Artifacts

Remove generated test/coverage/cache files.

```bash
./scripts/clean.sh
```

## Quick Reference

| Task       | Command                |
| ---------- | ---------------------- |
| Run tests  | `./scripts/test.sh`    |
| Format     | `./scripts/format.sh`  |
| Type check | `./scripts/typecheck.sh` |
| Clean      | `./scripts/clean.sh`   |

## Notes

- For app runtime and deployment, use [docker-compose.yml](../docker-compose.yml) with the published image.
- Contributor setup and daily workflow are documented in [CONTRIBUTING.md](../CONTRIBUTING.md).
