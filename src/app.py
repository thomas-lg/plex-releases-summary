import logging
import sys
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from config import Config, get_bootstrap_log_level, load_config
from discord_client import DiscordNotifier
from logging_config import setup_logging
from tautulli_client import TautulliClient

logger = logging.getLogger("plex-weekly")

# Constants
DEFAULT_INFO_DISPLAY_LIMIT = 10  # Number of items to display in INFO log level


def _calculate_batch_params(days: int, override: int | None = None) -> tuple[int, int]:
    """
    Calculate initial batch size and increment based on time range.

    Args:
        days: Number of days to look back
        override: Optional override value from environment variable

    Returns:
        Tuple of (initial_count, increment)
    """
    if override is not None:
        return (override, override)

    if days <= 7:
        return (100, 100)
    elif days <= 30:
        return (200, 200)
    else:
        return (500, 500)


def _format_display_title(item: dict[str, Any]) -> str:
    """
    Format display title based on media type.

    Args:
        item: Media item dictionary from Tautulli

    Returns:
        Formatted display title string
    """
    media_type = item.get("media_type", "unknown")

    if media_type == "episode":
        show = item.get("grandparent_title", "Unknown Show")
        season_num = item.get("parent_media_index", "?")
        episode_num = item.get("media_index", "?")
        episode_title = item.get("title", "Unknown Episode")
        # Format episode numbers safely, handling non-integer values
        try:
            s_num = int(season_num) if season_num != "?" else 0
            e_num = int(episode_num) if episode_num != "?" else 0
            return f"{show} - S{s_num:02d}E{e_num:02d} - {episode_title}"
        except (ValueError, TypeError):
            return f"{show} - S{season_num}E{episode_num} - {episode_title}"
    elif media_type == "season":
        show = item.get("parent_title", "Unknown Show")
        season_num = item.get("media_index", "?")
        return f"{show} - Season {season_num}"
    elif media_type == "show":
        show = item.get("title", "Unknown Show")
        year = item.get("year", "")
        return f"{show}" + (f" ({year})" if year else " (New Series)")
    elif media_type == "track":
        artist = item.get("grandparent_title", "Unknown Artist")
        album = item.get("parent_title", "Unknown Album")
        track = item.get("title", "Unknown Track")
        return f"{artist} - {album} - {track}"
    elif media_type == "album":
        artist = item.get("parent_title", "Unknown Artist")
        album = item.get("title", "Unknown Album")
        return f"{artist} - {album}"
    elif media_type == "movie":
        title = item.get("title", "Unknown Movie")
        year = item.get("year", "")
        return f"{title}" + (f" ({year})" if year else "")
    else:
        title = item.get("title", "Unknown")
        return str(title)


def run_summary(config: Config) -> int:
    """
    Execute the Plex summary task: fetch and display recently added media.

    Args:
        config: Application configuration

    Returns:
        Exit code: 0 for success, 1 for error
    """
    logger.info("🚀 Plex weekly summary starting")

    days = config.days_back
    logger.info("Configuration: Looking back %d days", days)

    tautulli = TautulliClient(
        base_url=config.tautulli_url,
        api_key=config.tautulli_api_key,
    )

    # Query items with date filter
    # Fetch items iteratively since Tautulli API lacks date filtering (see TautulliClient.get_recently_added)
    logger.info("Querying recently added items with iterative fetching...")

    # Calculate cutoff timestamp for filtering
    cutoff_timestamp = int((datetime.now(UTC) - timedelta(days=days)).timestamp())
    logger.debug("Filtering items to show only those added after timestamp: %d", cutoff_timestamp)

    # Calculate batch parameters based on time range
    initial_count, increment = _calculate_batch_params(days, override=config.initial_batch_size)
    current_count = initial_count
    iteration = 0
    items = []

    # Iteratively fetch items until we get items beyond the time range
    while True:
        iteration += 1
        logger.debug("Iteration %d: Fetching batch with count=%d", iteration, current_count)

        # Add small delay between iterations to avoid hammering the API
        if iteration > 1:
            time.sleep(0.2)

        try:
            items_raw = tautulli.get_recently_added(days=days, count=current_count)
        except (ConnectionError, TimeoutError) as e:
            logger.error("Network error while fetching recently added items: %s", e)
            return 1
        except ValueError as e:
            logger.error("Invalid response from Tautulli API: %s", e)
            return 1
        except Exception as e:
            logger.exception("Unexpected error while fetching recently added items: %s", e)
            return 1

        # depending on API version, the data is inside 'recently_added'
        if isinstance(items_raw, dict) and "recently_added" in items_raw:
            items = items_raw["recently_added"]
        elif isinstance(items_raw, list):
            items = items_raw
        else:
            items = []

        # Break if no items returned
        if not items:
            logger.debug("No items returned, stopping iteration")
            break

        # If we received fewer items than requested, we've hit the API's limit
        if len(items) < current_count:
            logger.debug("Received %d items (less than requested %d), reached API limit", len(items), current_count)
            break

        # Check if oldest item is still within time range
        oldest_timestamp = int(items[-1].get("added_at", 0))

        if oldest_timestamp >= cutoff_timestamp:
            # Oldest item is still in range, need to fetch more
            logger.info(
                "Oldest item still in range (iteration %d), fetching more items (next count: %d)",
                iteration,
                current_count + increment,
            )
            current_count += increment
        else:
            # We've fetched beyond the time range, we're done
            logger.debug("Fetched beyond time range after %d iteration(s)", iteration)
            break

    # Filter items client-side by date
    items_before_filter = len(items)
    items = [item for item in items if int(item.get("added_at", 0)) >= cutoff_timestamp]

    if iteration > 1:
        logger.info(
            "Retrieved %d items in %d iterations, filtered to %d items from last %d days",
            items_before_filter,
            iteration,
            len(items),
            days,
        )
    else:
        logger.info("Retrieved %d items, filtered to %d items from last %d days", items_before_filter, len(items), days)

    logger.info("Found %d recent items matching criteria", len(items))

    # Prepare structured data for Discord and display items in logs
    discord_items = []
    suppressed_by_type: dict[str, int] = {}
    displayed_by_type: dict[str, int] = {}
    debug_enabled = logger.isEnabledFor(logging.DEBUG)

    for item in items:
        added_at = int(item.get("added_at", 0))
        date_str = datetime.fromtimestamp(added_at, tz=UTC).strftime("%Y-%m-%d %H:%M")
        date_str_short = datetime.fromtimestamp(added_at, tz=UTC).strftime("%m/%d")
        media_type = item.get("media_type", "unknown")
        display_title = _format_display_title(item)

        if debug_enabled:
            logger.info("➕ %s | added: %s", display_title, date_str)
        else:
            shown_count = displayed_by_type.get(media_type, 0)
            if shown_count < DEFAULT_INFO_DISPLAY_LIMIT:
                logger.info("➕ %s | added: %s", display_title, date_str)
                displayed_by_type[media_type] = shown_count + 1
            else:
                suppressed_by_type[media_type] = suppressed_by_type.get(media_type, 0) + 1

        discord_items.append(
            {
                "type": media_type,
                "title": display_title,
                "added_at": date_str_short,
                "rating_key": item.get("rating_key"),
            }
        )

    if suppressed_by_type:
        suppressed_summary = ", ".join(
            f"{media_type}: {count}" for media_type, count in sorted(suppressed_by_type.items())
        )
        logger.info(
            "... additional items hidden at INFO level by type (%s). "
            "Set log_level: DEBUG in config.yml to see all entries.",
            suppressed_summary,
        )

    # Summary
    logger.info("✅ Summary complete: Found %d items in the last %d days", len(items), days)

    # Send Discord notification if webhook URL is configured
    if config.discord_webhook_url:
        logger.debug("Discord webhook URL configured, sending notification...")
        try:
            plex_server_id = config.plex_server_id

            # Auto-fetch Plex Server ID from Tautulli if not provided
            if not plex_server_id:
                logger.debug("plex_server_id not configured, fetching from Tautulli...")
                try:
                    server_info = tautulli.get_server_identity()
                    plex_server_id = server_info.get("machine_identifier")
                    if plex_server_id:
                        logger.info("Auto-detected Plex Server ID: %s", plex_server_id)
                    else:
                        logger.warning("Could not auto-detect Plex Server ID from Tautulli")
                except (ConnectionError, TimeoutError) as e:
                    logger.warning("Network error while fetching Plex Server ID: %s", e)
                except ValueError as e:
                    logger.warning("Invalid response from Tautulli: %s", e)

            notifier = DiscordNotifier(config.discord_webhook_url, config.plex_url, plex_server_id)
            notifier.send_summary(discord_items, days, len(items))
        except (ConnectionError, TimeoutError) as e:
            logger.error("Network error while sending Discord notification: %s", e)
            if config.run_once:
                return 1
        except ValueError as e:
            logger.error("Invalid Discord webhook configuration: %s", e)
            if config.run_once:
                return 1
        except Exception as e:
            logger.exception("Unexpected error while sending Discord notification: %s", e)
            if config.run_once:
                return 1
    else:
        logger.debug("No Discord webhook URL configured, skipping Discord notification")

    return 0  # Success


def main():
    """
    Main entry point: Choose between scheduled or one-shot execution mode.

    Execution mode is configured via config.yml:
      - set run_once: true to run once and exit
      - or provide cron_schedule to run as a persistent scheduled task
    """
    # Bootstrap logging level from raw config so load-time logs honor user verbosity
    setup_logging(get_bootstrap_log_level())
    try:
        config = load_config()
    except Exception as e:
        logger.exception("FATAL: Failed to load configuration: %s", e)
        return 1

    # Now setup logging with config
    setup_logging(config.log_level)
    logger.info("Configuration loaded successfully")

    if config.run_once:
        # One-shot mode: run once and exit
        logger.info("▶️  Starting in ONE-SHOT mode (run_once=true)")
        return run_summary(config)
    else:
        # Scheduled mode: run as daemon with CRON schedule
        logger.info("📅 Starting in SCHEDULED mode")
        from scheduler import run_scheduled

        assert config.cron_schedule is not None

        # Wrap run_summary to pass config
        return run_scheduled(lambda: run_summary(config), config.cron_schedule)


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)
