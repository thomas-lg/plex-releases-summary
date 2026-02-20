"""Discord webhook client for sending Plex release summaries."""

import logging
import random
import re
import time
from datetime import datetime
from typing import Any, NotRequired, TypedDict

from discord_webhook import DiscordEmbed, DiscordWebhook

# Type definitions for Discord payloads


class DiscordMediaItem(TypedDict):
    type: str
    title: str
    added_at: NotRequired[str]
    rating_key: NotRequired[int | str]


logger = logging.getLogger(__name__)


def _escape_title_markdown(text: str) -> str:
    """
    Escape markdown metacharacters that can alter a title's visible text.
    This keeps titles looking raw in Discord while preventing emphasis, code,
    and link-text parsing from changing what the user sees.

    Args:
        text: Text that may contain markdown characters

    Returns:
        Text with markdown characters escaped
    """
    markdown_chars = r"([\\`*_~\[\]])"
    return re.sub(markdown_chars, r"\\\1", text)


class DiscordNotifier:
    """Handles sending Plex release summaries to Discord via webhook."""

    # Discord limits
    MAX_FIELD_VALUE = 1024
    MAX_ITEMS_TOTAL = 25  # Discord embed hard limit: 25 fields per embed
    EMBED_SIZE_BUFFER = 5800  # Safety buffer below 6000 to account for JSON overhead

    # Retry configuration
    MAX_SEND_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # Exponential backoff base (1s, 2s, 4s, ...)
    REQUEST_TIMEOUT_SECONDS = 15

    # Embed trimming configuration
    MAX_TRIM_ATTEMPTS = 5
    TRIM_REDUCTION_FACTOR = 0.8  # Reduce by 20% on each attempt

    # Emoji icons for media types
    MEDIA_ICONS = {
        "Movies": "🎬",
        "TV Shows": "📺",
        "TV Seasons": "📺",
        "TV Episodes": "📺",
        "Music Albums": "💿",
        "Music Tracks": "🎵",
    }

    # Friendly empty-state messages when no new media is found
    NO_NEW_TITLES = [
        "🛋️ Quiet Plex vibes",
        "🍃 Nothing new this round",
        "📭 No fresh arrivals",
        "🌙 Calm library check-in",
    ]

    NO_NEW_MESSAGES = [
        "No new releases in the last {days} {day_word}. Time to add something awesome to the library 🍿",
        "Your Plex library stayed peaceful for {days} {day_word}. Maybe tonight is a perfect time to queue a new download ✨",
        "Nothing new landed in the past {days} {day_word}. Give your future self a surprise and add something fun 🎬",
        "No new content in {days} {day_word}. Friendly reminder: your watchlist won’t fill itself 😄",
    ]

    def __init__(self, webhook_url: str, plex_url: str | None = None, plex_server_id: str | None = None):
        """
        Initialize Discord notifier.

        Args:
            webhook_url: Discord webhook URL for the target channel
            plex_url: Optional Plex server URL (e.g., 'https://app.plex.tv' or 'http://plex:32400')
            plex_server_id: Optional Plex server machine identifier for creating direct links
        """
        self.webhook_url = webhook_url
        self.plex_url = plex_url.rstrip("/") if plex_url else None
        self.plex_server_id = plex_server_id

    def send_summary(self, media_items: list[DiscordMediaItem], days_back: int, total_count: int) -> bool:
        """
        Send media summary to Discord as rich embed(s), grouped by category.
        Sends separate messages for each media type (Movies, TV Shows, etc.).

        Args:
            media_items: List of media items with 'type', 'title', 'added_at' keys
            days_back: Number of days included in the summary
            total_count: Total number of items found

        Returns:
            bool: True if all messages sent successfully, False otherwise
        """
        try:
            if not media_items or total_count == 0:
                webhook = DiscordWebhook(url=self.webhook_url)
                webhook.add_embed(self._create_no_new_items_embed(days_back))

                response = self._send_with_retry(webhook)
                if response.status_code in [200, 204]:
                    logger.info("✅ Discord no-new-items notification sent")
                    return True

                if response.status_code == 400:
                    logger.error("Discord rejected no-new-items message (invalid payload): %s", response.text)
                else:
                    logger.error(
                        "Discord webhook failed with status %d for no-new-items message: %s",
                        response.status_code,
                        response.text,
                    )
                return False

            # Group items by type
            grouped = self._group_items_by_type(media_items)

            # Category order for display
            category_order = ["Movies", "TV Shows", "TV Seasons", "TV Episodes", "Music Albums", "Music Tracks"]

            total_messages = 0
            success_count = 0

            # Send messages for each category
            for category in category_order:
                items = grouped.get(category, [])
                if not items:
                    continue

                # Sort items by date (ascending - oldest first)
                items.sort(key=lambda x: x.get("added_at", ""))

                # Send items in chunks, handling dynamic sizing based on validation
                items_remaining = items[:]
                part_num = 1

                while items_remaining:
                    total_messages += 1

                    # Try to send a chunk (start with MAX_ITEMS_TOTAL)
                    chunk = items_remaining[: self.MAX_ITEMS_TOTAL]

                    webhook = DiscordWebhook(url=self.webhook_url)

                    # Create and validate embed - this may trim items if too large
                    embed, items_sent = self._validate_and_trim_embed(
                        category, chunk, days_back, total_count, part_num, len(items), items_remaining
                    )
                    webhook.add_embed(embed)

                    # Send with retry logic
                    response = self._send_with_retry(webhook)

                    if response.status_code in [200, 204]:
                        success_count += 1

                        # Remove sent items from remaining
                        items_remaining = items_remaining[items_sent:]

                        if items_remaining:
                            logger.info(
                                "✅ Discord notification sent: %s (part %d, %d items sent, %d remaining)",
                                category,
                                part_num,
                                items_sent,
                                len(items_remaining),
                            )
                        else:
                            logger.info("✅ Discord notification sent: %s (%d items total)", category, len(items))

                        part_num += 1

                        # Small delay between messages to avoid rate limits
                        if items_remaining:
                            time.sleep(0.5)
                    elif response.status_code == 400:
                        logger.error(
                            "Discord rejected message (invalid payload): %s (%s part %d). "
                            "Embed may be malformed or exceed limits. Skipping remaining %d items.",
                            response.text,
                            category,
                            part_num,
                            len(items_remaining),
                        )
                        break  # Stop trying to send this category
                    else:
                        logger.error(
                            "Discord webhook failed with status %d: %s (%s part %d)",
                            response.status_code,
                            response.text,
                            category,
                            part_num,
                        )
                        break  # Stop trying to send this category

            logger.info("✅ All Discord notifications sent (%d/%d messages)", success_count, total_messages)
            return success_count == total_messages

        except (ConnectionError, TimeoutError) as e:
            logger.error("Network error sending Discord notification: %s", e)
            return False
        except ValueError as e:
            logger.error("Invalid data for Discord notification: %s", e)
            return False
        except Exception as e:
            logger.exception("Unexpected error sending Discord notification: %s", e)
            return False

    def _create_no_new_items_embed(self, days_back: int) -> DiscordEmbed:
        """Create a friendly embed for periods with no new items."""
        day_word = "day" if days_back == 1 else "days"
        title = random.choice(self.NO_NEW_TITLES)
        description = random.choice(self.NO_NEW_MESSAGES).format(days=days_back, day_word=day_word)

        embed = DiscordEmbed(title=title, description=description, color=0x5865F2)
        embed.set_footer(text=f"Checked on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        embed.set_timestamp()
        return embed

    def _create_category_embed(
        self,
        category: str,
        items: list[DiscordMediaItem],
        days_back: int,
        part_num: int,
        estimated_parts: int,
        category_total: int,
    ) -> DiscordEmbed:
        """Create Discord embed for a specific category."""
        date_range = f"Last {days_back} day{'s' if days_back != 1 else ''}"
        icon = self.MEDIA_ICONS.get(category, "📁")

        # Build title
        if estimated_parts > 1 or part_num > 1:
            title = f"{icon} {category} - {date_range} (Part {part_num})"
        else:
            title = f"{icon} {category} - {date_range}"

        # Build description - just show category count to avoid confusion
        if category_total == 1:
            description = f"**{category_total} {category[:-1].lower()} added**"  # Singular
        else:
            description = f"**{category_total} {category.lower()} added**"

        embed = DiscordEmbed(title=title, description=description, color=0x57F287)  # Green color

        # Add all items in this chunk with their dates for range calculation
        self._add_items_to_embed(embed, items, category)

        # Add footer with timestamp
        embed.set_footer(text=f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        embed.set_timestamp()

        return embed

    def _calculate_embed_size(self, embed: DiscordEmbed) -> int:
        """
        Calculate the approximate total character count of an embed.

        Discord counts: title + description + fields (name + value) + footer + author

        Returns:
            Total character count of the embed
        """
        total = 0

        # Title
        if embed.title:
            total += len(embed.title)

        # Description
        if embed.description:
            total += len(embed.description)

        # Fields
        for field in embed.fields:
            name = field.get("name")
            if name:
                total += len(str(name))
            value = field.get("value")
            if value:
                total += len(str(value))

        # Footer
        if embed.footer:
            footer_text = embed.footer.get("text")
            if footer_text:
                total += len(footer_text)

        # Author
        if embed.author:
            author_name = embed.author.get("name")
            if author_name:
                total += len(author_name)

        return total

    def _validate_and_trim_embed(
        self,
        category: str,
        items: list[DiscordMediaItem],
        days_back: int,
        total_count: int,
        part_num: int,
        category_total: int,
        all_items: list[DiscordMediaItem],
    ) -> tuple[DiscordEmbed, int]:
        """
        Create embed and validate size, trimming items if necessary to stay under Discord limits.

        Args:
            category: Media category name
            items: List of media items to attempt to include
            days_back: Number of days in the summary
            total_count: Total count across all categories
            part_num: Current part number
            category_total: Total items in this category
            all_items: All remaining items (for calculating parts)

        Returns:
            Tuple of (DiscordEmbed, number of items actually included)
        """
        current_items = items[:]

        for attempt in range(self.MAX_TRIM_ATTEMPTS):
            # Calculate how many parts we might need (estimate)
            items_per_part = len(current_items)
            estimated_parts = (len(all_items) + items_per_part - 1) // items_per_part if items_per_part > 0 else 1

            embed = self._create_category_embed(
                category, current_items, days_back, total_count, part_num, estimated_parts
            )

            size = self._calculate_embed_size(embed)

            # Check if within safe limits (with buffer)
            if size <= self.EMBED_SIZE_BUFFER:
                if len(current_items) < len(items):
                    removed = len(items) - len(current_items)
                    logger.warning(
                        "⚠️  Trimmed %d items from %s part %d to fit Discord size limit (final size: %d chars). "
                        "These items will be sent in the next message.",
                        removed,
                        category,
                        part_num,
                        size,
                    )
                return embed, len(current_items)

            # Too large, remove 20% of items and try again
            if len(current_items) <= 1:
                # Can't reduce further, log error and return as-is
                logger.error(
                    "❌ Cannot reduce %s embed further (current size: %d chars, limit: %d). "
                    "Discord may reject this message.",
                    category,
                    size,
                    self.EMBED_SIZE_BUFFER,
                )
                return embed, len(current_items)

            new_count = max(1, int(len(current_items) * self.TRIM_REDUCTION_FACTOR))
            logger.warning(
                "⚠️  Embed too large (%d chars), reducing %s from %d to %d items (attempt %d/%d)",
                size,
                category,
                len(current_items),
                new_count,
                attempt + 1,
                self.MAX_TRIM_ATTEMPTS,
            )
            current_items = current_items[:new_count]

        # Return the smallest version we managed to create
        return embed, len(current_items)

    def _add_items_to_embed(self, embed: DiscordEmbed, items: list[DiscordMediaItem], category: str) -> None:
        """Add items to embed, splitting into multiple fields if needed with date ranges."""
        current_chunk: list[str] = []
        current_chunk_items: list[DiscordMediaItem] = []  # Track items for date range
        current_chars = 0
        chunk_num = 1

        for item in items:
            item_text = self._format_media_item(item)
            item_length = len(item_text) + 1  # +1 for newline

            # Check if adding this item would exceed field limit
            if current_chars + item_length > self.MAX_FIELD_VALUE - 50 and current_chunk:
                # Add current chunk as a field
                field_name = self._get_date_range_field_name(current_chunk_items, chunk_num)
                field_value = "\n".join(current_chunk)
                embed.add_embed_field(name=field_name, value=field_value, inline=False)
                chunk_num += 1
                current_chunk = []
                current_chunk_items = []
                current_chars = 0

            current_chunk.append(item_text)
            current_chunk_items.append(item)
            current_chars += item_length

        # Add final chunk
        if current_chunk:
            field_name = self._get_date_range_field_name(current_chunk_items, chunk_num)
            field_value = "\n".join(current_chunk)
            embed.add_embed_field(name=field_name, value=field_value, inline=False)

    def _get_date_range_field_name(self, items: list[DiscordMediaItem], chunk_num: int) -> str:
        """Generate field name with date range in DD/MM - DD/MM format."""
        if not items:
            return f"Items ({chunk_num})" if chunk_num > 1 else "Items"

        # Items are sorted by date ascending, so first is oldest, last is newest
        first_date = items[0].get("added_at", "")
        last_date = items[-1].get("added_at", "")

        # Parse ISO date format (YYYY-MM-DD) and format as DD/MM for display
        try:
            first_dt = datetime.strptime(first_date, "%Y-%m-%d")
            last_dt = datetime.strptime(last_date, "%Y-%m-%d")
            first_formatted = first_dt.strftime("%d/%m")
            last_formatted = last_dt.strftime("%d/%m")

            if first_formatted == last_formatted:
                return first_formatted
            else:
                return f"{first_formatted} - {last_formatted}"
        except (ValueError, AttributeError):
            logger.debug("Failed to parse date format for field name, using fallback")

        return f"Items ({chunk_num})" if chunk_num > 1 else "Items"

    def _group_items_by_type(self, media_items: list[DiscordMediaItem]) -> dict[str, list[DiscordMediaItem]]:
        """Group media items by type."""
        grouped: dict[str, list[DiscordMediaItem]] = {
            "Movies": [],
            "TV Shows": [],
            "TV Seasons": [],
            "TV Episodes": [],
            "Music Albums": [],
            "Music Tracks": [],
        }

        for item in media_items:
            media_type = item.get("type", "unknown")

            if media_type == "movie":
                grouped["Movies"].append(item)
            elif media_type == "show":
                grouped["TV Shows"].append(item)
            elif media_type == "season":
                grouped["TV Seasons"].append(item)
            elif media_type == "episode":
                grouped["TV Episodes"].append(item)
            elif media_type == "album":
                grouped["Music Albums"].append(item)
            elif media_type == "track":
                grouped["Music Tracks"].append(item)
            else:
                logger.warning("Unrecognized media type: %s — item will be skipped", media_type)

        return grouped

    def _format_media_item(self, item: DiscordMediaItem) -> str:
        """Format a single media item for display."""
        title = item.get("title", "Unknown")
        rating_key = item.get("rating_key")

        # Escape only markdown characters that would alter the visible title
        safe_title = _escape_title_markdown(title)

        # Create clickable link to Plex if URL and server ID are available
        if self.plex_url and self.plex_server_id and rating_key:
            # URL encode the library path
            encoded_key = f"%2Flibrary%2Fmetadata%2F{rating_key}"

            # Check if using Plex.tv or local Plex server
            if "plex.tv" in self.plex_url.lower():
                # Plex.tv format
                link_url = f"{self.plex_url}/desktop#!/server/{self.plex_server_id}/details?key={encoded_key}"
            else:
                # Local Plex server format
                link_url = f"{self.plex_url}/web/index.html#!/server/{self.plex_server_id}/details?key={encoded_key}"

            display_title = f"[{safe_title}]({link_url})"
        else:
            display_title = f"**{safe_title}**"

        # Format based on type (year already included in title from app.py)
        return f"• {display_title}"

    def _send_with_retry(self, webhook: DiscordWebhook, max_retries: int | None = None) -> Any:
        """
        Send webhook with retry logic for rate limits and transient failures.

        Args:
            webhook: The Discord webhook to send
            max_retries: Maximum number of retry attempts (default: MAX_SEND_RETRIES)

        Returns:
            Response object from the webhook execution
        """
        if max_retries is None:
            max_retries = self.MAX_SEND_RETRIES

        if max_retries == 0:
            raise ValueError("max_retries must be at least 1")

        response = None
        for attempt in range(max_retries):
            try:
                try:
                    # Prefer passing timeout as a keyword argument (discord-webhook 1.x style)
                    response = webhook.execute(timeout=self.REQUEST_TIMEOUT_SECONDS)  # type: ignore[call-arg]
                except TypeError:
                    # Fallback for older or non-standard implementations that use a timeout attribute
                    if hasattr(webhook, "timeout"):
                        webhook.timeout = self.REQUEST_TIMEOUT_SECONDS
                        response = webhook.execute()
                    else:
                        # Re-raise if neither the kwarg nor the attribute is supported
                        raise

                # If validation error (bad request), don't retry - it won't help
                if response.status_code == 400:
                    logger.error("Discord webhook validation failed (400 Bad Request): %s", response.text)
                    return response

                # If rate limited, wait and retry
                if response.status_code == 429:
                    retry_after = response.json().get("retry_after", 1)
                    logger.warning(
                        "Discord rate limit hit, retrying after %ss (attempt %d/%d)",
                        retry_after,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(retry_after)
                    continue

                return response

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = self.RETRY_BACKOFF_BASE**attempt  # Exponential backoff
                    logger.warning(
                        "Discord webhook attempt %d failed: %s. Retrying in %ds...", attempt + 1, e, wait_time
                    )
                    time.sleep(wait_time)
                else:
                    raise

        # This point is only reached if every attempt hit the rate-limit path
        # without a successful response; callers should check for None.
        assert response is not None, "_send_with_retry exhausted retries without raising"
        return response
