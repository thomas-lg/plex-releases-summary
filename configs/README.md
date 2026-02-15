# Configuration Directory

This directory contains the application configuration file.

## Quick Start

1. Copy the example configuration:

   ```bash
   cp config.yml.example config.yml
   ```

2. Edit `config.yml` with your settings:
   - Set your Tautulli URL and API key
   - Configure schedule or one-shot mode
   - Optionally add Discord webhook

3. Run with Docker Compose:
   ```bash
   docker compose up
   ```

## Configuration Methods

### Method 1: Static Values (Simple)

Hardcode values directly in the YAML file:

```yaml
tautulli_url: http://tautulli:8181
tautulli_api_key: your_api_key_here
days_back: 7
```

### Method 2: Environment Variables (Flexible)

Reference environment variables using `${VAR}` syntax:

```yaml
tautulli_api_key: ${TAUTULLI_API_KEY}
```

Then set in docker-compose.yml:

```yaml
environment:
  - TAUTULLI_API_KEY=your_api_key
```

### Method 3: File-Based Secrets (Production)

Use file-based secrets for sensitive data. Two approaches available:

**Approach A: Simple Volume Mount (Recommended)**

1. Create secret file:

   ```bash
   mkdir -p secrets
   echo "your_api_key" > secrets/tautulli_key
   ```

2. Mount secrets folder in docker-compose.yml:

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

The application automatically detects paths starting with `/` and reads the file content.

**Approach B: Docker Compose Secrets Syntax**

1. Create secret file (same as above)

2. Use Docker Compose secrets feature:

   ```yaml
   services:
     app:
       environment:
         - TAUTULLI_API_KEY=/run/secrets/tautulli_key
       secrets:
         - tautulli_key

   secrets:
     tautulli_key:
       file: ./secrets/tautulli_key
   ```

3. Reference in config.yml (same as Approach A)

Both approaches work identically. Approach A is simpler and more flexible.

## Files

- `config.yml.example` - Example configuration with all options documented
- `config.yml` - Your actual configuration (gitignored, not committed to repo)
- `README.md` - This file

## Security

⚠️ **Important**: The `config.yml` file is gitignored. Never commit real credentials to version control.

For maximum security, use Method 3 (File-Based Secrets) to keep sensitive values separate from the config file. Approach A (simple volume mount) is recommended for its simplicity and flexibility.
