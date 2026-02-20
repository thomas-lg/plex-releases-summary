"""Tautulli API client for fetching Plex media library data."""

import logging
import re
import time
from typing import TypedDict, TypeVar, cast

import requests
from pydantic import BaseModel, ConfigDict, ValidationError

# Type definitions for Tautulli API responses


class TautulliMediaItem(TypedDict, total=False):
    added_at: int | str
    grandparent_title: str
    media_index: int | str
    media_type: str
    parent_media_index: int | str
    parent_title: str
    rating_key: int | str
    title: str
    year: int | str


class TautulliRecentlyAdded(TypedDict, total=False):
    recently_added: list[TautulliMediaItem]


class TautulliServerIdentity(TypedDict, total=False):
    machine_identifier: str


TautulliRecentlyAddedPayload = TautulliRecentlyAdded | list[TautulliMediaItem]


# Pydantic models for runtime validation


class TautulliMediaItemModel(BaseModel):
    """Pydantic model for runtime validation of Tautulli media items."""

    model_config = ConfigDict(extra="allow")

    # Required fields
    added_at: int
    media_type: str
    title: str

    # Optional fields
    year: int | str | None = None
    grandparent_title: str | None = None
    parent_title: str | None = None
    parent_media_index: int | str | None = None
    media_index: int | str | None = None
    rating_key: int | str | None = None


class TautulliRecentlyAddedModel(BaseModel):
    """Pydantic model for runtime validation of Tautulli recently_added responses."""

    model_config = ConfigDict(extra="allow")

    recently_added: list[TautulliMediaItemModel]


class TautulliServerIdentityModel(BaseModel):
    """Pydantic model for runtime validation of Tautulli server identity."""

    model_config = ConfigDict(extra="allow")

    machine_identifier: str


logger = logging.getLogger(__name__)


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

    def _sanitize_exception(self, error: Exception) -> Exception:
        """
        Create a sanitized exception instance to avoid leaking credentials.

        Args:
            error: Exception to sanitize

        Returns:
            New exception with redacted message
        """
        safe_message = self._sanitize_error(error)
        return type(error)(safe_message)

    T = TypeVar("T", bound=BaseModel)

    def _validate_response(self, data: dict[str, object], model: type[T]) -> T:
        """
        Validate API response data using Pydantic model.

        Args:
            data: Raw response data from API
            model: Pydantic model class to validate against

        Returns:
            Validated model instance

        Raises:
            RuntimeError: If validation fails
        """
        try:
            return model.model_validate(data)
        except ValidationError as e:
            # Extract a concise error message
            errors = e.errors()
            error_details = "; ".join(
                [
                    f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" if err["loc"] else err["msg"]
                    for err in errors
                ]
            )
            sanitized_msg = self._sanitize_error(Exception(error_details))
            raise RuntimeError(f"Tautulli response validation failed: {sanitized_msg}") from None

    def _request(self, cmd: str, max_retries: int | None = None, **params) -> dict[str, object]:
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

                data = cast(dict[str, object], resp.json())
                response = cast(dict[str, object], data.get("response", {}))
                if response.get("result") != "success":
                    message = response.get("message", "unknown error")
                    raise RuntimeError(f"Tautulli command '{cmd}' returned unsuccessful response: {message}")
                response_payload = cast(dict[str, object], response.get("data", {}))
                return response_payload

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

        raise self._sanitize_exception(last_exception) from None

    def get_recently_added(self, days: int = 7, count: int = 100) -> TautulliRecentlyAddedPayload:
        """
        Get recently added items from Tautulli.

        Note: The Tautulli API doesn't support date filtering natively, so this method
        retrieves a batch of items and the caller must filter them client-side by timestamp.

        Args:
            days: Number of days to look back. Used only for debug logging; the actual
                date filtering is performed by the caller against each item's timestamp.
                This value is NOT forwarded to the Tautulli API.
            count: Maximum number of items to retrieve from API

        Returns:
            Dict containing Tautulli API response with 'recently_added' list of media items
        """
        logger.debug("Requesting %d recently added items (will filter to last %d days client-side)", count, days)

        response_payload = self._request(
            "get_recently_added",
            count=count,
        )

        # Validate response - handle both dict and list formats
        # Try dict format first (newer API)
        if isinstance(response_payload, dict) and "recently_added" in response_payload:
            validated = self._validate_response(response_payload, TautulliRecentlyAddedModel)
            return cast(TautulliRecentlyAddedPayload, validated.model_dump())
        elif isinstance(response_payload, list):
            # List format (older API)
            validated_items = [
                self._validate_response(cast(dict[str, object], item), TautulliMediaItemModel)
                for item in response_payload
            ]
            return cast(TautulliRecentlyAddedPayload, [item.model_dump() for item in validated_items])
        else:
            raise RuntimeError(f"Unexpected response format: {type(response_payload).__name__}")

    def get_server_identity(self) -> TautulliServerIdentity:
        """
        Get Plex server identity information including machine identifier.

        Returns:
            Dict with server info including 'machine_identifier'
        """
        logger.debug("Requesting Plex server identity")
        response_payload = self._request("get_server_identity")
        validated = self._validate_response(response_payload, TautulliServerIdentityModel)
        return cast(TautulliServerIdentity, validated.model_dump())
