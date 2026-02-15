FROM python:3.12-slim

# Metadata labels
LABEL org.opencontainers.image.title="Plex Releases Summary"
LABEL org.opencontainers.image.description="Fetches and displays recently added media items from Plex via Tautulli"
LABEL org.opencontainers.image.authors="Plex Releases Summary Contributors"
LABEL org.opencontainers.image.url="https://github.com/thomas-lg/plex-releases-summary"
LABEL org.opencontainers.image.source="https://github.com/thomas-lg/plex-releases-summary"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY configs/config.yml config.yml.default
COPY entrypoint.sh .

# Make entrypoint executable and run as non-root user for security
RUN chmod +x entrypoint.sh && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "src/app.py"]