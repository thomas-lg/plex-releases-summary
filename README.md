# Plex Releases Summary

<p align="center">
  <img src="assets/plex_releases_summary.png" alt="Plex Releases Summary logo" width="180"/>
</p>

<p align="center">
  <a href="https://github.com/thomas-lg/plex-releases-summary/actions/workflows/quality-and-tests.yml"><img src="https://github.com/thomas-lg/plex-releases-summary/actions/workflows/quality-and-tests.yml/badge.svg" alt="Quality and Tests"/></a>
  <a href="https://github.com/thomas-lg/plex-releases-summary/actions/workflows/docker-publish.yml"><img src="https://github.com/thomas-lg/plex-releases-summary/actions/workflows/docker-publish.yml/badge.svg" alt="Docker Build and Release"/></a>
  <a href="https://codecov.io/gh/thomas-lg/plex-releases-summary"><img src="https://codecov.io/gh/thomas-lg/plex-releases-summary/branch/main/graph/badge.svg" alt="Coverage"/></a>
  <a href="https://github.com/thomas-lg/plex-releases-summary/releases/latest"><img src="https://img.shields.io/github/v/release/thomas-lg/plex-releases-summary" alt="Latest Release"/></a>
  <a href="https://ghcr.io/thomas-lg/plex-releases-summary"><img src="https://img.shields.io/badge/docker-ghcr.io-blue?logo=docker" alt="Docker Image"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12+-3776ab?logo=python&logoColor=white" alt="Python 3.12+"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"/></a>
</p>

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
    - [Scheduled Mode (Default)](#scheduled-mode-default)
    - [One-Shot Mode](#one-shot-mode)
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
- 💬 **Optional Discord notifications** with rich embed formatting (including friendly "nothing new" updates)
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

**Clone the repository:**

```bash
git clone https://github.com/thomas-lg/plex-releases-summary.git
cd plex-releases-summary
```

**Create Tautulli API key secret:**

```bash
mkdir -p secrets
echo "your_tautulli_api_key" > secrets/tautulli_api_key
```

**Update docker-compose.yml:**

- Mount the secrets directory into the container (example: `./secrets:/run/secrets:ro`)
- Set `TAUTULLI_URL` to your Tautulli server URL (e.g., `http://tautulli:8181` or `http://192.168.1.100:8181`)
- Set `TAUTULLI_API_KEY=/run/secrets/tautulli_api_key` to read the secret from the mounted path

**Run the container:**

```bash
docker compose up
```

That's it! On first run, the entrypoint automatically creates `config.yml` from the template with environment variable references. The application will run weekly on Sundays at 4 PM UTC by default.

> **Container path contract (Docker):** Keep container-side targets fixed and customize only host-side paths.
>
> - Config: `/app/configs/config.yml`
> - Logs: `/app/logs`
> - Examples: `./my-configs:/app/configs`, `./my-logs:/app/logs`
>   **For advanced configuration options**, see [CONFIGURATION.md](CONFIGURATION.md#environment-variable-behavior)

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

### Scheduled Mode (Default)

Runs on schedule (default: Sundays at 4 PM). Container stays running. See [Configuration Fields](CONFIGURATION.md#configuration-fields) for schedule customization.

### One-Shot Mode

Run once and exit. Set `RUN_ONCE=true`. See [examples](CONFIGURATION.md#examples).

## Configuration

**Only 2 fields are required:** `tautulli_url` and `tautulli_api_key`. All other fields are optional and use the defaults shown below.

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

> **📖 For complete configuration documentation**, including configuration methods, Docker secrets, all fields, troubleshooting, and examples, see **[CONFIGURATION.md](CONFIGURATION.md)**

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
- Permission errors? Check [Configuration Troubleshooting](CONFIGURATION.md#troubleshooting)

## Example Output

```text
2026-02-15 10:00:15 | INFO    | app | 🚀 Plex weekly summary starting
2026-02-15 10:00:15 | INFO    | app | Configuration: Looking back 7 days
2026-02-15 10:00:15 | INFO    | app | Querying recently added items with iterative fetching...
2026-02-15 10:00:16 | INFO    | app | Retrieved 45 items, filtered to 23 items from last 7 days
2026-02-15 10:00:16 | INFO    | app | Found 23 recent items matching criteria
2026-02-15 10:00:16 | INFO    | app | ➕ The Last of Us - S01E03 - Long, Long Time | added: 2026-02-12 14:23
2026-02-15 10:00:16 | INFO    | app | ➕ Everything Everywhere All at Once (2022) | added: 2026-02-13 20:15
2026-02-15 10:00:16 | INFO    | app | ➕ Succession - S04E01 - The Munsters | added: 2026-02-14 18:45
```

> **About "iteration" logs:** You may see logs like "iteration 1, 2, 3...". This is normal behavior. Iterative fetch has safety guardrails to avoid runaway loops. See [Iteration Logs](CONFIGURATION.md#minimal-configuration) for details.

## Discord Notifications

Send release summaries to Discord with rich embeds.

**Quick Setup:**

1. Create webhook: Server Settings → Integrations → Webhooks ([Discord guide](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks))
2. Create secret: `echo "webhook-url" > secrets/discord_webhook`
3. Set: `DISCORD_WEBHOOK_URL=/run/secrets/discord_webhook`

**Features:**

- Rich embeds grouped by media category with clickable Plex links
- Auto-retry with rate-limit handling
- When no items are found in the selected period, sends a friendly "nothing new" embed
- Empty-period embed message is randomized from a built-in set to keep updates fresh

See [Discord Notification Notes](CONFIGURATION.md#discord-notification-notes) for details.

**Troubleshooting:** Not receiving notifications? See [Discord Troubleshooting](CONFIGURATION.md#discord-notifications-not-sending).

## Development

### For Contributors

Contributor setup and all development commands are documented in [CONTRIBUTING.md](CONTRIBUTING.md).

Use the devcontainer for day-to-day work:

```text
Command Palette → Dev Containers: Reopen in Container
```

If Dev Containers is not available, use the same dev environment via Docker Compose:

```bash
docker compose -f docker-compose.dev.yml up -d --build
docker compose -f docker-compose.dev.yml exec app bash
# or:
./scripts/dev-shell.sh
```

Then run contributor checks:

```bash
./scripts/format.sh
./scripts/typecheck.sh
./scripts/test.sh
```

To run the app locally (devcontainer or optional host-native workflow):

```bash
cp .env.example .env
# Edit .env with your Tautulli values
./scripts/start.sh
```

Script reference: [scripts/README.md](scripts/README.md)

### Project Structure

```text
.
├── src/
│ ├── app.py # Main application logic
│ ├── config.py # Configuration loader and validator
│ ├── discord_client.py # Discord webhook client
│ ├── logging_config.py # Logging configuration
│ ├── scheduler.py # APScheduler daemon mode
│ └── tautulli_client.py # Tautulli API client
├── tests/ # Test suite
│ ├── test_app.py # App logic tests
│ ├── test_config.py # Configuration tests
│ ├── test_discord_client.py # Discord tests
│ ├── test_discord_markdown.py # Markdown escaping tests
│ ├── test_logging_config.py # Logging config tests
│ ├── test_scheduler.py # Scheduler tests
│ └── test_tautulli_client.py # Tautulli client tests
├── scripts/ # Helper scripts
│ ├── clean.sh # Clean up caches
│ ├── dev-shell.sh # Enter dev compose shell
│ ├── format.sh # Format Python code
│ ├── README.md # Scripts documentation
│ ├── test.sh # Run tests
│ └── typecheck.sh # Type-check with mypy
├── configs/
│ └── config.yml # User configuration file
├── CONFIGURATION.md # Complete configuration reference
├── .devcontainer/
│ ├── Dockerfile.dev # Devcontainer image
│ └── devcontainer.json # Devcontainer definition
├── .github/
│ └── workflows/ # CI/CD pipelines
├── assets/ # Project assets (screenshots, etc.)
├── CONTRIBUTING.md # Contribution guidelines
├── Dockerfile # Production Docker image
├── docker-compose.dev.yml # Development compose config
├── docker-compose.yml # Production compose config
├── entrypoint.sh # Container entrypoint script
├── my-plex-releases-summary.xml # Unraid template
├── pyproject.toml # Python project configuration
├── requirements-dev.txt # Development dependencies
├── requirements-test.txt # Testing dependencies
├── requirements.txt # Python dependencies
└── README.md

```

## Docker Images

Pre-built images available: `ghcr.io/thomas-lg/plex-releases-summary`

Tags: `latest` (stable), `vX.Y.Z` (specific versions), `sha-<commit>` (commit builds)

```bash
docker pull ghcr.io/thomas-lg/plex-releases-summary:latest
```

## Deployment Options

See [docker-compose.yml](docker-compose.yml) for minimal production setup or [CONFIGURATION.md](CONFIGURATION.md#examples) for advanced configurations.

## Operational Notes

- **Restart:** Safe anytime. Missed schedules don't run retroactively. See [Scheduler Behavior](CONFIGURATION.md#scheduler-behavior).
- **Shutdown:** Handles `SIGTERM`/`SIGINT` cleanly.
- **Upgrades:** Pull new image, restart. See [Migration Guide](CONFIGURATION.md#migration-and-updates).
- **Exit codes:** `0` (success), `1` (error), `130` (interrupted). See [Exit Codes](CONFIGURATION.md#exit-codes).
- **Persistent logs:** Rotating log files are stored in host `./logs` (`5 MB` each, `5` backups + current), while `docker logs` remains available.

### Health Monitoring

Monitor using exit codes or process checks:

```dockerfile
# Process monitoring
HEALTHCHECK CMD pgrep -f "python.*app.py" || exit 1

# One-shot mode - check exit code
docker run --rm plex-releases-summary; [ $? -eq 0 ] || alert

# Scheduled mode - check logs for successful summary completion
docker logs container --since 24h | grep -q "✅ Summary complete"
```

External tools: Uptime Kuma, Prometheus/Grafana, Healthchecks.io. See [Exit Codes](CONFIGURATION.md#exit-codes) for monitoring integration.

## Troubleshooting

Common issues:

- **Connection errors**: Check Tautulli URL/API key and accessibility
- **No items**: Increase `days_back` or verify media timing
- **Config not working**: Verify environment variables in your deployment environment file (example: `docker-compose.yml`)
- **"iteration 1, 2..." logs**: Normal - see [Iteration Logs](CONFIGURATION.md#minimal-configuration)

Enable debug: Set `LOG_LEVEL=DEBUG` in your deployment environment file (example: `docker-compose.yml`)

See [Configuration Troubleshooting](CONFIGURATION.md#troubleshooting) for comprehensive guidance.

## Security

### Credentials

Never commit credentials. Use file-based secrets: mount secrets directory and set `TAUTULLI_API_KEY=/run/secrets/tautulli_api_key`. Application auto-reads files starting with `/`, and required secret files fail fast if missing, unreadable, or empty. See [Docker Secrets](CONFIGURATION.md#docker-secrets) for detailed setup.

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
