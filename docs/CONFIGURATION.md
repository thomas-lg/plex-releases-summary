# Configuration Reference

Complete configuration guide for Plex Releases Summary. This document covers all configuration fields, methods, and troubleshooting.

> **📌 Quick Start:** Only 2 fields are required to run the application! See [Minimal Configuration](#minimal-configuration) below.

---

## Table of Contents

- [Configuration Fields](#configuration-fields)
- [Minimal Configuration](#minimal-configuration)
- [Configuration Methods](#configuration-methods)
- [Environment Variables and Docker](#environment-variables-and-docker)
- [Optional Field Overrides](#optional-field-overrides)
- [Docker Secrets](#docker-secrets)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Configuration Fields

All configuration fields are defined in `src/config.py`. The table below shows all available options:

| Field                  | Type    | Required         | Default                 | Validation                            | Description                                                                        |
| ---------------------- | ------- | ---------------- | ----------------------- | ------------------------------------- | ---------------------------------------------------------------------------------- |
| **`tautulli_url`**     | string  | ✅ **Yes**       | -                       | -                                     | Full URL to Tautulli instance (e.g., `http://tautulli:8181`)                       |
| **`tautulli_api_key`** | string  | ✅ **Yes**       | -                       | -                                     | Tautulli API key (find in Tautulli: Settings → Web Interface → API)                |
| `days_back`            | integer | No               | `7`                     | ≥ 1                                   | Number of days to look back for new media releases                                 |
| `cron_schedule`        | string  | ⚠️ Conditional\* | `"0 16 * * SUN"`        | Valid CRON                            | CRON expression for scheduled execution (Sundays at 4 PM)                          |
| `discord_webhook_url`  | string  | No               | `None`                  | -                                     | Discord webhook URL for notifications (optional)                                   |
| `plex_url`             | string  | No               | `"https://app.plex.tv"` | -                                     | Plex server URL for generating clickable media links                               |
| `plex_server_id`       | string  | No               | Auto-detected           | -                                     | Plex server machine identifier (auto-detected via Tautulli when Discord enabled)   |
| `run_once`             | boolean | No               | `false`                 | -                                     | `true` = one-shot execution, `false` = scheduled mode                              |
| `log_level`            | string  | No               | `"INFO"`                | DEBUG, INFO, WARNING, ERROR, CRITICAL | Logging verbosity level                                                            |
| `initial_batch_size`   | integer | No               | Adaptive\*              | 1-10000                               | Tautulli API batch size (adaptive: 100 for ≤7 days, 200 for ≤30 days, 500 for >30) |

**\* Conditional:** `cron_schedule` is required when `run_once` is `false` (scheduled mode).

**\* Adaptive Batch Size:** Automatically calculated based on `days_back` value:

- **≤7 days:** 100 items per batch (typical weekly use)
- **≤30 days:** 200 items per batch (monthly summaries)
- **>30 days:** 500 items per batch (large historical queries)

This optimizes API calls for different time ranges. Override with `INITIAL_BATCH_SIZE` environment variable only for large libraries with specific performance needs.

---

## Minimal Configuration

**You only need to configure 2 fields to get started:**

1. **`tautulli_url`** - Your Tautulli server URL
2. **`tautulli_api_key`** - Your Tautulli API key

All other fields have sensible defaults and work out of the box:

- ✅ Checks last **7 days** of new media
- ✅ Runs **weekly on Sundays at 4 PM**
- ✅ Uses **Plex web app** for media links
- ✅ **No Discord** notifications (optional)
- ✅ **INFO** level logging

**Example minimal setup:**

```yaml
# docker-compose.yml
environment:
  - TAUTULLI_URL=http://tautulli:8181
  - TAUTULLI_API_KEY=/run/secrets/tautulli_key
```

The default `config.yml` is already configured with all fields - you only set environment variables for what you want to customize.

> **Timezone:** Container defaults to UTC. To use your local timezone, set `TZ` environment variable (e.g., `TZ=America/New_York`, `TZ=Europe/Paris`). CRON schedules will run in the configured timezone. Use [crontab.guru](https://crontab.guru) to validate CRON expressions.

> **Iteration Logs:** You may see logs like "iteration 1, 2, 3...". This is normal - Tautulli API lacks date filtering, so the application fetches items in batches and filters client-side until all matches are found.

---

## Configuration Methods

There are three ways to set configuration values:

### Method 1: Environment Variables (Recommended for Docker)

This is the recommended approach for Docker deployments. It requires **two steps**:

**Step 1:** Set environment variable in `docker-compose.yml`:

```yaml
environment:
  - TAUTULLI_URL=http://tautulli:8181
```

**Step 2:** Reference it in `configs/config.yml`:

```yaml
tautulli_url: ${TAUTULLI_URL}
```

**For optional fields:** They already have `${VAR}` placeholders. Just set the environment variable - no config editing needed!

```yaml
# docker-compose.yml - set this
environment:
  - DAYS_BACK=14

# config.yml - already has this, no editing needed
days_back: ${DAYS_BACK}
```

**Why two steps?** The application reads from `config.yml`, not directly from environment variables. Using `${VAR}` syntax in the YAML file tells the application to substitute the environment variable's value.

**Visual flow:**

```
docker-compose.yml          config.yml                 Application
TAUTULLI_URL=...      →     tautulli_url: ${...}  →    Reads value
```

> ⚠️ **Important:** Setting only the environment variable is NOT sufficient. Both steps are required.

---

### Method 2: Hardcoded Values (Simple for Testing)

For quick testing or simple setups, you can hardcode values directly in `config.yml`:

```yaml
# configs/config.yml
tautulli_url: http://192.168.1.100:8181
tautulli_api_key: your_actual_api_key_here
```

> **⚠️ Security Warning:** Do not commit real credentials to version control with this method.

---

### Method 3: Docker Secrets (Best for Production)

For production deployments, use file-based secrets for sensitive values:

1. Create secret files:

   ```bash
   mkdir -p secrets
   echo "your_api_key" > secrets/tautulli_key
   echo "https://discord.com/api/webhooks/..." > secrets/discord_webhook
   ```

2. Set environment variables to file paths:

   ```yaml
   # docker-compose.yml
   environment:
     - TAUTULLI_API_KEY=/run/secrets/tautulli_key
       - DISCORD_WEBHOOK_URL=/app/secrets/discord_webhook
   ```

3. Reference in config.yml:
   ```yaml
   # configs/config.yml
   tautulli_api_key: ${TAUTULLI_API_KEY}
   discord_webhook_url: ${DISCORD_WEBHOOK_URL}
   ```

**How it works:** The application automatically detects file paths (strings starting with `/`) and reads the file content. This is the Docker secrets pattern.

---

## Environment Variables and Docker

### When to Use Environment Variables

Use environment variables for:

- **Required fields** (tautulli_url, tautulli_api_key) - **Must be defined**
- **Optional fields you want to override** (e.g., days_back, discord_webhook_url)

You do **NOT** need environment variables for optional fields you want to keep at their defaults.

> **✨ Lenient Behavior:** Optional fields use `${VAR}` placeholders by default:
>
> - **Undefined env var** (not set): Silently uses default value (clean logs)
> - **Empty env var** (set to `""`): Logs WARNING, uses default (possible mistake)
> - **Valid env var**: Uses your custom value
>
> Only required fields will cause startup errors if undefined or empty.

### Environment Variable to Field Mapping

| Environment Variable  | Config Field          | Purpose                        |
| --------------------- | --------------------- | ------------------------------ |
| `TAUTULLI_URL`        | `tautulli_url`        | Tautulli server URL (required) |
| `TAUTULLI_API_KEY`    | `tautulli_api_key`    | Tautulli API key (required)    |
| `DAYS_BACK`           | `days_back`           | Override default (7 days)      |
| `CRON_SCHEDULE`       | `cron_schedule`       | Override default (Sunday 4 PM) |
| `DISCORD_WEBHOOK_URL` | `discord_webhook_url` | Enable Discord notifications   |
| `PLEX_URL`            | `plex_url`            | Override default (app.plex.tv) |
| `PLEX_SERVER_ID`      | `plex_server_id`      | Override auto-detection        |
| `RUN_ONCE`            | `run_once`            | Override default (false)       |
| `LOG_LEVEL`           | `log_level`           | Override default (INFO)        |
| `INITIAL_BATCH_SIZE`  | `initial_batch_size`  | Override adaptive batching     |

---

## Optional Field Overrides

**All optional fields are pre-configured with `${VAR}` placeholders** in `config.yml`.

To override: **Just set the environment variable** in `docker-compose.yml`. No config file editing needed!

**Example: Change to daily execution at midnight:**

```yaml
# docker-compose.yml - just add this env var
environment:
  - TAUTULLI_URL=http://tautulli:8181
  - TAUTULLI_API_KEY=/run/secrets/tautulli_key
  - CRON_SCHEDULE=0 0 * * *
```

The config.yml already has `cron_schedule: ${CRON_SCHEDULE}`, so it will automatically use your value.

**Example: Enable Discord notifications:**

```yaml
# docker-compose.yml - just add this env var
environment:
  - TAUTULLI_URL=http://tautulli:8181
  - TAUTULLI_API_KEY=/run/secrets/tautulli_key
  - DISCORD_WEBHOOK_URL=/app/secrets/discord_webhook
```

The config.yml already has `discord_webhook_url: ${DISCORD_WEBHOOK_URL}`, so it will automatically use your value.

### Discord Embed Limits

Discord enforces the following limits on embeds:

- **6000 characters** per embed (total)
- **1024 characters** per field (enforced, no splitting)
- **25 fields** maximum per embed

The application automatically handles these limits:

- **Long fields:** Split across multiple fields at 1024 chars (preserves readability)
- **Too many fields:** Trims oldest entries when exceeding 25 fields (keeps most recent items)
- **Oversized embeds:** Unlikely to cause issues due to field-level trimming, but if total exceeds 6000 chars, Discord may reject (rare)

**Retry Logic:** Both Tautulli and Discord clients use exponential backoff with 3 retry attempts and increasing delays to handle transient network failures gracefully.

---

## Docker Secrets

### Volume-Mounted Secrets (Recommended)

The simplest approach for secrets:

```yaml
# docker-compose.yml
services:
  app:
    volumes:
      - ./secrets:/app/secrets:ro # Mount secrets directory
    environment:
      - TAUTULLI_API_KEY=/run/secrets/tautulli_key # Point to file
```

Create secret files:

```bash
mkdir -p secrets
echo "your_api_key" > secrets/tautulli_key
chmod 600 secrets/tautulli_key  # Secure permissions
```

### Docker Compose Secrets (Alternative)

For more complex deployments:

```yaml
# docker-compose.yml
services:
  app:
    secrets:
      - tautulli_key
    environment:
      - TAUTULLI_API_KEY=/run/secrets/tautulli_key

secrets:
  tautulli_key:
    file: ./secrets/tautulli_key
```

Both methods work identically from the application's perspective.

---

## Examples

### Example 1: Minimal Production Setup

**Goal:** Weekly summary on Sundays using defaults

```yaml
# docker-compose.yml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    volumes:
      - ./configs:/app/configs:ro
      - ./secrets:/app/secrets:ro
    environment:
      - TAUTULLI_URL=http://tautulli:8181
      - TAUTULLI_API_KEY=/run/secrets/tautulli_key
    restart: unless-stopped
```

Use the default `config.yml` as-is. All optional fields use their defaults silently when environment variables are not set (clean logs).

---

### Example 2: Daily Summaries with Discord

**Goal:** Daily summaries at 9 AM with Discord notifications

```yaml
# docker-compose.yml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    volumes:
      - ./configs:/app/configs:ro
      - ./secrets:/app/secrets:ro
    environment:
      - TAUTULLI_URL=http://tautulli:8181
      - TAUTULLI_API_KEY=/run/secrets/tautulli_key
      - DISCORD_WEBHOOK_URL=/app/secrets/discord_webhook
      - CRON_SCHEDULE=0 9 * * *
    restart: unless-stopped
```

**Discord Message Format:**

Messages are sent as rich embeds—one per media category (Movies, TV Shows, Albums, Tracks):

- **Embed Structure**: Each embed shows the media type with emoji (e.g., "🎬 Movies - Last 7 days")
- **Field Grouping**: Items grouped by date range (e.g., "12/01 - 12/07")
- **Clickable Links**: Direct links to Plex Web for each media item
- **Auto-Detection**: Plex Server ID automatically detected from Tautulli
- **Smart Formatting**: Automatically handles rate limits and character limits

Each media item includes:

- **Movies**: Clickable title with year (e.g., [Interstellar](https://app.plex.tv/desktop#!/server/.../details) (2014))
- **TV Episodes**: Show name, season/episode, and episode title
- **Music**: Artist, album, and track information

---

### Example 3: One-Shot Execution

**Goal:** Run once and exit (for external cron or manual execution)

```yaml
# docker-compose.yml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    volumes:
      - ./configs:/app/configs:ro
      - ./secrets:/app/secrets:ro
    environment:
      - TAUTULLI_URL=http://tautulli:8181
      - TAUTULLI_API_KEY=/run/secrets/tautulli_key
      - RUN_ONCE=true
```

Or run directly with Docker CLI:

```bash
docker run --rm \
  -e TAUTULLI_URL=http://tautulli:8181 \
  -e TAUTULLI_API_KEY=your_key \
  -e RUN_ONCE=true \
  -v ./configs:/app/configs:ro \
  ghcr.io/thomas-lg/plex-releases-summary:latest
```

---

### Example 4: Advanced Configuration

**Goal:** Biweekly summaries, custom Plex URL, debug logging

```yaml
# docker-compose.yml
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    volumes:
      - ./configs:/app/configs:ro
      - ./secrets:/app/secrets:ro
    environment:
      - TAUTULLI_URL=http://tautulli:8181
      - TAUTULLI_API_KEY=/run/secrets/tautulli_key
      - DAYS_BACK=14
      - PLEX_URL=http://plex:32400
      - LOG_LEVEL=DEBUG
    restart: unless-stopped
```

---

## Troubleshooting

### Configuration Not Working

**Symptom:** Environment variables set but application uses defaults or fails

**Solution:** Ensure both steps are complete:

1. ✅ Environment variable set in docker-compose.yml
2. ✅ Variable referenced in config.yml with `${VAR}` syntax (default config.yml has all fields configured)

---

### Unresolved Environment Variable Error

**Symptom:** Error message about unresolved environment variable in a **required field** like `${UNDEFINED_VAR}`

**Cause:** A **required field** (`tautulli_url` or `tautulli_api_key`) references an environment variable that is not set or is empty

**Solution:** Set the required environment variable in docker-compose.yml to a non-empty value

**Note:** Optional fields with undefined environment variables silently use their default values (no log messages). Empty strings log a WARNING (possible configuration mistake). Only required fields cause startup errors.

---

### Discord Notifications Not Sending

**Symptom:** Application runs but Discord doesn't receive messages

**Checklist:**

1. ✅ `DISCORD_WEBHOOK_URL` set in docker-compose.yml
2. ✅ Webhook URL is valid (test with `curl -X POST -H "Content-Type: application/json" -d '{"content":"test"}' YOUR_WEBHOOK_URL`)
3. ✅ If using file-based secret, verify file exists and is readable
4. ✅ Check logs for warnings about undefined or empty environment variables

---

### CRON Schedule Not Running

**Symptom:** Application starts but scheduled execution doesn't happen

**Checklist:**

1. ✅ `run_once` is `false` (or not set)
2. ✅ `cron_schedule` is valid CRON expression
3. ✅ Check container logs: `docker logs plex-releases-summary`
4. ✅ Verify timezone - container defaults to UTC unless `TZ` environment variable is set

**CRON Expression Help:**

- `0 16 * * SUN` = Sundays at 4:00 PM in container timezone
- `0 0 * * *` = Daily at midnight in container timezone
- `0 */6 * * *` = Every 6 hours
- Use [crontab.guru](https://crontab.guru) to validate expressions

**Setting Timezone:**

```yaml
# docker-compose.yml
environment:
  - TZ=America/New_York # Use your timezone
  - CRON_SCHEDULE=0 16 * * SUN # Now runs 4 PM Eastern
```

---

### Secret File Not Found

**Symptom:** Error reading secret file

**Solution:**

1. Verify file exists: `ls -la secrets/`
2. Check volume mount in docker-compose.yml: `- ./secrets:/app/secrets:ro`
3. Ensure file path in env var matches: `TAUTULLI_API_KEY=/run/secrets/tautulli_key`
4. Check file permissions: `chmod 600 secrets/tautulli_key`

---

### Validation Errors

**Symptom:** Pydantic validation error on startup

**Common causes:**

- `days_back` must be integer ≥1
- `log_level` must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `initial_batch_size` must be between 1-10000
- `cron_schedule` must be valid CRON expression

**Solution:** Check environment variable values match expected types and constraints.

---

### Docker Networking Issues

**Symptom:** Connection refused to Tautulli from container

**Solution:**

- If Tautulli is in separate container, ensure both use same Docker network
- Use container name (e.g., `http://tautulli:8181`) if on same network
- Use host IP (e.g., `http://192.168.1.100:8181`) for external Tautulli
- On Docker Desktop: use `host.docker.internal` instead of `localhost`

---

### Need More Logging

**Symptom:** Need to debug issues

**Solution:** Enable debug logging by setting the environment variable:

```yaml
# docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG
```

Then check logs:

```bash
docker logs plex-releases-summary
# or for live streaming:
docker logs -f plex-releases-summary
```

---

## Source of Truth

Configuration is defined in these files (in order of authority):

1. **`src/config.py`** - Schema definition with types, defaults, and validation rules
2. **`configs/config.yml`** - User configuration with environment variable references
3. **`docker-compose.yml`** - Environment variable values

When in doubt, refer to `src/config.py` for the authoritative field definitions and defaults.

---

## See Also

- [Main README](../README.md) - Quick start guide
- [config.yml](../configs/config.yml) - Configuration file template
- [docker-compose.yml](../docker-compose.yml) - Production deployment example
