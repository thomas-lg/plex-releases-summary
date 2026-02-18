# Plex Releases Summary

A lightweight Docker container that fetches recently added media from your Plex server via Tautulli and sends summaries to Discord. Perfect for automated weekly notifications of new movies, TV shows, and music added to your media library.

> **🚀 Unraid Users:** Jump to [Unraid Quick Start](#unraid-quick-start) - just download the XML template and configure 2 settings!

## Table of Contents

- [Plex Releases Summary](#plex-releases-summary)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Unraid Quick Start](#unraid-quick-start)
  - [Execution Modes](#execution-modes)
    - [📅 Scheduled Mode (Default)](#-scheduled-mode-default)
    - [▶️ One-Shot Mode](#️-one-shot-mode)
  - [Configuration](#configuration)
    - [Available Configuration](#available-configuration)
  - [PUID/PGID Configuration](#puidpgid-configuration)
  - [Example Output](#example-output)
  - [Discord Notifications](#discord-notifications)
  - [Development](#development)
    - [For Contributors](#for-contributors)
    - [Project Structure](#project-structure)
  - [Docker Images](#docker-images)
  - [Deployment Options](#deployment-options)
  - [Operational Notes](#operational-notes)
    - [Health Monitoring](#health-monitoring)
  - [Troubleshooting](#troubleshooting)
  - [Security](#security)
    - [Credentials](#credentials)
    - [Container Security](#container-security)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## Features

- 📅 **Scheduled execution** with CRON-like timing (runs as daemon)
- ▶️ **One-shot mode** for external cron jobs or manual runs (`RUN_ONCE=true`)
- 📺 Fetches recently added movies, TV shows, episodes, music, and more
- 🎯 Configurable time range (e.g., last 7 days)
- 💬 **Optional Discord notifications** with rich embed formatting
- 🐳 Docker-ready with minimal footprint
- 📊 Clean, formatted output with media type detection
- ⚡ Graceful shutdown handling for containerized environments

## Prerequisites

- [Tautulli](https://tautulli.com/) v2.1.0+ with API enabled
- Tautulli API key (Settings → Web Interface → API)
- Docker or Docker Compose

> **Timezone:** Container defaults to UTC. Set `TZ` environment variable for local timezone (e.g., `TZ=America/New_York`).

## Quick Start

Minimal configuration required - just 2 fields!

1. **Clone the repository:**

```bash
git clone https://github.com/thomas-lg/plex-releases-summary.git
cd plex-releases-summary
```

2. **Create Tautulli API key secret:**

```bash
mkdir -p secrets
echo "your_tautulli_api_key" > secrets/tautulli_key
```

3. **Update docker-compose.yml:**
   - Mount the secrets directory into the container (example: `./secrets:/run/secrets:ro`)
   - Set `TAUTULLI_URL` to your Tautulli server URL (e.g., `http://tautulli:8181` or `http://192.168.1.100:8181`)
   - Set `TAUTULLI_API_KEY=/run/secrets/tautulli_key` to read the secret from the mounted path

4. **Run the container:**

```bash
docker compose up
```

That's it! On first run, the entrypoint automatically creates `config.yml` from the template with environment variable references. The application will run weekly on Sundays at 4 PM UTC by default.

> **Container path contract (Docker):** Keep container-side targets fixed and customize only host-side paths.
> - Config: `/app/configs/config.yml`
> - Logs: `/app/logs`
> - Examples: `./my-configs:/app/configs`, `./my-logs:/app/logs`

> **For advanced configuration options**, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md#optional-field-overrides)

## Unraid Quick Start

**🚀 Unraid users:** Installation is super simple! Just download the XML template and you're ready to go:

1. **Get the template:** Download [my-plex-releases-summary.xml](my-plex-releases-summary.xml)

2. **Add to Unraid:**
   - Copy to: `/boot/config/plugins/dockerMan/templates-user/my-plex-releases-summary.xml`
   - Refresh Docker tab in Unraid UI

3. **Configure (just 2 settings!):**
   - **Add Container** → Select "my-plex-releases-summary"
   - Set **TAUTULLI_URL**: `http://tautulli:8181` (your Tautulli container)
   - Set **TAUTULLI_API_KEY**: Your Tautulli API key (find in Tautulli: Settings → Web Interface → API)
   - Click **Apply**

**Done!** Everything else is automatic - appdata, config, weekly schedule (Sundays 4 PM), PUID/PGID (99/100).

## Execution Modes

The application supports two execution modes:

### 📅 Scheduled Mode (Default)

Runs on schedule (default: Sundays at 4 PM). Container stays running. See [CRON examples](docs/CONFIGURATION.md#optional-field-overrides) for customization.

### ▶️ One-Shot Mode

Run once and exit. Set `RUN_ONCE=true`. See [examples](docs/CONFIGURATION.md#examples).

## Configuration

**Only 2 fields are required:** `tautulli_url` and `tautulli_api_key`. All other fields have working defaults.

### Available Configuration

| Field                  | Required | Default        | Description                 |
| ---------------------- | -------- | -------------- | --------------------------- |
| **`tautulli_url`**     | ✅ Yes   | -              | Tautulli server URL         |
| **`tautulli_api_key`** | ✅ Yes   | -              | Tautulli API key            |
| `days_back`            | No       | `7`            | Days to look back           |
| `cron_schedule`        | No       | `0 16 * * SUN` | CRON schedule (Sunday 4 PM) |
| `discord_webhook_url`  | No       | None           | Discord webhook (optional)  |
| `run_once`             | No       | `false`        | One-shot mode               |
| `log_level`            | No       | `INFO`         | Logging level               |
| Other fields           | No       | See docs       | See full reference          |

> **📖 For complete configuration documentation**, including configuration methods, Docker secrets, all fields, troubleshooting, and examples, see **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)**

## PUID/PGID Configuration

Control file ownership via PUID/PGID environment variables. Defaults: `99`/`100` (Unraid compatible).

**Find your IDs:** `id` command shows `uid=1000 gid=1000`

**Example:**

```yaml
environment:
  - PUID=1000
  - PGID=1000
```

**Notes:**

- Rejects root (UID/GID 0) for security
- Entrypoint drops privileges before running app
- Permission errors? Check [Configuration Troubleshooting](docs/CONFIGURATION.md#troubleshooting)

## Example Output

```
2026-02-15 10:00:15 - INFO - 🚀 Plex weekly summary starting
2026-02-15 10:00:15 - INFO - Configuration: Looking back 7 days
2026-02-15 10:00:15 - INFO - Querying recently added items...
2026-02-15 10:00:16 - INFO - Retrieved 45 items, filtered to 23 items from last 7 days
2026-02-15 10:00:16 - INFO - Found 23 recent items matching criteria
2026-02-15 10:00:16 - INFO - ➕ The Last of Us - S01E03 - Long, Long Time | added: 2026-02-12 14:23
2026-02-15 10:00:16 - INFO - ➕ Everything Everywhere All at Once (2022) | added: 2026-02-13 20:15
2026-02-15 10:00:16 - INFO - ➕ Succession - S04E01 - The Munsters | added: 2026-02-14 18:45
```

> **About "iteration" logs:** You may see logs like "iteration 1, 2, 3...". This is normal behavior. See [Iteration Logs](docs/CONFIGURATION.md#minimal-configuration) for explanation.

## Discord Notifications

Send release summaries to Discord with rich embeds.

**Quick Setup:**

1. Create webhook: Server Settings → Integrations → Webhooks ([Discord guide](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks))
2. Create secret: `echo "webhook-url" > secrets/discord_webhook`
3. Set: `DISCORD_WEBHOOK_URL=/run/secrets/discord_webhook`

**Features:** Rich embeds, grouped media, clickable Plex links, auto-retry. See [Discord Configuration](docs/CONFIGURATION.md#discord-embed-limits) for details.

**Troubleshooting:** Not receiving notifications? See [Discord Troubleshooting](docs/CONFIGURATION.md#discord-notifications-not-sending).

## Development

### For Contributors

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development setup, code style guidelines, testing, and contribution process.

**Quick Start:**

```bash
# Clone repository
git clone https://github.com/thomas-lg/plex-releases-summary.git
cd plex-releases-summary

# Start development with hot-reload (recommended)
./scripts/dev.sh

# OR: Run tests
./scripts/test.sh

# OR: Start production mode
./scripts/start.sh
```

**Helper Scripts:**

All scripts are located in the `scripts/` directory. See [scripts/README.md](scripts/README.md) for full documentation.

```bash
./scripts/dev.sh       # Start development with hot-reload
./scripts/start.sh     # Start production mode
./scripts/test.sh      # Run tests with coverage
./scripts/logs.sh      # View logs (prod/dev/test)
./scripts/stop.sh      # Stop all containers
./scripts/clean.sh     # Clean up caches and Docker resources
```

**Development Setup (Manual):**

```bash
# Option 1: Docker development with hot-reload
cp docker-compose.dev.local.yml.example docker-compose.dev.local.yml
# Edit docker-compose.dev.local.yml with your settings
docker-compose -f docker-compose.dev.yml -f docker-compose.dev.local.yml up

# Option 2: Local Python development
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt -r requirements-test.txt
cp configs/config.yml configs/config-dev.yml
# Edit configs/config-dev.yml with your settings
cd src && python app.py
```

**Running Tests:**

```bash
# Using helper script (recommended - uses Docker)
./scripts/test.sh                           # Run all tests
./scripts/test.sh tests/test_config.py      # Run specific test file
./scripts/test.sh -k "test_config"          # Run tests matching pattern

# Using docker-compose directly
docker-compose -f docker-compose.test.yml run --rm test

# Using local Python environment (requires dependencies installed)
PYTHONPATH=src pytest --cov=src             # Run tests locally
PYTHONPATH=src black src/ tests/            # Format code locally
PYTHONPATH=src ruff check src/ tests/       # Lint locally
PYTHONPATH=src mypy src/                    # Type check locally
```

### Project Structure

```
.
├── src/
│ ├── app.py # Main application logic
│ ├── config.py # Configuration loader and validator
│ ├── scheduler.py # APScheduler daemon mode
│ ├── tautulli_client.py # Tautulli API client
│ ├── discord_client.py # Discord webhook client
│ └── logging_config.py # Logging configuration
├── tests/ # Test suite
│ ├── test_config.py # Configuration tests
│ ├── test_app.py # App logic tests
│ ├── test_discord_client.py # Discord tests
│ └── test_discord_markdown.py # Markdown escaping tests
├── scripts/ # Helper scripts
│ ├── dev.sh # Start development mode
│ ├── start.sh # Start production mode
│ ├── test.sh # Run tests
│ ├── logs.sh # View logs
│ ├── stop.sh # Stop all containers
│ ├── clean.sh # Clean up caches
│ └── [README.md](scripts/README.md) # Scripts documentation
├── configs/
│ ├── [config.yml](configs/config.yml) # User configuration file
│ └── [config-dev.yml](configs/config-dev.yml) # Development configuration
├── docs/
│ └── [CONFIGURATION.md](docs/CONFIGURATION.md) # Complete configuration reference
├── .github/
│ └── workflows/ # CI/CD pipelines
├── assets/ # Project assets (screenshots, etc.)
├── [Dockerfile](Dockerfile) # Production Docker image
├── [Dockerfile.dev](Dockerfile.dev) # Development Docker image
├── [Dockerfile.test](Dockerfile.test) # Test Docker image
├── [docker-compose.yml](docker-compose.yml) # Production compose config
├── [docker-compose.dev.yml](docker-compose.dev.yml) # Development compose config
├── [docker-compose.dev.local.yml.example](docker-compose.dev.local.yml.example) # Example local overrides
├── [docker-compose.test.yml](docker-compose.test.yml) # Test compose config
├── entrypoint.sh # Container entrypoint script
├── requirements.txt # Python dependencies
├── requirements-dev.txt # Development dependencies
├── requirements-test.txt # Testing dependencies
├── pyproject.toml # Python project configuration
├── pytest.ini # Pytest configuration
├── .pre-commit-config.yaml # Pre-commit hooks
├── my-plex-releases-summary.xml # Unraid template
├── [CONTRIBUTING.md](CONTRIBUTING.md) # Contribution guidelines
└── README.md

```

## Docker Images

Pre-built images available: `ghcr.io/thomas-lg/plex-releases-summary`

Tags: `latest` (stable), `vX.Y.Z` (specific versions), `sha-<commit>` (commit builds)

```bash
docker pull ghcr.io/thomas-lg/plex-releases-summary:latest
```

## Deployment Options

See [docker-compose.yml](docker-compose.yml) for minimal production setup or [docs/CONFIGURATION.md](docs/CONFIGURATION.md#examples) for advanced configurations.

## Operational Notes

- **Restart:** Safe anytime. Missed schedules don't run retroactively. See [Scheduler Behavior](docs/CONFIGURATION.md#scheduler-behavior).
- **Shutdown:** Handles `SIGTERM`/`SIGINT` cleanly.
- **Upgrades:** Pull new image, restart. See [Migration Guide](docs/CONFIGURATION.md#migration-and-updates).
- **Exit codes:** `0` (success), `1` (error), `130` (interrupted). See [Exit Codes](docs/CONFIGURATION.md#exit-codes).
- **Persistent logs:** Rotating log files are stored in host `./logs` (`5 MB` each, `5` backups + current), while `docker logs` remains available.

### Health Monitoring

Monitor using exit codes or process checks:

```dockerfile
# Process monitoring
HEALTHCHECK CMD pgrep -f "python.*app.py" || exit 1

# One-shot mode - check exit code
docker run --rm plex-releases-summary; [ $? -eq 0 ] || alert

# Scheduled mode - check logs
docker logs container --since 24h | grep -q "Job executed successfully"
```

External tools: Uptime Kuma, Prometheus/Grafana, Healthchecks.io. See [Exit Codes](docs/CONFIGURATION.md#exit-codes) for monitoring integration.

## Troubleshooting

Common issues:

- **Connection errors**: Check Tautulli URL/API key and accessibility
- **No items**: Increase `days_back` or verify media timing
- **Config not working**: Verify environment variables in docker-compose.yml
- **"iteration 1, 2..." logs**: Normal - see [Iteration Logs](docs/CONFIGURATION.md#minimal-configuration)

Enable debug: Set `LOG_LEVEL=DEBUG` in docker-compose.yml

See [Configuration Troubleshooting](docs/CONFIGURATION.md#troubleshooting) for comprehensive guidance.

## Security

### Credentials

Never commit credentials. Use file-based secrets: mount secrets directory and set `TAUTULLI_API_KEY=/run/secrets/tautulli_key`. Application auto-reads files starting with `/`. See [Docker Secrets](docs/CONFIGURATION.md#docker-secrets) for detailed setup.

### Container Security

- **Privilege dropping**: Starts as root for permissions, drops to `appuser` (UID 99) via `gosu`
- **PUID/PGID validation**: Rejects UID/GID 0, warns about shared UIDs (100, 1000)
- **Best practices**: Use `:ro` mounts, isolated networks, Docker secrets. See [Dockerfile](Dockerfile) SECURITY NOTE.

## License

MIT License - see [LICENSE](LICENSE) file.

## Acknowledgments

- [Tautulli](https://tautulli.com/) - Plex monitoring tool
- [Plex](https://www.plex.tv/) - Media server platform

---

Made with ❤️ for the Plex community
