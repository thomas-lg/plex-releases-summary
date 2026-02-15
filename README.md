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

> **📝 Tautulli Compatibility Note:** This project uses the `get_recently_added` and `get_server_identity` Tautulli API endpoints. These have been stable core API features since Tautulli v2.0.0 (December 2017). Any reasonably current Tautulli installation should be fully compatible. For best results, use Tautulli v2.5.0 or later which includes Python 3 support and improved stability.

## Quick Start

### Using Docker Compose (Recommended)

1. Clone this repository:

```bash
git clone https://github.com/thomas-lg/plex-releases-summary.git
cd plex-releases-summary
```

2. Create your configuration file:

```bash
cp configs/config.yml.example configs/config.yml
# Edit configs/config.yml with your settings
```

3. Run the container:

```bash
docker compose up
```

## Execution Modes

The application supports two execution modes:

### 📅 Scheduled Mode (Daemon)

Run the container with a CRON schedule to execute summaries automatically at specific times. The container stays running and executes on schedule.

**Docker Compose:**

```yaml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    container_name: plex-releases-summary
    restart: on-failure
    volumes:
      - ./configs:/app/configs:ro
    # Optional: Pass secrets via environment
    # environment:
    #   - TAUTULLI_API_KEY=${TAUTULLI_API_KEY}
```

**Docker CLI:**

```bash
docker run -d \
  --name plex-releases-summary \
  --restart unless-stopped \
  -v $(pwd)/configs:/app/configs:ro \
  ghcr.io/thomas-lg/plex-releases-summary:latest
```

> **Note**: Ensure your `config.yml` has `run_once: false` and `cron_schedule` set for scheduled mode.

**Common CRON Schedule Examples:**

| Schedule                   | CRON Expression   | Description               |
| -------------------------- | ----------------- | ------------------------- |
| Every Sunday at 4:00 PM    | `0 16 * * SUN`    | Weekly summary on Sundays |
| Daily at 9:00 AM           | `0 9 * * *`       | Every day at 9:00 AM      |
| Every Monday at 9:00 AM    | `0 9 * * MON`     | Weekly summary on Mondays |
| Every 6 hours              | `0 */6 * * *`     | Four times per day        |
| First of month at midnight | `0 0 1 * *`       | Monthly summary           |
| Weekdays at 8:00 AM        | `0 8 * * MON-FRI` | Business days only        |

**CRON Format:** `minute hour day month day_of_week`

- `minute`: 0-59
- `hour`: 0-23
- `day`: 1-31
- `month`: 1-12
- `day_of_week`: 0-6 (0=Sunday) or MON, TUE, WED, THU, FRI, SAT, SUN

**Graceful Shutdown:**

The scheduler handles `SIGTERM` and `SIGINT` signals gracefully, making it safe to stop with `docker stop`.

### ▶️ One-Shot Mode

Run once and exit immediately. Ideal for external cron jobs, manual execution, or CI/CD pipelines.

**Docker Compose:**

```yaml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    container_name: plex-releases-summary
    restart: "no"
    volumes:
      - ./configs:/app/configs:ro
```

**Docker CLI:**

```bash
docker run --rm \
  -v $(pwd)/configs:/app/configs:ro \
  ghcr.io/thomas-lg/plex-releases-summary:latest
```

> **Note**: Ensure your `config.yml` has `run_once: true` for one-shot mode.

### External Scheduling with System Cron

For external scheduling using system cron (one-shot mode):

```bash
# Run every Monday at 9:00 AM
0 9 * * 1 docker run --rm -v /path/to/configs:/app/configs:ro ghcr.io/thomas-lg/plex-releases-summary:latest
```

## Configuration

Configuration is managed via a `config.yml` file in the `configs/` directory. This file supports:

- **Static values**: Hardcoded in YAML (e.g., `days_back: 7`)
- **Environment variables**: Interpolation with `${VAR}` syntax
- **Docker secrets**: Environment variables pointing to secret files

### Configuration File

Create `configs/config.yml` from the provided example:

```bash
cp configs/config.yml.example configs/config.yml
```

**Basic example (`configs/config.yml`):**

```yaml
# Tautulli Configuration
tautulli_url: http://tautulli:8181
tautulli_api_key: ${TAUTULLI_API_KEY} # Read from environment

# Core Settings
days_back: 7
cron_schedule: "0 16 * * SUN" # Every Sunday at 4 PM
run_once: false

# Discord (Optional)
# discord_webhook_url: ${DISCORD_WEBHOOK_URL}

# Advanced
log_level: INFO
```

See [configs/config.yml.example](configs/config.yml.example) for detailed documentation and all available options.

### Configuration Reference

| Variable           | Required | Default                | Description                                                                                                                    |
| ------------------ | -------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `TAUTULLI_URL`     | Yes      | `http://tautulli:8181` | Full URL to your Tautulli instance. Use container name if on same Docker network, or IP address/hostname if different network. |
| `TAUTULLI_API_KEY` | Yes      | -                      | Your Tautulli API key (found in Tautulli → Settings → Web Interface → API)                                                     |
| `DAYS_BACK`        | Yes      | `7`                    | Number of days to look back for recently added media.                                                                          |
| `CRON_SCHEDULE`    | Yes\*    | -                      | CRON expression for scheduled execution (e.g., `0 16 * * SUN`). \*Not required if `RUN_ONCE=true`.                             |

### Discord Notifications (Optional)

| Variable              | Required | Default               | Description                                                                                                                |
| --------------------- | -------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `DISCORD_WEBHOOK_URL` | No       | -                     | Discord webhook URL for sending release summaries. Leave unset to disable Discord notifications.                           |
| `PLEX_URL`            | No       | `https://app.plex.tv` | Plex server URL for creating clickable links in Discord. Default works for most users. Only change for custom local links. |
| `PLEX_SERVER_ID`      | No       | Auto-detected         | Plex server machine identifier (auto-detected from Tautulli). Only set manually if auto-detection fails.                   |

### Execution Mode

| Variable   | Required | Default | Description                                                                                                             |
| ---------- | -------- | ------- | ----------------------------------------------------------------------------------------------------------------------- |
| `RUN_ONCE` | No       | `false` | Set to `true` for one-shot execution (runs once and exits). When `false` or unset, runs as daemon with `CRON_SCHEDULE`. |

### Advanced Settings

| Variable             | Required | Default | Description                                                                                                                                    |
| -------------------- | -------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `LOG_LEVEL`          | No       | `INFO`  | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`                                                                                         |
| `TZ`                 | No       | `UTC`   | Container timezone (e.g., `Europe/Paris`, `America/New_York`). Affects log timestamps and CRON schedule interpretation.                        |
| `INITIAL_BATCH_SIZE` | No       | Auto    | Override default batch size for fetching items from Tautulli. Auto-determined by `DAYS_BACK`: 100 (1-7 days), 200 (8-30 days), 500 (31+ days). |

### Performance Tuning

The application uses **iterative fetching** to efficiently retrieve media items from Tautulli. Instead of fetching all items at once, it starts with a reasonable batch size and increases if needed.

**Default batch sizes** (automatically determined by `DAYS_BACK`):

- **1-7 days**: 100 items per iteration
- **8-30 days**: 200 items per iteration
- **31+ days**: 500 items per iteration

The application will automatically fetch more items if the oldest item is still within the time range, preventing missed items while minimizing unnecessary data transfer.

**Custom batch size** (`initial_batch_size`):

You can override the default behavior in `config.yml` if you:

- Have a very large library with frequent additions (increase to 300-500)
- Have a slow network connection to Tautulli (decrease to 50-100)
- Want to optimize for your specific use case

Example:

```yaml
# configs/config.yml
initial_batch_size: 150 # Custom batch size
```

### Getting Your Tautulli API Key

1. Open Tautulli web interface
2. Go to Settings (⚙️) → Web Interface
3. Scroll down to "API" section
4. Copy your API key
5. **Important**: Keep this key secret! Never commit it to version control.

## Example Output

```
2026-02-13 10:00:15 - INFO - 🚀 Plex weekly summary starting
2026-02-13 10:00:15 - INFO - Configuration: Looking back 7 days
2026-02-13 10:00:15 - INFO - Querying recently added items...
2026-02-13 10:00:16 - INFO - Retrieved 45 items, filtered to 23 items from last 7 days
2026-02-13 10:00:16 - INFO - Found 23 recent items matching criteria
2026-02-13 10:00:16 - INFO - ➕ The Last of Us - S01E03 - Long, Long Time | added: 2026-02-10 14:23
2026-02-13 10:00:16 - INFO - ➕ Everything Everywhere All at Once (2022) | added: 2026-02-09 20:15
2026-02-13 10:00:16 - INFO - ➕ Succession - S04E01 - The Munsters | added: 2026-02-08 18:45
```

## Discord Notifications

Optionally send release summaries to a Discord channel using webhooks. The application will post a rich embed with all new media grouped by type.

### Setting Up Discord Webhook

1. Open your Discord server
2. Go to **Server Settings** → **Integrations** → **Webhooks**
3. Click **New Webhook** or **Create Webhook**
4. Customize the webhook:
   - Set a name (e.g., "Plex Releases")
   - Choose the target channel
   - Optionally set a custom avatar
5. Click **Copy Webhook URL**
6. Add the webhook URL to your `config.yml` file:

```yaml
# configs/config.yml
discord_webhook_url: ${DISCORD_WEBHOOK_URL} # Or hardcode the URL
```

### Plex Direct Links in Discord

Clickable Plex links in Discord messages work **automatically out of the box** - no configuration needed! The application:

- Uses `https://app.plex.tv` by default (works for remote access)
- Auto-detects your Plex Server ID from Tautulli on startup

**You only need to customize `PLEX_URL` if:**

- You want direct local links instead of Plex.tv links
- You have a custom Plex server setup

**Example - Custom local links:**

```yaml
# In your configs/config.yml file
plex_url: http://plex:32400 # Or your local Plex server URL
```

> **📝 Note:** If you need to manually set the Plex Server ID (auto-detection failed), find your server's Machine Identifier in Tautulli (Settings → Plex Media Server → "i" icon) or Plex Web (Settings → General → Show Advanced) and add `plex_server_id: your-machine-id` to your `config.yml` file.

### Discord Message Format

Messages are sent as multiple rich embeds—one per media category (e.g., Movies, TV Shows, Albums, Tracks):

- **Embed Titles**: Each embed is titled with the media type and emoji (e.g., "🎬 Movies - Last X days", "📺 TV Shows - Last X days")
- **Field Headers**: Each field groups items by date range (e.g., "12/01 - 12/07"), not by individual item
- **Field Content**: Lists of media items for that date range, with clickable titles linking directly to Plex Web
- **Description**: Total count of new items in that category
- **Color**: Green (#57F287) for successful summaries
- **Timestamp**: When the summary was generated

Each media item includes:

- **Movies**: Clickable title with year (e.g., [Interstellar](https://app.plex.tv/desktop#!/server/.../details) (2014))
- **TV Episodes**: Show name, season/episode numbers, and episode title
- **Music**: Artist, album, and track information

**Note:** The added date is shown as a range in the field header, not per individual item.

### Features

- **Optional**: Leaving `DISCORD_WEBHOOK_URL` unset disables Discord notifications
- **Non-blocking**: Application continues even if Discord posting fails
- **Emoji icons**: Visual indicators for each media type (🎬 📺 💿 🎵)
- **Clickable links**: Direct links to Plex Web for each media item (Server ID auto-detected from Tautulli)
- **Smart formatting**: Automatically groups media by type and truncates long lists
- **Rate limit handling**: Built-in retry logic for Discord API rate limits
- **Character limit handling**: Automatically truncates messages to fit Discord's 6000 character limit

### Example Configuration

```yaml
# docker-compose.yml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    container_name: plex-releases-summary
    restart: on-failure
    volumes:
      - ./configs:/app/configs:ro
    environment:
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL} # Pass from host env
```

**Note**: Discord webhooks are sensitive credentials. Never commit them to version control. Either use environment variables or Docker secrets.

## Development

### Local Development Setup

1. Clone and install dependencies:

```bash
git clone https://github.com/thomas-lg/plex-releases-summary.git
cd plex-releases-summary
```

2. Create configuration file:

```bash
cp configs/config.yml.example configs/config.yml
# Edit with your settings (set run_once: true and log_level: DEBUG for dev)
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

### Setup Instructions

1. **Create appdata directory** on your Unraid server:

   ```bash
   mkdir -p /mnt/user/appdata/plex-releases-summary
   ```

2. **Copy configuration file** to appdata:

   ```bash
   cd /mnt/user/appdata/plex-releases-summary
   # Download config.yml.example from the repository
   wget https://raw.githubusercontent.com/thomas-lg/plex-releases-summary/main/configs/config.yml.example -O config.yml
   # Edit with your settings
   nano config.yml
   ```

3. **Install via Docker** (or Community Applications):
   - **Repository**: `ghcr.io/thomas-lg/plex-releases-summary:latest`
   - **Volume mapping**: `/mnt/user/appdata/plex-releases-summary:/app/configs`
   - **Restart policy**: `on-failure`
   - **Network**: `bridge` or your custom network (e.g., `br0` for static IP)

4. **Optional - Pass secrets via environment variables** instead of hardcoding in config.yml:
   - Add environment variable: `TAUTULLI_API_KEY` = `your-api-key`
   - In config.yml use: `tautulli_api_key: ${TAUTULLI_API_KEY}`

### Editing Configuration on Unraid

Your configuration file is accessible via the Unraid webUI:

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

**Note**: The template will need to be updated to use volume mapping instead of individual environment variables. Check the repository for the latest template version.

**Security**: Store sensitive values (API keys, webhooks) as Unraid environment variables in the Docker template, then reference them in `config.yml` using `${VARIABLE_NAME}` syntax.

## Deployment Options

### Docker Compose (Production)

See [docker-compose.yml](docker-compose.yml) for a production-ready configuration.

**Scheduled Mode (Recommended):**

```yaml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    container_name: plex-releases-summary
    restart: on-failure
    volumes:
      - ./configs:/app/configs:ro
```

**One-Shot Mode (For External Cron):**

```yaml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    container_name: plex-releases-summary
    restart: "no"
    volumes:
      - ./configs:/app/configs:ro
```

**Note**: Set `run_once: true` or `run_once: false` in your `config.yml` file to control the execution mode.

## Troubleshooting

### Connection Issues

If you see connection errors:

- Verify Tautulli URL is correct and accessible from the container
- Check that the API key is valid (Settings → Web Interface → API in Tautulli)
- Ensure Tautulli is running and healthy
- If using Docker networks, verify network connectivity

### No Items Found

If the summary shows 0 items:

- Verify media has been added to Plex during the specified time range
- Check that Tautulli has scanned and indexed the new media
- Try increasing `DAYS_BACK` to verify the query works
- Set `LOG_LEVEL=DEBUG` to see detailed filtering information

### Debug Mode

Enable detailed logging by setting `log_level: DEBUG` in your `config.yml`:

```yaml
# configs/config.yml
log_level: DEBUG
```

Then run normally:

```bash
docker run --rm -v $(pwd)/configs:/app/configs:ro ghcr.io/thomas-lg/plex-releases-summary:latest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Tautulli](https://tautulli.com/) - Monitoring and tracking tool for Plex Media Server
- [Plex](https://www.plex.tv/) - Media server platform

## Security

**Important**: Never commit your `config.yml` file with real credentials or expose your Tautulli API key. The `configs/config.yml` file is gitignored by default. If you accidentally commit secrets, rotate your Tautulli API key immediately.

**Recommended**: Use environment variables or Docker secrets for sensitive values like API keys and webhook URLs, then reference them in `config.yml` using `${VARIABLE_NAME}` syntax.

---

Made with ❤️ for the Plex community
