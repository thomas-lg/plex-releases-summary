# Configuration Reference

Complete configuration guide for Plex Releases Summary. This document covers all configuration fields, methods, and troubleshooting.

> **📌 Quick Start:** Only 2 fields are required to run the application! See [Minimal Configuration](#minimal-configuration) below.

---

## Table of Contents

- [Configuration Reference](#configuration-reference)
  - [Table of Contents](#table-of-contents)
  - [Configuration Fields](#configuration-fields)
  - [Minimal Configuration](#minimal-configuration)
    - [Understanding Retry Logic](#understanding-retry-logic)
  - [Configuration Methods](#configuration-methods)
    - [Method 1: Environment Variables (Recommended)](#method-1-environment-variables-recommended)
    - [Method 2: Hardcoded Values](#method-2-hardcoded-values)
    - [Method 3: Docker Secrets (Production)](#method-3-docker-secrets-production)
  - [Environment Variables and Docker](#environment-variables-and-docker)
    - [When to Use Environment Variables](#when-to-use-environment-variables)
    - [Environment Variable to Field Mapping](#environment-variable-to-field-mapping)
  - [Optional Field Overrides](#optional-field-overrides)
    - [Discord Embed Limits](#discord-embed-limits)
  - [Docker Secrets](#docker-secrets)
    - [Volume-Mounted Secrets (Recommended for Sensitive Values)](#volume-mounted-secrets-recommended-for-sensitive-values)
    - [Direct Values (Alternative)](#direct-values-alternative)
    - [Docker Compose Secrets (Alternative)](#docker-compose-secrets-alternative)
    - [How Values Are Processed](#how-values-are-processed)
  - [Examples](#examples)
    - [Example 1: Minimal Production](#example-1-minimal-production)
    - [Example 2: Discord + One-Shot](#example-2-discord--one-shot)
  - [Operational Guide](#operational-guide)
    - [Configuration Auto-Creation](#configuration-auto-creation)
    - [Exit Codes](#exit-codes)
    - [Logging](#logging)
    - [Scheduler Behavior](#scheduler-behavior)
    - [Performance and Scaling](#performance-and-scaling)
    - [Backup and Restoration](#backup-and-restoration)
    - [Migration and Updates](#migration-and-updates)
    - [Tautulli API Version Compatibility](#tautulli-api-version-compatibility)
    - [Docker Networking](#docker-networking)
  - [Troubleshooting](#troubleshooting)
    - [Configuration Not Working](#configuration-not-working)
    - [Unresolved Environment Variable Error](#unresolved-environment-variable-error)
    - [Discord Notifications Not Sending](#discord-notifications-not-sending)
    - [CRON Schedule Not Running](#cron-schedule-not-running)
    - [Secret File Not Found](#secret-file-not-found)
    - [Validation Errors](#validation-errors)
    - [Docker Networking Issues](#docker-networking-issues)
    - [Need More Logging](#need-more-logging)
  - [Source of Truth](#source-of-truth)
  - [See Also](#see-also)

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

**\* Adaptive Batch Size:** Auto-calculated: 100 (≤7 days), 200 (≤30 days), 500 (>30 days). Override with `INITIAL_BATCH_SIZE` for specific performance needs.

---

## Minimal Configuration

**Only 2 fields are required:**

1. **`tautulli_url`** - Tautulli server URL
2. **`tautulli_api_key`** - Tautulli API key

**All other fields are optional** and have sensible defaults:

- `days_back`: 7 days
- `cron_schedule`: Weekly Sundays at 4 PM UTC (`0 16 * * SUN`)
- `plex_url`: Plex web app (`https://app.plex.tv`)
- `discord_webhook_url`: Disabled (no Discord notifications)
- `run_once`: `false` (scheduled mode)
- `log_level`: `INFO`
- `initial_batch_size`: Adaptive (100-500 based on `days_back`)

**You don't need to set optional fields unless you want to change the defaults.**

```yaml
# docker-compose.yml
environment:
  - TAUTULLI_URL=http://tautulli:8181
  - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key
  # That's it! All other fields use defaults
```

> **Timezone:** Container defaults to UTC. Set `TZ` environment variable for local timezone (e.g., `TZ=America/New_York`). CRON schedules run in configured timezone. Use [crontab.guru](https://crontab.guru) to validate expressions.
> **Iteration Logs:** "iteration 1, 2, 3..." is normal. Tautulli API lacks date filtering, so app fetches batches until finding all matches within `days_back`.

### Understanding Retry Logic

Both Tautulli and Discord API clients implement retry logic with exponential backoff:

**Tautulli API Retries:**

- **Attempts:** 3 retries with exponential backoff (1s, 2s, 4s)
- **Timeout:** 10s per request
- **Triggers:** Network errors, HTTP 5xx, timeouts

**Discord API Retries:**

- **Attempts:** 3 retries with exponential backoff (1s, 2s, 4s)
- **Timeout:** No explicit per-request timeout (uses `discord-webhook` library defaults)
- **Rate limits:** Respects HTTP 429 with `retry_after` header
- **No retry:** HTTP 400 errors (validation failures) fail immediately

---

## Configuration Methods

### Method 1: Environment Variables (Recommended)

Set in `docker-compose.yml` (or equivalent deployment file), then reference in `config.yml`:

```yaml
# deployment env file (example: docker-compose.yml)
environment:
  - TAUTULLI_URL=http://tautulli:8181

# config.yml (already configured)
tautulli_url: ${TAUTULLI_URL}
```

Optional fields already have `${VAR}` placeholders - just set the environment variable.

> ⚠️ Both steps required: env var + `${VAR}` reference in config.yml.

---

### Method 2: Hardcoded Values

```yaml
# configs/config.yml
tautulli_url: http://192.168.1.100:8181
tautulli_api_key: your_api_key
```

⚠️ Don't commit credentials.

---

### Method 3: Docker Secrets (Production)

```yaml
# deployment env file (example: docker-compose.yml)
environment:
  - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key

# config.yml (already configured)
tautulli_api_key: ${TAUTULLI_API_KEY}
```

**How it works:** The application automatically detects file paths (strings starting with `/`) and reads the file content. This is the Docker secrets pattern.

---

## Environment Variables and Docker

### When to Use Environment Variables

**Set environment variables for:**

- **Required fields** (`TAUTULLI_URL`, `TAUTULLI_API_KEY`) - **Always required**
- **Optional fields you want to customize** (e.g., `DAYS_BACK`, `DISCORD_WEBHOOK_URL`)

**Don't set environment variables for:**

- **Optional fields you want to keep at default values** - they work automatically

**How optional fields work:**

The default `config.yml` has all fields pre-configured with `${VAR}` placeholders:

```yaml
# Example from config.yml
days_back: ${DAYS_BACK} # Optional - defaults to 7
discord_webhook_url: ${DISCORD_WEBHOOK_URL} # Optional - defaults to None
```

**Behavior based on environment variable state:**

| Env Var State           | Required Field (`TAUTULLI_URL`) | Optional Field (`DAYS_BACK`)         |
| ----------------------- | ------------------------------- | ------------------------------------ |
| **Not set**             | ❌ Startup error                | ✅ Uses default (7) - no log message |
| **Empty string** (`""`) | ❌ Startup error                | ⚠️ WARNING logged, uses default      |
| **Valid value**         | ✅ Uses your value              | ✅ Uses your value                   |

**Example - Only setting what you need:**

```yaml
# deployment env file (example: docker-compose.yml)
environment:
  # Required - must set these
  - TAUTULLI_URL=http://tautulli:8181
  - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key

  # Optional - only set what you want to customize
  - DISCORD_WEBHOOK_URL=/run/secrets/discord_webhook # Enable Discord (file path)
  # OR direct URL: - DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
  - DAYS_BACK=14 # Change from default 7 to 14


  # Not setting CRON_SCHEDULE, LOG_LEVEL, etc. - they use defaults
```

### Environment Variable to Field Mapping

| Environment Variable  | Config Field          | Purpose                                                                                            |
| --------------------- | --------------------- | -------------------------------------------------------------------------------------------------- |
| `TAUTULLI_URL`        | `tautulli_url`        | Tautulli server URL (required)                                                                     |
| `TAUTULLI_API_KEY`    | `tautulli_api_key`    | Tautulli API key (required)                                                                        |
| `DAYS_BACK`           | `days_back`           | Override default (7 days)                                                                          |
| `CRON_SCHEDULE`       | `cron_schedule`       | Override default (Sunday 4 PM)                                                                     |
| `DISCORD_WEBHOOK_URL` | `discord_webhook_url` | Enable Discord notifications                                                                       |
| `PLEX_URL`            | `plex_url`            | Override default (app.plex.tv)                                                                     |
| `PLEX_SERVER_ID`      | `plex_server_id`      | Override auto-detection                                                                            |
| `RUN_ONCE`            | `run_once`            | Override default (false)                                                                           |
| `LOG_LEVEL`           | `log_level`           | Override default (INFO)                                                                            |
| `INITIAL_BATCH_SIZE`  | `initial_batch_size`  | Override adaptive batching                                                                         |
| `TZ`                  | N/A                   | Container timezone (UTC default)                                                                   |
| `PUID`                | N/A                   | User ID for file permissions - see [PUID/PGID Configuration](../README.md#puidpgid-configuration)  |
| `PGID`                | N/A                   | Group ID for file permissions - see [PUID/PGID Configuration](../README.md#puidpgid-configuration) |

---

## Optional Field Overrides

**All optional fields are pre-configured with `${VAR}` placeholders** in the default `config.yml`.

**To customize an optional field:** Just set the environment variable in `docker-compose.yml`. No config file editing needed.

**To use the default value:** Don't set the environment variable at all - it will use the default automatically.

**Example 1: Change to daily execution at midnight (override default):**

```yaml
# deployment env file (example: docker-compose.yml)
environment:
  - TAUTULLI_URL=http://tautulli:8181
  - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key
  - CRON_SCHEDULE=0 0 * * * # Override default (was: 0 16 * * SUN)
```

The `config.yml` already has `cron_schedule: ${CRON_SCHEDULE}`, so it will use your value.

**Example 2: Enable Discord notifications (was disabled by default):**

```yaml
# deployment env file (example: docker-compose.yml)
environment:
  - TAUTULLI_URL=http://tautulli:8181
  - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key
  - DISCORD_WEBHOOK_URL=/run/secrets/discord_webhook # File path (recommended)
  # OR direct URL:
  # - DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc...
```

The `config.yml` already has `discord_webhook_url: ${DISCORD_WEBHOOK_URL}`, which defaults to `None` if not set.

**Example 3: Using multiple optional overrides:**

```yaml
# deployment env file (example: docker-compose.yml)
environment:
  # Required
  - TAUTULLI_URL=http://tautulli:8181
  - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key

  # Optional customizations
  - DAYS_BACK=14 # Override default (7)
  - RUN_ONCE=true # Override default (false)
  - LOG_LEVEL=DEBUG # Override default (INFO)


  # Not setting CRON_SCHEDULE, PLEX_URL, etc. - they use defaults
```

### Discord Embed Limits

Discord enforces the following limits on embeds:

- **6000 characters** per embed (total)
- **1024 characters** per field (enforced, no splitting)
- **25 fields** maximum per embed

The application automatically handles these limits with a sophisticated dynamic trimming system:

**Field-Level Handling:**

- **Long fields:** Split across multiple fields at 1024 chars (preserves readability)
- **Too many fields:** Trims oldest entries when exceeding 25 fields (keeps most recent items)

**Embed-Level Validation:**

- Dynamic size calculation with 5800-character safety buffer
- Automatic trimming algorithm with up to 5 attempts
- 20% reduction per attempt when embed exceeds limits
- Items split into multiple Discord messages if necessary

**What you'll see:**

When trimming occurs, you'll see log messages like:

```text
WARNING - Embed for Movies exceeds size limits, trimming attempt 1/5
WARNING - Reduced field count from 30 to 24 items
```

**How to reduce trimming:**

- Reduce `days_back` value (fewer days = fewer items)
- Use more selective media type filtering in Tautulli settings
- Accept that some older items may not appear in Discord (all items still logged)

**Note:** All items are processed and logged regardless of Discord limits - trimming only affects Discord message content, not the actual functionality.

---

## Docker Secrets

### Volume-Mounted Secrets (Recommended for Sensitive Values)

For sensitive values like API keys and webhooks, use file-based secrets:

```yaml
# deployment env file (example: docker-compose.yml)
services:
  app:
    volumes:
      - ./secrets:/run/secrets:ro # Mount secrets directory
    environment:
      - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key # File path
      - DISCORD_WEBHOOK_URL=/run/secrets/discord_webhook # File path
```

Create secret files:

```bash
mkdir -p secrets
echo "your_api_key" > secrets/tautulli_api_key
echo "https://discord.com/api/webhooks/..." > secrets/discord_webhook
chmod 600 secrets/*  # Secure permissions
```

### Direct Values (Alternative)

You can also use direct values in environment variables (less secure for production):

```yaml
# deployment env file (example: docker-compose.yml)
environment:
  - TAUTULLI_URL=http://tautulli:8181
  - TAUTULLI_API_KEY=your_api_key_here # Direct value
  - DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc... # Direct URL
```

⚠️ **Security Note:** Direct values are visible in `docker-compose.yml`. Use file-based secrets for production.

### Docker Compose Secrets (Alternative)

For more complex deployments:

```yaml
# deployment env file (example: docker-compose.yml)
services:
  app:
    secrets:
      - tautulli_api_key
    environment:
      - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key

secrets:
  tautulli_api_key:
    file: ./secrets/tautulli_api_key
```

Both methods work identically from the application's perspective.

### How Values Are Processed

The application automatically detects whether you're using a file path (starts with `/`) or a direct value:

```yaml
environment:
  - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key # File path → reads file
  - DISCORD_WEBHOOK_URL=https://discord.com/api/... # Direct value → uses as-is
```

**File handling:** Full file contents are read with surrounding whitespace stripped. Startup fails with a clear error if the file is unreadable.

**Security considerations:**

See [Security](../README.md#security) for comprehensive security best practices including:

- File permissions and PUID/PGID considerations
- Container privilege dropping
- Secret management
- Production deployment security

**Troubleshooting:**

If file reading fails:

- Verify file exists: `docker exec <container> ls -la /path/to/file`
- Check file permissions (should be 600 or 400)
  - Ensure the volume mount is correct in `docker-compose.yml`
- Check logs for "Read secret from file" or error messages

---

## Examples

> **💡 New to the project?** See [Quick Start](../README.md#quick-start) in the main README for the simplest setup guide.

### Example 1: Minimal Production

Weekly summary using defaults:

```yaml
# deployment env file (example: docker-compose.yml)
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    volumes:
      - ./configs:/app/configs:ro
      - ./secrets:/run/secrets:ro
    environment:
      - TAUTULLI_URL=http://tautulli:8181
      - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key
    restart: unless-stopped
```

### Example 2: Discord + One-Shot

With Discord notifications and one-shot mode:

```yaml
# deployment env file (example: docker-compose.yml)
services:
  app:
    image: ghcr.io/thomas-lg/plex-releases-summary:latest
    volumes:
      - ./configs:/app/configs:ro
      - ./secrets:/run/secrets:ro
    environment:
      - TAUTULLI_URL=http://tautulli:8181
      - TAUTULLI_API_KEY=/run/secrets/tautulli_api_key
      - DISCORD_WEBHOOK_URL=/run/secrets/discord_webhook
      - RUN_ONCE=true
      - DAYS_BACK=14
      - LOG_LEVEL=DEBUG
```

**Discord notifications include:**

- 🎬 Movies | 📺 TV Shows | 💿 Albums | 🎵 Tracks
- Rich embeds per category with clickable Plex links
- Items grouped by date range

---

## Operational Guide

### Configuration Auto-Creation

Container auto-creates `config.yml` on first run if missing:

1. Copies from built-in template (`config.yml.default`)
2. Sets ownership via PUID/PGID (see [README](../README.md#puidpgid-configuration))
3. Pre-configured with `${VAR}` placeholders

**Container path contract (Docker):**

- Keep container-side targets fixed:
  - Config file: `/app/configs/config.yml`
  - Logs directory: `/app/logs`
- Customize host-side paths only (left side of volume mapping), for example:
  - `./custom-config:/app/configs`
  - `./custom-logs:/app/logs`

Reset to defaults: `rm configs/config.yml && docker compose restart`

### Exit Codes

| Code  | Meaning     | Cause                                                   |
| ----- | ----------- | ------------------------------------------------------- |
| `0`   | Success     | Completed successfully                                  |
| `1`   | Error       | Config/API errors, plus Discord errors in one-shot mode |
| `130` | Interrupted | KeyboardInterrupt (Ctrl+C)                              |

Use for monitoring: `docker run --rm app; [ $? -eq 0 ] || alert`

### Logging

**Format:** `%(asctime)s | %(levelname)-7s | %(name)s | %(message)s`

**Levels:** DEBUG (all items, API responses), INFO (default, first 10 items per type), WARNING (issues), ERROR (failures), CRITICAL (fatal)

**INFO Display Limit:** Shows first 10 items per media type, logs total count. All items still processed/sent to Discord. Use `LOG_LEVEL=DEBUG` to see all.

**View logs:** `docker logs plex-releases-summary` or `docker logs -f plex-releases-summary`

**Persistent file logs:** The container also writes rotating logs to `/app/logs/app.log` (mounted to host `./logs`).

- Max file size: `5 MB` per file
- Retention: `5` backup files + current file (`6` total max)
- Rotation behavior: when the current log file reaches `5 MB`, it is rotated (renamed to `app.log.1`) and a new `app.log` is created. Older backups are shifted (`app.log.1` → `app.log.2`, etc.), and the oldest backup beyond the 5-file limit is deleted.

### Scheduler Behavior

Scheduled mode (`run_once: false`) with APScheduler:

- **Coalesce:** Skips missed runs if previous execution still running
- **Max Instances:** 1 - only one job at a time
- **No retroactive runs:** Missed schedules don't execute after restart

Example: Daily 4 PM job, container down 2-6 PM → Missed run doesn't execute at 6 PM, next run tomorrow 4 PM.

**Graceful Shutdown:** SIGTERM/SIGINT handled, completes job if possible, clean exit.

### Performance and Scaling

**Resource Requirements:** ~50-100MB (small libraries <1000 items), ~400-800MB (very large 10000+)

**Factors:** Library size, time range (`days_back`), network latency, Tautulli performance

**Optimization:**

```yaml
# Large libraries or slow networks - fewer API calls
environment:
  - INITIAL_BATCH_SIZE=1000
  - DAYS_BACK=7

# Better Discord display - avoid trimming
environment:
  - DAYS_BACK=3
```

**Expected iterations:** 1-2 (1000 items, 7 days), 3-5 (10000 items, 7 days), 5-10 (10000 items, 30 days)

### Backup and Restoration

**Backup essentials:** `configs/config.yml` and `secrets/` directory

```bash
# Backup
tar czf backup-$(date +%Y%m%d).tar.gz configs/ secrets/

# Restore
docker compose down
tar xzf backup-YYYYMMDD.tar.gz
chmod 600 secrets/*
docker compose up -d
```

### Migration and Updates

**Update procedure:**

```bash
cp configs/config.yml configs/config.yml.backup  # Backup
docker compose pull && docker compose down && docker compose up -d
docker logs -f plex-releases-summary  # Verify
```

**Pinning:** Use `:latest` for auto-updates or `:v1.0.0` for stable production. Config format is stable.

**Rollback:** `docker compose down`, restore backup, update image tag to old version, `docker compose up -d`

### Tautulli API Version Compatibility

**Endpoints used:** `get_recently_added`, `get_server_identity` (auto-detects Plex server ID)

**Minimum:** Tautulli v2.1.0 | **Recommended:** v2.5.0+ | **Tested:** v2.5.0 - v2.13.0+

Handles both wrapped and direct response formats automatically. API maintains backward compatibility.

**Test API:** `curl "http://tautulli:8181/api/v2?apikey=YOUR_KEY&cmd=get_recently_added&count=10"`

### Docker Networking

**Bridge Network (Default):** Use container names as hostnames

```yaml
environment:
  - TAUTULLI_URL=http://tautulli:8181 # Container name
```

**Tautulli on host:** Use `http://host.docker.internal:8181` (Docker Desktop) or host IP `http://192.168.1.100:8181` (Linux)

**External server:** Use hostname `http://tautulli.example.com:8181`

**Troubleshooting:**

```bash
# Check network
docker network inspect bridge

# Test connectivity
docker exec plex-releases-summary ping tautulli

# Get IP
docker inspect tautulli | grep IPAddress

# Linux host.docker.internal fix
extra_hosts:
  - "host.docker.internal:host-gateway"
```

---

## Troubleshooting

### Configuration Not Working

**Symptom:** Environment variables set but application uses defaults or fails

**Solution:** Ensure both steps are complete:

1. ✅ Environment variable set in `docker-compose.yml`
2. ✅ Variable referenced in config.yml with `${VAR}` syntax (default config.yml has all fields configured)

---

### Unresolved Environment Variable Error

**Symptom:** Error message about unresolved environment variable in a **required field** like `${UNDEFINED_VAR}`

**Cause:** A **required field** (`tautulli_url` or `tautulli_api_key`) references an environment variable that is not set or is empty

**Solution:** Set the required environment variable in `docker-compose.yml` to a non-empty value

**Note:** Optional fields with undefined environment variables silently use their default values (no log messages). Empty strings log a WARNING (possible configuration mistake). Only required fields cause startup errors.

---

### Discord Notifications Not Sending

**Symptom:** Application runs but Discord doesn't receive messages

**Checklist:**

1. ✅ `DISCORD_WEBHOOK_URL` set in `docker-compose.yml`
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
# deployment env file (example: docker-compose.yml)
environment:
  - TZ=America/New_York # Use your timezone
  - CRON_SCHEDULE=0 16 * * SUN # Now runs 4 PM Eastern
```

---

### Secret File Not Found

**Symptom:** Error reading secret file

**Solution:**

1. Verify file exists: `ls -la secrets/`
2. Check volume mount in `docker-compose.yml`: `- ./secrets:/run/secrets:ro`
3. Ensure file path in env var matches: `TAUTULLI_API_KEY=/run/secrets/tautulli_api_key`
4. Check file permissions: `chmod 600 secrets/tautulli_api_key`

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
3. **`docker-compose.yml`** — Environment variable values

When in doubt, refer to `src/config.py` for the authoritative field definitions and defaults.

---

## See Also

- [Main README](../README.md) - Quick start guide
- [config.yml](../configs/config.yml) - Configuration file template
- [docker-compose.yml](../docker-compose.yml) - Production deployment example
