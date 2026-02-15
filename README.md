# Plex Releases Summary

A lightweight Docker container that fetches recently added media from your Plex server via Tautulli and sends summaries to Discord. Perfect for automated weekly notifications of new movies, TV shows, and music added to your media library.

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

- [Tautulli](https://tautulli.com/) v2.1.0 or later (v2.5.0+ recommended)
  - Installed and configured with your Plex server
  - API access must be enabled (enabled by default)
- Tautulli API key (found in Tautulli → Settings → Web Interface → API)
- Docker or Docker Compose

> **Tautulli Compatibility Note:** This project uses the [`get_recently_added`](https://github.com/Tautulli/Tautulli/wiki/Tautulli-API-Reference#get_recently_added) and [`get_server_identity`](https://github.com/Tautulli/Tautulli/wiki/Tautulli-API-Reference#get_server_identity) Tautulli API endpoints. These have been stable core API features since Tautulli v2.0.0 (December 2017). Any reasonably current Tautulli installation should be fully compatible. For best results, use Tautulli v2.5.0 or later which includes Python 3 support and improved stability.

> **Timezone Note:** Container defaults to UTC for CRON schedules. To use your local timezone, set the `TZ` environment variable (e.g., `TZ=America/New_York`). The default schedule `0 16 * * SUN` runs Sundays at 4 PM in the configured timezone. Use [crontab.guru](https://crontab.guru) for schedule validation.

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
   - Set `TAUTULLI_URL` to your Tautulli server URL (e.g., `http://tautulli:8181` or `http://192.168.1.100:8181`)
   - Verify `TAUTULLI_API_KEY=/app/secrets/tautulli_key` points to the secret file created above

4. **Run the container:**

```bash
docker compose up
```

That's it! On first run, the entrypoint automatically creates `config.yml` from the template with environment variable references. The application will run weekly on Sundays at 4 PM UTC by default.

> **For advanced configuration options**, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md#optional-field-overrides)

## Execution Modes

The application supports two execution modes:

### 📅 Scheduled Mode (Default)

Runs automatically on a schedule (default: Sundays at 4 PM). The container stays running and executes on schedule.

Using docker-compose.yml as-is runs in this mode with sensible defaults.

To customize the schedule, see [CRON schedule examples](docs/CONFIGURATION.md#optional-field-overrides) in the configuration guide.

**Graceful Shutdown:** The scheduler handles `SIGTERM` and `SIGINT` signals gracefully.

### ▶️ One-Shot Mode

Run once and exit. Ideal for external cron jobs or manual execution.

```bash
docker run --rm \
  -e TAUTULLI_URL=http://tautulli:8181 \
  -e TAUTULLI_API_KEY=your-api-key \
  -e RUN_ONCE=true \
  -v $(pwd)/configs:/app/configs:ro \
  ghcr.io/thomas-lg/plex-releases-summary:latest
```

For more execution mode examples, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md#examples).

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

## Example Output

```
2025-03-17 10:00:15 - INFO - 🚀 Plex weekly summary starting
2025-03-17 10:00:15 - INFO - Configuration: Looking back 7 days
2025-03-17 10:00:15 - INFO - Querying recently added items...
2025-03-17 10:00:16 - INFO - Retrieved 45 items, filtered to 23 items from last 7 days
2025-03-17 10:00:16 - INFO - Found 23 recent items matching criteria
2025-03-17 10:00:16 - INFO - ➕ The Last of Us - S01E03 - Long, Long Time | added: 2025-03-13 14:23
2025-03-17 10:00:16 - INFO - ➕ Everything Everywhere All at Once (2022) | added: 2025-03-15 20:15
2025-03-17 10:00:16 - INFO - ➕ Succession - S04E01 - The Munsters | added: 2025-03-14 18:45
```

> **About "iteration" logs:** You may see logs like "iteration 1, 2, 3...". This is normal - the application uses client-side filtering to work around Tautulli API date filtering limitations, fetching items in batches until all matches are found.

## Discord Notifications

Optionally send release summaries to Discord with rich embeds showing all new media grouped by type.

**Quick Setup:**

1. Create webhook in Discord: Server Settings → Integrations → Webhooks → New Webhook ([Discord guide](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks))
2. Create secret file: `echo "your-webhook-url" > secrets/discord_webhook`
3. Set in docker-compose.yml: `DISCORD_WEBHOOK_URL=/app/secrets/discord_webhook`

**Features:**

- Rich embeds with media grouped by type (Movies, TV Shows, Music)
- Clickable links to Plex Web (Server ID auto-detected from Tautulli when Discord enabled)
- Automatic rate limiting and retry logic with exponential backoff
- Smart character limit handling (6000 chars/embed, 1024/field, 25 fields max)
- Optional - disabled by default

For detailed Discord configuration and message format, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md#examples).

## Development

### Local Development Setup

1. Clone and install dependencies:

```bash
git clone https://github.com/thomas-lg/plex-releases-summary.git
cd plex-releases-summary
```

2. Update configuration file:

```bash
nano configs/config.yml
# For development, set RUN_ONCE=true and log_level: DEBUG in docker-compose.dev.local.yml
```

3. (Optional) Create local overrides for custom network or other settings:

```bash
cp docker-compose.dev.local.yml.example docker-compose.dev.local.yml
# Edit with your custom configuration (e.g., add custom networks)
```

4. Run in development mode (with hot-reload):

```bash
# Without local overrides
docker compose -f docker-compose.dev.yml up --build

# With local overrides
docker compose -f docker-compose.dev.yml -f docker-compose.dev.local.yml up --build
```

**Note**: `docker-compose.dev.local.yml` is gitignored for personal customizations like custom Docker networks or volume mounts.

### Project Structure

```
.
├── src/
│   ├── app.py              # Main application logic
│   ├── tautulli_client.py  # Tautulli API client
│   ├── discord_client.py   # Discord webhook client
│   └── logging_config.py   # Logging configuration
├── Dockerfile              # Production Docker image
├── docker-compose.yml      # Production compose config
├── docker-compose.dev.yml  # Development compose config
├── docker-compose.dev.local.yml.example  # Example local overrides
├── requirements.txt        # Python dependencies
└── README.md
```

## Building from Source

```bash
# Build the image
docker build -t plex-releases-summary:latest .

# Run locally
docker run --rm \
  -v $(pwd)/configs:/app/configs:ro \
  plex-releases-summary:latest
```

## Docker Images

Pre-built images are available on GitHub Container Registry:

```bash
# Latest version
docker pull ghcr.io/thomas-lg/plex-releases-summary:latest

# Specific version
docker pull ghcr.io/thomas-lg/plex-releases-summary:v1.0.0
```

### Available Tags

- `latest` - Latest stable release from main branch
- `vX.Y.Z` - Specific semantic version releases
- `sha-<commit>` - Specific commit builds

## Unraid Installation

Unraid users can easily install and configure this application with volume mapping for easy config editing.

The Unraid template already handles auto-creating config.yml on first run. See [my-plex-releases-summary.xml](my-plex-releases-summary.xml) for the template details.

### Setup Instructions

1. **Create appdata directory** on your Unraid server:

   ```bash
   mkdir -p /mnt/user/appdata/plex-releases-summary
   ```

2. **Copy configuration file** to appdata:

   ```bash
   cd /mnt/user/appdata/plex-releases-summary
   # Download config.yml from the repository
   wget https://raw.githubusercontent.com/thomas-lg/plex-releases-summary/main/configs/config.yml -O config.yml
   ```

   The default `config.yml` comes pre-configured with environment variable references. You don't need to edit it for typical use.

3. **Install via Docker** (or Community Applications):
   - **Repository**: `ghcr.io/thomas-lg/plex-releases-summary:latest`
   - **Volume mapping**: `/mnt/user/appdata/plex-releases-summary:/app/configs`
   - **Restart policy**: `on-failure`
   - **Network**: `bridge` or your custom network

4. **Configure required environment variables:**
   - `TAUTULLI_URL` = `http://tautulli:8181` (required)
   - `TAUTULLI_API_KEY` = `your-api-key` (required)
   - Optional: See [docs/CONFIGURATION.md](docs/CONFIGURATION.md#optional-field-overrides) for additional environment variables

### Editing Configuration on Unraid

Your configuration file is accessible via the Unraid webUI if you need to customize it:

1. Go to **Shares** → **appdata** → **plex-releases-summary**
2. Edit `config.yml` with the built-in editor or via SMB share
3. Restart the container for changes to take effect

**Example appdata structure:**

```
/mnt/user/appdata/plex-releases-summary/
└── config.yml  (your configuration file)
```

### Unraid Template (Community Applications)

An Unraid template file is provided at [my-plex-releases-summary.xml](my-plex-releases-summary.xml).

## Deployment Options

See [docker-compose.yml](docker-compose.yml) for the minimal production configuration. For additional deployment examples and advanced configurations, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md#examples).

## Operational Notes

- **Container restart:** Safe to restart anytime. Scheduler persists across restarts, missed schedules don't execute retroactively.
- **Graceful shutdown:** Handles `SIGTERM`/`SIGINT` signals cleanly (e.g., `docker compose down`).
- **Upgrades:** Pull new image, restart container. Config format is stable.

## Troubleshooting

**Common Issues:**

- **Connection errors**: Verify Tautulli URL/API key, ensure Tautulli is running and accessible
- **No items found**: Check media was added in time range, increase `days_back` to test
- **Configuration not working**: Ensure environment variable is set in docker-compose.yml (config.yml already has `${VAR}` placeholders)
- **Empty env var warnings**: These indicate env vars set to empty strings. Either unset them or provide values.
- **"iteration 1, 2, 3..." logs**: Normal behavior. The app fetches data in batches using client-side filtering.
- **Validation errors**: Check field types (e.g., `days_back` must be integer ≥1, `log_level` must be DEBUG/INFO/WARNING/ERROR/CRITICAL)
- **Docker networking**: Ensure containers can communicate (use Docker network or `host.docker.internal` on Docker Desktop)

**Enable debug logging:**

```yaml
# docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG
```

For comprehensive troubleshooting and solutions, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md#troubleshooting).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Tautulli](https://tautulli.com/) - Monitoring and tracking tool for Plex Media Server
- [Plex](https://www.plex.tv/) - Media server platform

## Security

**Important**: Never commit your `config.yml` file with real credentials or expose your Tautulli API key. If you accidentally commit secrets, rotate your Tautulli API key immediately.

**Recommended**: Use file-based secrets for sensitive values. Mount a secrets directory and point environment variables to files (e.g., `TAUTULLI_API_KEY=/app/secrets/tautulli_key`). The application automatically reads file contents for any path starting with `/`. For development, you can hardcode values directly in docker-compose.yml.

---

Made with ❤️ for the Plex community
