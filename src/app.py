import os
import sys
import logging
from datetime import datetime, timedelta, timezone

from logging_config import setup_logging
from tautulli_client import TautulliClient

setup_logging()
logger = logging.getLogger("plex-weekly")


def run_summary() -> int:
    """
    Execute the Plex summary task: fetch and display recently added media.
    
    Returns:
        Exit code: 0 for success, 1 for error
    """
    logger.info("🚀 Plex weekly summary starting")

    # Validate required environment variables
    if "DAYS_BACK" not in os.environ:
        logger.error("DAYS_BACK environment variable is required but not set")
        return 1  # Exit with error code
    
    try:
        days = int(os.environ["DAYS_BACK"])
    except (KeyError, ValueError) as e:
        logger.error("Invalid DAYS_BACK configuration: %s", e)
        return 1
    
    logger.info("Configuration: Looking back %d days", days)

    try:
        tautulli = TautulliClient(
            base_url=os.environ["TAUTULLI_URL"],
            api_key=os.environ["TAUTULLI_API_KEY"],
        )
    except KeyError as e:
        logger.error("Missing required environment variable: %s", e)
        return 1

    # Query items with date filter
    # Note: Tautulli API doesn't support date filtering, we get the most recent items and filter client-side
    logger.info("Querying recently added items...")
    
    try:
        items_raw = tautulli.get_recently_added(days=days, count=500)
    except Exception as e:
        logger.error("Failed to fetch recently added items: %s", e)
        return 1

    # depending on API version, the data is inside 'recently_added'
    if isinstance(items_raw, dict) and "recently_added" in items_raw:
        items = items_raw["recently_added"]
    elif isinstance(items_raw, list):
        items = items_raw
    else:
        items = []

    # Filter items client-side by date (Tautulli API doesn't support date filtering)
    cutoff_timestamp = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    logger.debug("Filtering items to show only those added after timestamp: %d", cutoff_timestamp)
    items_before_filter = len(items)
    items = [item for item in items if int(item.get("added_at", 0)) >= cutoff_timestamp]
    
    logger.info("Retrieved %d items, filtered to %d items from last %d days", 
                items_before_filter, len(items), days)

    logger.info("Found %d recent items matching criteria", len(items))

    # Display items (limit to first 10 in INFO, show all in DEBUG)
    display_count = len(items) if logger.isEnabledFor(logging.DEBUG) else min(10, len(items))
    for item in items[:display_count]:
        added_at = int(item.get("added_at", 0))
        date_str = datetime.fromtimestamp(added_at, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        media_type = item.get("media_type", "unknown")
        
        # Format the display based on media type
        if media_type == "episode":
            show = item.get("grandparent_title", "Unknown Show")
            season_num = item.get("parent_media_index", "?")
            episode_num = item.get("media_index", "?")
            episode_title = item.get("title", "Unknown Episode")
            # Format episode numbers safely, handling non-integer values
            try:
                s_num = int(season_num) if season_num != "?" else 0
                e_num = int(episode_num) if episode_num != "?" else 0
                display_title = f"{show} - S{s_num:02d}E{e_num:02d} - {episode_title}"
            except (ValueError, TypeError):
                display_title = f"{show} - S{season_num}E{episode_num} - {episode_title}"
        elif media_type == "season":
            show = item.get("parent_title", "Unknown Show")
            season_num = item.get("media_index", "?")
            display_title = f"{show} - Season {season_num}"
        elif media_type == "show":
            show = item.get("title", "Unknown Show")
            year = item.get("year", "")
            display_title = f"{show}" + (f" ({year})" if year else " (New Series)")
        elif media_type == "track":
            artist = item.get("grandparent_title", "Unknown Artist")
            album = item.get("parent_title", "Unknown Album")
            track = item.get("title", "Unknown Track")
            display_title = f"{artist} - {album} - {track}"
        elif media_type == "album":
            artist = item.get("parent_title", "Unknown Artist")
            album = item.get("title", "Unknown Album")
            display_title = f"{artist} - {album}"
        elif media_type == "movie":
            title = item.get("title", "Unknown Movie")
            year = item.get("year", "")
            display_title = f"{title}" + (f" ({year})" if year else "")
        else:
            display_title = item.get("title", "Unknown")
        
        logger.info("➕ %s | added: %s", display_title, date_str)
    
    if len(items) > display_count:
        logger.info("... and %d more items (set LOG_LEVEL=DEBUG to see all)", len(items) - display_count)

    # Summary
    logger.info("✅ Summary complete: Found %d items in the last %d days", len(items), days)
    return 0  # Success


def main():
    """
    Main entry point: Choose between scheduled or one-shot execution mode.
    
    If RUN_ONCE is true, run once and exit.
    Otherwise, run as a persistent scheduler with CRON schedule.
    """
    run_once = os.environ.get("RUN_ONCE", "false").lower() in ("true", "1", "yes")
    
    if run_once:
        # One-shot mode: run once and exit
        logger.info("▶️  Starting in ONE-SHOT mode (RUN_ONCE=true)")
        return run_summary()
    else:
        # Scheduled mode: run as daemon with CRON schedule
        logger.info("📅 Starting in SCHEDULED mode")
        from scheduler import run_scheduled
        return run_scheduled(run_summary)


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
