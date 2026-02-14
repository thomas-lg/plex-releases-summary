# Plex Releases Summary

A lightweight Docker container that fetches and displays recently added media items from your Plex server via Tautulli. Perfect for scheduled reports of new content added to your media library.

## Features

- 📅 **Scheduled execution** with CRON-like timing (runs as daemon)
- ▶️ **One-shot mode** for external cron jobs or manual runs (`RUN_ONCE=true`)
- 📺 Fetches recently added movies, TV shows, episodes, music, and more
- 🎯 Configurable time range (e.g., last 7 days)
- 🐳 Docker-ready with minimal footprint
- 📊 Clean, formatted output with media type detection
- ⚡ Graceful shutdown handling for containerized environments

## Prerequisites

- [Tautulli](https://tautulli.com/) installed and configured with your Plex server
- Tautulli API key (found in Tautulli → Settings → Web Interface → API)
- Docker or Docker Compose

## Quick Start

### Using Docker Compose (Recommended)

1. Clone this repository:

```bash
git clone https://github.com/thomas-lg/plex-releases-summary.git
cd plex-releases-summary
```

2. Create a `.env` file with your configuration:

```bash
cp .env.example .env
# Edit .env with your Tautulli URL and API key
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
    restart: unless-stopped
    env_file:
      - .env
    environment:
      CRON_SCHEDULE: "0 9 * * MON" # Every Monday at 9:00 AM
```

**Docker CLI:**

```bash
docker run -d \
  --name plex-releases-summary \
  --restart unless-stopped \
  -e TAUTULLI_URL=http://your-tautulli-host:8181 \
  -e TAUTULLI_API_KEY=your-api-key \
  -e DAYS_BACK=7 \
  -e CRON_SCHEDULE="0 9 * * MON" \
  ghcr.io/thomas-lg/plex-releases-summary:latest
```

**Common CRON Schedule Examples:**

| Schedule                   | CRON Expression   | Description               |
| -------------------------- | ----------------- | ------------------------- |
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

The scheduler handles `SIGTERM` and `SIGINT` signals gracefully, making it safe to stop with `docker stop` or Kubernetes pod termination.

### ▶️ One-Shot Mode

Run once and exit immediately. Ideal for external cron jobs, manual execution, or CI/CD pipelines.

**Docker Compose:**

```yaml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    container_name: plex-releases-summary
    restart: "no"
    env_file:
      - .env
    # No CRON_SCHEDULE = one-shot mode
```

**Docker CLI:**

```bash
docker run --rm \
  -e TAUTULLI_URL=http://your-tautulli-host:8181 \
  -e TAUTULLI_API_KEY=your-api-key \
  -e DAYS_BACK=7 \
  ghcr.io/thomas-lg/plex-releases-summary:latest
```

### External Scheduling with System Cron

For external scheduling using system cron (one-shot mode):

```bash
# Run every Monday at 9:00 AM
0 9 * * 1 docker run --rm --env-file /path/to/.env ghcr.io/thomas-lg/plex-releases-summary:latest
```

### Using Docker CLI

```bash
docker run --rm \
  -e TAUTULLI_URL=http://your-tautulli-host:8181 \
  -e TAUTULLI_API_KEY=your-api-key \
  -e DAYS_BACK=7 \
  -e LOG_LEVEL=INFO \
  ghcr.io/thomas-lg/plex-releases-summary:latest
```

## Configuration

All configuration is done via environment variables:

| Variable             | Required | Default | Description                                                                                                          |
| -------------------- | -------- | ------- | -------------------------------------------------------------------------------------------------------------------- |
| `TAUTULLI_URL`       | Yes      | -       | Full URL to your Tautulli instance (e.g., `http://tautulli:8181`)                                                    |
| `TAUTULLI_API_KEY`   | Yes      | -       | Your Tautulli API key (found in Tautulli settings)                                                                   |
| `DAYS_BACK`          | Yes      | -       | Number of days to look back for new media                                                                            |
| `CRON_SCHEDULE`      | Yes      | -       | CRON expression for scheduled execution (e.g., `0 9 * * MON`). Required when `RUN_ONCE` is not set to `true`.        |
| `RUN_ONCE`           | No       | `false` | When set to `true`, runs once and exits instead of running on a schedule. If `false`/unset, `CRON_SCHEDULE` is used. |
| `LOG_LEVEL`          | No       | `INFO`  | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`                                                                   |
| `INITIAL_BATCH_SIZE` | No       | Auto    | Override batch size for fetching items. Default: 100 (1-7 days), 200 (8-30 days), 500 (31+ days)                     |

### Performance Tuning

The application uses **iterative fetching** to efficiently retrieve media items from Tautulli. Instead of fetching all items at once, it starts with a reasonable batch size and increases if needed.

**Default batch sizes** (automatically determined by `DAYS_BACK`):

- **1-7 days**: 100 items per iteration
- **8-30 days**: 200 items per iteration
- **31+ days**: 500 items per iteration

The application will automatically fetch more items if the oldest item is still within the time range, preventing missed items while minimizing unnecessary data transfer.

**Custom batch size** (`INITIAL_BATCH_SIZE`):

You can override the default behavior by setting `INITIAL_BATCH_SIZE` if you:

- Have a very large library with frequent additions (increase to 300-500)
- Have a slow network connection to Tautulli (decrease to 50-100)
- Want to optimize for your specific use case

Example:

```yaml
environment:
  - INITIAL_BATCH_SIZE=150 # Custom batch size
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

## Development

### Local Development Setup

1. Clone and install dependencies:

```bash
git clone https://github.com/thomas-lg/plex-releases-summary.git
cd plex-releases-summary
```

2. Create `.env` file:

```bash
cp .env.example .env
# Edit with your settings
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
docker run --rm --env-file .env plex-releases-summary:latest
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

## Deployment Options

### Docker Compose (Production)

See [docker-compose.yml](docker-compose.yml) for a production-ready configuration.

**Scheduled Mode (Recommended):**

```yaml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    container_name: plex-releases-summary
    restart: unless-stopped
    env_file:
      - .env
    environment:
      CRON_SCHEDULE: "0 9 * * MON" # Every Monday at 9:00 AM
```

**One-Shot Mode (For External Cron):**

```yaml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    container_name: plex-releases-summary
    restart: "no"
    env_file:
      - .env
```

### Kubernetes Deployment

**Option 1: Deployment with Built-in Scheduler (Recommended)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: plex-summary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: plex-summary
  template:
    metadata:
      labels:
        app: plex-summary
    spec:
      containers:
        - name: plex-summary
          image: ghcr.io/thomas-lg/plex-releases-summary:latest
          env:
            - name: TAUTULLI_URL
              value: "http://tautulli:8181"
            - name: TAUTULLI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: tautulli-secret
                  key: api-key
            - name: DAYS_BACK
              value: "7"
            - name: CRON_SCHEDULE
              value: "0 9 * * MON" # Every Monday at 9 AM
```

**Option 2: Kubernetes CronJob (External Scheduling)**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: plex-summary
spec:
  schedule: "0 9 * * 1" # Every Monday at 9 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: plex-summary
              image: ghcr.io/thomas-lg/plex-releases-summary:latest
              env:
                - name: TAUTULLI_URL
                  value: "http://tautulli:8181"
                - name: TAUTULLI_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: tautulli-secret
                      key: api-key
                - name: DAYS_BACK
                  value: "7"
                - name: LOG_LEVEL
                  value: "INFO"
          restartPolicy: OnFailure
```

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

Enable detailed logging:

```bash
docker run --rm \
  -e LOG_LEVEL=DEBUG \
  -e TAUTULLI_URL=http://your-host:8181 \
  -e TAUTULLI_API_KEY=your-key \
  -e DAYS_BACK=7 \
  ghcr.io/thomas-lg/plex-releases-summary:latest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Tautulli](https://tautulli.com/) - Monitoring and tracking tool for Plex Media Server
- [Plex](https://www.plex.tv/) - Media server platform

## Security

**Important**: Never commit your `.env` file or expose your Tautulli API key. The `.env` file is gitignored by default. If you accidentally commit secrets, rotate your Tautulli API key immediately.

---

Made with ❤️ for the Plex community
