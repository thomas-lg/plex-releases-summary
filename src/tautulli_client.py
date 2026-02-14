import requests
import logging
import time
from typing import Dict, Any

logger = logging.getLogger("plex-weekly.tautulli")


class TautulliClient:
    """Client for interacting with Tautulli API."""

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize Tautulli client.

        Args:
            base_url: Base URL of the Tautulli instance
            api_key: Tautulli API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _request(self, cmd: str, max_retries: int = 3, **params) -> Dict[str, Any]:
        """Make a request to Tautulli API with exponential backoff retry logic."""
        url = f"{self.base_url}/api/v2"
        query = {
            "apikey": self.api_key,
            "cmd": cmd,
            **params,
        }
        logger.debug("Requesting Tautulli: %s", cmd)

        last_exception = None
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, params=query, timeout=10)
                resp.raise_for_status()

                data = resp.json()
                if data.get("response", {}).get("result") != "success":
                    raise RuntimeError(f"Tautulli error: {data}")
                return data["response"]["data"]

            except (requests.RequestException, RuntimeError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        "Request failed (attempt %d/%d): %s. Retrying in %ds...",
                        attempt + 1, max_retries, e, wait_time
                    )
                    time.sleep(wait_time)
                else:
                    logger.error("Request failed after %d attempts: %s", max_retries, e)

        raise last_exception

    def get_recently_added(self, days: int = 7, count: int = 100) -> Dict[str, Any]:
        """
        Get recently added items from Tautulli.
        Note: Tautulli API doesn't support date filtering, so we retrieve
        a large number of items and filter client-side.
        """
        logger.debug("Requesting %d recently added items (will filter to last %d days client-side)", count, days)

        return self._request(
            "get_recently_added",
            count=count,
        )

    def get_server_identity(self) -> Dict[str, Any]:
        """
        Get Plex server identity information including machine identifier.

        Returns:
            Dict with server info including 'machine_identifier'
        """
        logger.debug("Requesting Plex server identity")
        return self._request("get_server_identity")
