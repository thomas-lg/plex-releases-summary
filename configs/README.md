# Configuration Directory

This directory contains the application configuration file.

## Quick Start

1. Copy example: `cp config.yml.example config.yml`
2. Edit `config.yml` with your Tautulli URL, API key, and schedule
3. Run: `docker compose up`

## Configuration Methods

### Method 1: Static Values

Hardcode values directly in YAML:

```yaml
tautulli_url: http://tautulli:8181
tautulli_api_key: your_api_key_here
days_back: 7
```

### Method 2: Environment Variables

Use `${VAR}` syntax in config.yml:

```yaml
tautulli_api_key: ${TAUTULLI_API_KEY}
```

Set in docker-compose.yml:

```yaml
environment:
  - TAUTULLI_API_KEY=your_api_key
```

### Method 3: File-Based Secrets (Recommended for Production)

1. Create secret file:

   ```bash
   mkdir -p secrets
   echo "your_api_key" > secrets/tautulli_key
   ```

2. Mount in docker-compose.yml:

   ```yaml
   volumes:
     - ./secrets:/app/secrets:ro
   environment:
     - TAUTULLI_API_KEY=/app/secrets/tautulli_key
   ```

3. Reference in config.yml:
   ```yaml
   tautulli_api_key: ${TAUTULLI_API_KEY}
   ```

The app automatically reads file content for paths starting with `/`.

_Advanced: Docker Compose secrets: syntax also supported (see docker-compose.yml)_

## Files

- `config.yml.example` - Example configuration with all options
- `config.yml` - Your configuration (gitignored)

## Security

⚠️ Never commit `config.yml` with real credentials. Use Method 3 for production.
