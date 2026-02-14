"""Discord webhook client for sending Plex release summaries."""

import logging
import time
from typing import List, Dict, Any, Optional
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Handles sending Plex release summaries to Discord via webhook."""

    # Discord limits
    MAX_EMBED_TOTAL = 6000  # Total characters for entire embed
    MAX_EMBED_DESCRIPTION = 4096
    MAX_FIELD_VALUE = 1024
    MAX_FIELDS = 25
    MAX_ITEMS_PER_FIELD = 20
    MAX_ITEMS_TOTAL = 30  # Limit total items to stay under 6000 char limit with URLs
    
    # Emoji icons for media types
    MEDIA_ICONS = {
        'Movies': '🎬',
        'TV Shows': '📺',
        'TV Seasons': '📺',
        'TV Episodes': '📺',
        'Music Albums': '💿',
        'Music Tracks': '🎵'
    }

    def __init__(self, webhook_url: str, plex_url: Optional[str] = None, plex_server_id: Optional[str] = None):
        """
        Initialize Discord notifier.

        Args:
            webhook_url: Discord webhook URL for the target channel
            plex_url: Optional Plex server URL (e.g., 'https://app.plex.tv' or 'http://plex:32400')
            plex_server_id: Optional Plex server machine identifier for creating direct links
        """
        self.webhook_url = webhook_url
        self.plex_url = plex_url.rstrip('/') if plex_url else None
        self.plex_server_id = plex_server_id

    def send_summary(
        self, 
        media_items: List[Dict[str, Any]], 
        days_back: int,
        total_count: int
    ) -> bool:
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
            # Group items by type
            grouped = self._group_items_by_type(media_items)
            
            # Category order for display
            category_order = ['Movies', 'TV Shows', 'TV Seasons', 'TV Episodes', 'Music Albums', 'Music Tracks']
            
            total_messages = 0
            success_count = 0
            
            # Send messages for each category
            for category in category_order:
                items = grouped.get(category, [])
                if not items:
                    continue
                
                # Sort items by date (ascending - oldest first)
                items.sort(key=lambda x: x.get('added_at', ''))
                
                # Split category into chunks if needed
                chunks = []
                for i in range(0, len(items), self.MAX_ITEMS_TOTAL):
                    chunks.append(items[i:i + self.MAX_ITEMS_TOTAL])
                
                # Send each chunk as a separate message
                for chunk_idx, chunk in enumerate(chunks, 1):
                    total_messages += 1
                    webhook = DiscordWebhook(url=self.webhook_url)
                    
                    # Create embed for this category chunk
                    embed = self._create_category_embed(
                        category, chunk, days_back, total_count,
                        chunk_idx, len(chunks), len(items)
                    )
                    webhook.add_embed(embed)

                    # Send with retry logic
                    response = self._send_with_retry(webhook)
                    
                    if response.status_code in [200, 204]:
                        success_count += 1
                        if len(chunks) > 1:
                            logger.info("✅ Discord notification sent: %s (part %d/%d)", category, chunk_idx, len(chunks))
                        else:
                            logger.info("✅ Discord notification sent: %s (%d items)", category, len(items))
                        
                        # Small delay between messages to avoid rate limits
                        time.sleep(0.5)
                    else:
                        logger.error(
                            "Discord webhook failed with status %d: %s (%s part %d/%d)",
                            response.status_code, response.text, category, chunk_idx, len(chunks)
                        )
            
            logger.info("✅ All Discord notifications sent (%d/%d messages)", success_count, total_messages)
            return success_count == total_messages

        except Exception as e:
            logger.error("Failed to send Discord notification: %s", e, exc_info=True)
            return False

    def _create_category_embed(
        self,
        category: str,
        items: List[Dict[str, Any]],
        days_back: int,
        total_count: int,
        part_num: int,
        total_parts: int,
        category_total: int
    ) -> DiscordEmbed:
        """Create Discord embed for a specific category."""
        date_range = f"Last {days_back} day{'s' if days_back != 1 else ''}"
        icon = self.MEDIA_ICONS.get(category, '📁')
        
        # Build title
        if total_parts > 1:
            title = f"{icon} {category} - {date_range} (Part {part_num}/{total_parts})"
        else:
            title = f"{icon} {category} - {date_range}"
        
        # Build description - just show category count to avoid confusion
        if category_total == 1:
            description = f"**{category_total} {category[:-1].lower()} added**"  # Singular
        else:
            description = f"**{category_total} {category.lower()} added**"
        
        embed = DiscordEmbed(
            title=title,
            description=description,
            color=0x57F287  # Green color
        )
        
        # Add all items in this chunk with their dates for range calculation
        self._add_items_to_embed(embed, items, category)
        
        # Add footer with timestamp
        embed.set_footer(text=f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        embed.set_timestamp()
        
        return embed
    
    def _add_items_to_embed(self, embed: DiscordEmbed, items: List[Dict[str, Any]], category: str):
        """Add items to embed, splitting into multiple fields if needed with date ranges."""
        current_chunk = []
        current_chunk_items = []  # Track items for date range
        current_chars = 0
        chunk_num = 1
        
        for item in items:
            item_text = self._format_media_item(item)
            item_length = len(item_text) + 1  # +1 for newline
            
            # Check if adding this item would exceed field limit
            if current_chars + item_length > self.MAX_FIELD_VALUE - 50:
                # Add current chunk as a field
                if current_chunk:
                    field_name = self._get_date_range_field_name(current_chunk_items, chunk_num)
                    field_value = "\n".join(current_chunk)
                    embed.add_embed_field(
                        name=field_name,
                        value=field_value,
                        inline=False
                    )
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
            embed.add_embed_field(
                name=field_name,
                value=field_value,
                inline=False
            )
    
    def _get_date_range_field_name(self, items: List[Dict[str, Any]], chunk_num: int) -> str:
        """Generate field name with date range in DD/MM - DD/MM format."""
        if not items:
            return f"Items ({chunk_num})" if chunk_num > 1 else "Items"
        
        # Items are sorted by date ascending, so first is oldest, last is newest
        first_date = items[0].get('added_at', '')
        last_date = items[-1].get('added_at', '')
        
        # Convert MM/DD to DD/MM format
        try:
            # Parse MM/DD format
            if '/' in first_date and '/' in last_date:
                first_parts = first_date.split('/')
                last_parts = last_date.split('/')
                
                # Convert to DD/MM
                first_formatted = f"{first_parts[1]}/{first_parts[0]}"
                last_formatted = f"{last_parts[1]}/{last_parts[0]}"
                
                if first_formatted == last_formatted:
                    return first_formatted
                else:
                    return f"{first_formatted} - {last_formatted}"
        except (IndexError, ValueError):
            pass
        
        return f"Items ({chunk_num})" if chunk_num > 1 else "Items"

    def _create_embed(
        self, 
        media_items: List[Dict[str, Any]], 
        days_back: int,
        total_count: int,
        page_num: int = 1,
        total_pages: int = 1
    ) -> DiscordEmbed:
        """Create Discord embed from media items."""
        # Group items by type (items already chunked in send_summary)
        grouped = self._group_items_by_type(media_items)
        
        # Create embed with title and description
        date_range = f"Last {days_back} day{'s' if days_back != 1 else ''}"
        
        # Add page indicator to title if multiple pages
        if total_pages > 1:
            title = f"📺 Plex Releases Summary - {date_range} (Page {page_num}/{total_pages})"
        else:
            title = f"📺 Plex Releases Summary - {date_range}"
        
        description = f"**{total_count} new item{'s' if total_count != 1 else ''} added**"
        
        embed = DiscordEmbed(
            title=title,
            description=description,
            color=0x57F287  # Green color
        )

        # Add fields for each media type
        for media_type, items in grouped.items():
            if items:
                self._add_media_field(embed, media_type, items)

        # Add footer with timestamp
        embed.set_footer(text=f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        embed.set_timestamp()

        return embed

    def _group_items_by_type(self, media_items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group media items by type."""
        grouped = {
            'Movies': [],
            'TV Shows': [],
            'TV Seasons': [],
            'TV Episodes': [],
            'Music Albums': [],
            'Music Tracks': []
        }

        for item in media_items:
            media_type = item.get('type', 'unknown')
            
            if media_type == 'movie':
                grouped['Movies'].append(item)
            elif media_type == 'show':
                grouped['TV Shows'].append(item)
            elif media_type == 'season':
                grouped['TV Seasons'].append(item)
            elif media_type == 'episode':
                grouped['TV Episodes'].append(item)
            elif media_type == 'album':
                grouped['Music Albums'].append(item)
            elif media_type == 'track':
                grouped['Music Tracks'].append(item)

        return grouped

    def _add_media_field(
        self, 
        embed: DiscordEmbed, 
        media_type: str, 
        items: List[Dict[str, Any]]
    ):
        """Add field(s) for a specific media type, splitting if needed to fit Discord limits."""
        if not items:
            return

        icon = self.MEDIA_ICONS.get(media_type, '📁')
        total_items = len(items)
        items_to_process = items[:self.MAX_ITEMS_PER_FIELD]
        items_truncated = len(items) > self.MAX_ITEMS_PER_FIELD
        
        # Split items into chunks that fit within Discord's field value limit
        current_chunk = []
        current_chars = 0
        chunk_start_idx = 0
        all_chunks = []
        
        for idx, item in enumerate(items_to_process):
            formatted = self._format_media_item(item)
            item_length = len(formatted) + 1  # +1 for newline
            
            # Check if adding this item would exceed field limit
            if current_chars + item_length > self.MAX_FIELD_VALUE - 50:  # Leave small buffer
                # Save current chunk
                if current_chunk:
                    all_chunks.append((chunk_start_idx, idx, current_chunk[:]))
                    chunk_start_idx = idx
                    current_chunk = []
                    current_chars = 0
            
            current_chunk.append(formatted)
            current_chars += item_length
        
        # Add final chunk
        if current_chunk:
            items_shown = chunk_start_idx + len(current_chunk)
            all_chunks.append((chunk_start_idx, items_shown, current_chunk))
        
        # Create fields for all chunks
        for i, (start_idx, end_idx, chunk) in enumerate(all_chunks):
            is_last_field = (i == len(all_chunks) - 1)
            self._create_field(embed, icon, media_type, total_items, 
                             chunk, start_idx, end_idx, is_last_field, items_truncated)
    
    def _create_field(
        self,
        embed: DiscordEmbed,
        icon: str,
        media_type: str,
        total_items: int,
        formatted_items: List[str],
        start_idx: int,
        end_idx: int,
        is_last_field: bool,
        items_truncated: bool
    ):
        """Create a single Discord embed field."""
        field_value = "\n".join(formatted_items)
        
        # Only show truncation notice on the last field if items were actually truncated
        if is_last_field and items_truncated:
            remaining = total_items - end_idx
            if remaining > 0:
                field_value += f"\n\n*...and {remaining} more*"
        
        # Field name with range if multiple fields or if truncated
        items_shown = end_idx
        if len(formatted_items) < total_items or items_truncated:
            field_name = f"{icon} {media_type} ({start_idx + 1}-{end_idx} of {total_items})"
        else:
            field_name = f"{icon} {media_type} ({total_items})"
        
        embed.add_embed_field(
            name=field_name,
            value=field_value or "*No items*",
            inline=False
        )

    def _format_media_item(self, item: Dict[str, Any]) -> str:
        """Format a single media item for display."""
        title = item.get('title', 'Unknown')
        added_at = item.get('added_at', '')
        rating_key = item.get('rating_key')
        
        # Create clickable link to Plex if URL and server ID are available
        if self.plex_url and self.plex_server_id and rating_key:
            # URL encode the library path
            encoded_key = '%2Flibrary%2Fmetadata%2F' + str(rating_key)
            
            # Check if using Plex.tv or local Plex server
            if 'plex.tv' in self.plex_url.lower():
                # Plex.tv format
                link_url = f"{self.plex_url}/desktop#!/server/{self.plex_server_id}/details?key={encoded_key}"
            else:
                # Local Plex server format
                link_url = f"{self.plex_url}/web/index.html#!/server/{self.plex_server_id}/details?key={encoded_key}"
            
            display_title = f"[{title}]({link_url})"
        else:
            display_title = f"**{title}**"
        
        # Format based on type (year already included in title from app.py)
        return f"• {display_title}"

    def _send_with_retry(self, webhook: DiscordWebhook, max_retries: int = 3) -> Any:
        """
        Send webhook with retry logic for rate limits and transient failures.

        Args:
            webhook: The Discord webhook to send
            max_retries: Maximum number of retry attempts

        Returns:
            Response object from the webhook execution
        """
        for attempt in range(max_retries):
            try:
                response = webhook.execute()
                
                # If rate limited, wait and retry
                if response.status_code == 429:
                    retry_after = response.json().get('retry_after', 1)
                    logger.warning(
                        "Discord rate limit hit, retrying after %ss (attempt %d/%d)",
                        retry_after, attempt + 1, max_retries
                    )
                    time.sleep(retry_after)
                    continue
                
                return response
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        "Discord webhook attempt %d failed: %s. Retrying in %ds...",
                        attempt + 1, e, wait_time
                    )
                    time.sleep(wait_time)
                else:
                    raise
        
        # Should not reach here, but return last response if we do
        return response
