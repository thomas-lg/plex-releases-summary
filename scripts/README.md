# Scripts Directory

This directory contains helper scripts to run the application in different modes.

## Available Scripts

### 🚀 `start.sh` - Production Mode

Start the application in production mode using `docker compose` with `docker-compose.yml`.

```bash
./scripts/start.sh              # Start in foreground
./scripts/start.sh -d           # Start in background (detached)
```

**Requirements:**

- TAUTULLI_URL and TAUTULLI_API_KEY set in `docker-compose.yml`
- Secrets file at `./secrets/tautulli_key` (if using file-based secrets)

---

### 🔧 `dev.sh` - Development Mode

Start the application in development mode with hot-reload enabled.

```bash
./scripts/dev.sh                # Start dev environment
./scripts/dev.sh -d             # Start in background
```

**Features:**

- Auto-creates `docker-compose.dev.local.yml` from example if missing
- Hot-reload on Python file changes
- Uses development configuration

**Requirements:**

- `docker-compose.dev.local.yml` with your settings
- `configs/config-dev.yml` (auto-created if missing)

---

### 🧪 `test.sh` - Run Tests

Run the full test suite in Docker with coverage reports.

```bash
./scripts/test.sh                           # Run all tests
./scripts/test.sh tests/test_config.py      # Run specific test file
./scripts/test.sh -k "test_config"          # Run tests matching pattern
```

**Output:**

- Terminal coverage summary
- HTML coverage report in `htmlcov/index.html`
- XML coverage report in `coverage.xml`

---

### 🎨 `format.sh` - Format + Auto-fix Python Code

Run Black and Ruff in the development container.

```bash
./scripts/format.sh                          # Black format + Ruff --fix (default: src tests)
./scripts/format.sh src                      # Black + Ruff --fix for src only
./scripts/format.sh --check src tests        # Check mode (Black --check + Ruff check)
```

---

### 🧠 `typecheck.sh` - Type Check Python Code

Run mypy in the development container.

```bash
./scripts/typecheck.sh                        # Type check default target: src
./scripts/typecheck.sh src                    # Type check src explicitly
./scripts/typecheck.sh src/config.py          # Type check specific file
```

---

### 📜 `logs.sh` - View Logs

View logs from running containers.

```bash
./scripts/logs.sh                # View production logs (default)
./scripts/logs.sh prod           # View production logs
./scripts/logs.sh dev            # View development logs
./scripts/logs.sh test           # View test logs
./scripts/logs.sh prod --tail 50 # Last 50 lines
```

---

### 🛑 `stop.sh` - Stop All Containers

Stop all running containers for this project.

```bash
./scripts/stop.sh
```

Stops:

- Production containers
- Development containers
- Test containers
- Any containers matching `plex-releases-summary*`

---

### 🧹 `clean.sh` - Clean Up

Remove generated files, caches, and Docker resources.

```bash
./scripts/clean.sh
```

Removes:

- Python caches (`__pycache__`, `.pyc`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`)
- Coverage reports (`htmlcov/`, `.coverage`, `coverage.xml`)
- Stopped Docker containers
- Optionally: unused Docker images

---

## Quick Reference

| Task              | Command              |
| ----------------- | -------------------- |
| Start production  | `./scripts/start.sh` |
| Start development | `./scripts/dev.sh`   |
| Run tests         | `./scripts/test.sh`  |
| Format code       | `./scripts/format.sh`|
| Type check        | `./scripts/typecheck.sh` |
| View logs         | `./scripts/logs.sh`  |
| Stop everything   | `./scripts/stop.sh`  |
| Clean up          | `./scripts/clean.sh` |

## Tips

- **Background mode:** Add `-d` flag to any start command to run in background
- **Follow logs:** Use `./scripts/logs.sh` to view logs from running containers
- **Test specific files:** Pass pytest arguments to `test.sh` (e.g., `./scripts/test.sh tests/test_config.py`)
- **Clean workspace:** Run `./scripts/clean.sh` before committing to remove temporary files

## Environment Setup

### Production

1. Copy secrets: `mkdir -p secrets && echo 'your_key' > secrets/tautulli_key`
2. Edit `docker-compose.yml` to set TAUTULLI_URL
3. Run: `./scripts/start.sh`

### Development

1. Create local config: `cp docker-compose.dev.local.yml.example docker-compose.dev.local.yml`
2. Edit `docker-compose.dev.local.yml` with your settings
3. Run: `./scripts/dev.sh`

### Testing

Just run: `./scripts/test.sh` (no configuration needed)
