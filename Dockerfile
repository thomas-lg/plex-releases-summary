FROM python:3.14-slim

# Metadata labels
LABEL org.opencontainers.image.title="Plex Releases Summary"
LABEL org.opencontainers.image.description="Fetches and displays recently added media items from Plex via Tautulli"
LABEL org.opencontainers.image.authors="Plex Releases Summary Contributors"
LABEL org.opencontainers.image.url="https://github.com/thomas-lg/plex-releases-summary"
LABEL org.opencontainers.image.source="https://github.com/thomas-lg/plex-releases-summary"
LABEL org.opencontainers.image.licenses="MIT"

# Prevent Python from writing bytecode files
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install gosu for privilege dropping
RUN apt-get update && \
    apt-get install -y --no-install-recommends gosu && \
    rm -rf /var/lib/apt/lists/* && \
    gosu nobody true

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY configs/config.yml config.yml.default
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create default user (will be modified by entrypoint based on PUID/PGID)
RUN useradd -m -u 1000 appuser

# SECURITY NOTE:
# The entrypoint is invoked as root so it can adjust file ownership/permissions
# according to the requested PUID/PGID before the main process starts. This
# briefly increases the attack surface during initialization, so the logic in
# entrypoint.sh must remain minimal, well-audited, and should drop privileges
# with gosu to the unprivileged user (appuser) as early as possible.
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "src/app.py"]
