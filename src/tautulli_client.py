"""Tautulli API client for fetching Plex media library data."""

import logging
import re
import time
from typing import Any, cast

import requests

logger = logging.getLogger("plex-weekly.tautulli")


class TautulliClient:
    """Client for interacting with Tautulli API."""

    # Request configuration
    DEFAULT_TIMEOUT = 10  # seconds
    DEFAULT_MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # Exponential backoff base (1s, 2s, 4s, ...)
    APIKEY_PATTERN = re.compile(r"(apikey=)[^&\s]+", re.IGNORECASE)

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize Tautulli client.

        Args:
            base_url: Base URL of the Tautulli instance
            api_key: Tautulli API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _sanitize_error(self, error: Exception) -> str:
        """
        Sanitize exception text to avoid leaking credentials.

        Args:
            error: Exception to sanitize

        Returns:
            Redacted exception message
        """
        message = str(error)
        if self.api_key:
            message = message.replace(self.api_key, "***")
        return self.APIKEY_PATTERN.sub(r"\1***", message)

    def _request(self, cmd: str, max_retries: int | None = None, **params) -> dict[str, Any]:
        """
        Make a request to Tautulli API with exponential backoff retry logic.

        Args:
            cmd: Tautulli API command to execute
            max_retries: Maximum number of retry attempts (default: DEFAULT_MAX_RETRIES)
            **params: Additional query parameters for the API request

        Returns:
            Dict containing the API response data

        Raises:
            requests.RequestException: If request fails after all retries
            RuntimeError: If Tautulli returns unsuccessful response
        """
        if max_retries is None:
            max_retries = self.DEFAULT_MAX_RETRIES

        url = f"{self.base_url}/api/v2"
        query = {
            "apikey": self.api_key,
            "cmd": cmd,
            **params,
        }
        logger.debug("Requesting Tautulli: %s", cmd)

        last_exception: Exception = RuntimeError("No attempts made")
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, params=query, timeout=self.DEFAULT_TIMEOUT)
                resp.raise_for_status()

                data = resp.json()
                if data.get("response", {}).get("result") != "success":
                    response_data = cast(dict[str, Any], data.get("response", {}))
                    message = response_data.get("message", "unknown error")
                    raise RuntimeError(f"Tautulli command '{cmd}' returned unsuccessful response: {message}")
                return cast(dict[str, Any], data["response"]["data"])

            except (requests.RequestException, RuntimeError) as e:
                last_exception = e
                safe_error = self._sanitize_error(e)
                if attempt < max_retries - 1:
                    wait_time = self.RETRY_BACKOFF_BASE**attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        "Request failed for cmd=%s (attempt %d/%d): %s. Retrying in %ds...",
                        cmd,
                        attempt + 1,
                        max_retries,
                        safe_error,
                        wait_time,
                    )
                    time.sleep(wait_time)
                else:
                    logger.error("Request failed for cmd=%s after %d attempts: %s", cmd, max_retries, safe_error)

        raise last_exception

    def get_recently_added(self, days: int = 7, count: int = 100) -> dict[str, Any]:
        """
        Get recently added items from Tautulli.

        Note: The Tautulli API doesn't support date filtering natively, so this method
        retrieves a batch of items and the caller must filter them client-side by timestamp.

        Args:
            days: Number of days to look back (used for logging; actual filtering happens in caller)
            count: Maximum number of items to retrieve from API

        Returns:
            Dict containing Tautulli API response with 'recently_added' list of media items
        """
        logger.debug("Requesting %d recently added items (will filter to last %d days client-side)", count, days)

        return self._request(
            "get_recently_added",
            count=count,
        )

    def get_server_identity(self) -> dict[str, Any]:
        """
        Get Plex server identity information including machine identifier.

        Returns:
            Dict with server info including 'machine_identifier'
        """
        logger.debug("Requesting Plex server identity")
        return self._request("get_server_identity")
