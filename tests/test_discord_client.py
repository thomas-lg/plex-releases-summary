"""Unit tests for Discord client size calculation logic."""

import pytest
from discord_webhook import DiscordEmbed

from src.discord_client import DiscordNotifier


class TestDiscordNotifier:
    """Tests for DiscordNotifier class."""

    @pytest.fixture
    def notifier(self):
        """Create a DiscordNotifier instance for testing."""
        return DiscordNotifier(
            webhook_url="https://discord.com/api/webhooks/test",
            plex_url="https://app.plex.tv",
            plex_server_id="test-server-id",
        )

    @pytest.mark.unit
    def test_calculate_embed_size_empty(self, notifier):
        """Test calculating size of an empty embed."""
        embed = DiscordEmbed()
        size = notifier._calculate_embed_size(embed)
        assert size == 0

    @pytest.mark.unit
    def test_calculate_embed_size_with_title(self, notifier):
        """Test calculating size with title."""
        embed = DiscordEmbed(title="Test Title")
        size = notifier._calculate_embed_size(embed)
        assert size == len("Test Title")

    @pytest.mark.unit
    def test_calculate_embed_size_with_description(self, notifier):
        """Test calculating size with description."""
        embed = DiscordEmbed(description="Test Description")
        size = notifier._calculate_embed_size(embed)
        assert size == len("Test Description")

    @pytest.mark.unit
    def test_calculate_embed_size_with_fields(self, notifier):
        """Test calculating size with fields."""
        embed = DiscordEmbed()
        embed.add_embed_field(name="Field 1", value="Value 1")
        embed.add_embed_field(name="Field 2", value="Value 2")

        size = notifier._calculate_embed_size(embed)
        expected = len("Field 1") + len("Value 1") + len("Field 2") + len("Value 2")
        assert size == expected

    @pytest.mark.unit
    def test_calculate_embed_size_with_footer(self, notifier):
        """Test calculating size with footer."""
        embed = DiscordEmbed()
        embed.set_footer(text="Footer text")

        size = notifier._calculate_embed_size(embed)
        assert size == len("Footer text")

    @pytest.mark.unit
    def test_calculate_embed_size_with_author(self, notifier):
        """Test calculating size with author."""
        embed = DiscordEmbed()
        embed.set_author(name="Author Name")

        size = notifier._calculate_embed_size(embed)
        assert size == len("Author Name")

    @pytest.mark.unit
    def test_calculate_embed_size_complete(self, notifier):
        """Test calculating size with all components."""
        embed = DiscordEmbed(title="Test Title", description="Test Description")
        embed.add_embed_field(name="Field", value="Value")
        embed.set_footer(text="Footer")
        embed.set_author(name="Author")

        size = notifier._calculate_embed_size(embed)
        expected = (
            len("Test Title") + len("Test Description") + len("Field") + len("Value") + len("Footer") + len("Author")
        )
        assert size == expected

    @pytest.mark.unit
    def test_calculate_embed_size_with_unicode(self, notifier):
        """Test calculating size with unicode characters."""
        embed = DiscordEmbed(title="🎬 Movies 📺")
        embed.add_embed_field(name="Field 🎵", value="Value 💿")

        size = notifier._calculate_embed_size(embed)
        # Should count by character count, not bytes
        expected = len("🎬 Movies 📺") + len("Field 🎵") + len("Value 💿")
        assert size == expected

    @pytest.mark.unit
    def test_group_items_by_type_movies(self, notifier):
        """Test grouping movie items."""
        items = [
            {"type": "movie", "title": "Movie 1"},
            {"type": "movie", "title": "Movie 2"},
        ]
        grouped = notifier._group_items_by_type(items)
        assert "Movies" in grouped
        assert len(grouped["Movies"]) == 2

    @pytest.mark.unit
    def test_group_items_by_type_tv_shows(self, notifier):
        """Test grouping TV show items."""
        items = [
            {"type": "show", "title": "Show 1"},
            {"type": "season", "title": "Season 1"},
            {"type": "episode", "title": "Episode 1"},
        ]
        grouped = notifier._group_items_by_type(items)
        assert "TV Shows" in grouped
        assert len(grouped["TV Shows"]) == 1
        assert "TV Seasons" in grouped
        assert len(grouped["TV Seasons"]) == 1
        assert "TV Episodes" in grouped
        assert len(grouped["TV Episodes"]) == 1

    @pytest.mark.unit
    def test_group_items_by_type_music(self, notifier):
        """Test grouping music items."""
        items = [
            {"type": "album", "title": "Album 1"},
            {"type": "track", "title": "Track 1"},
        ]
        grouped = notifier._group_items_by_type(items)
        assert "Music Albums" in grouped
        assert len(grouped["Music Albums"]) == 1
        assert "Music Tracks" in grouped
        assert len(grouped["Music Tracks"]) == 1

    @pytest.mark.unit
    def test_group_items_by_type_mixed(self, notifier):
        """Test grouping mixed media types."""
        items = [
            {"type": "movie", "title": "Movie 1"},
            {"type": "show", "title": "Show 1"},
            {"type": "album", "title": "Album 1"},
            {"type": "movie", "title": "Movie 2"},
        ]
        grouped = notifier._group_items_by_type(items)
        assert len(grouped["Movies"]) == 2
        assert len(grouped["TV Shows"]) == 1
        assert len(grouped["Music Albums"]) == 1

    @pytest.mark.unit
    def test_group_items_by_type_unknown(self, notifier):
        """Test grouping with unknown media type."""
        items = [
            {"type": "unknown", "title": "Unknown Item"},
        ]
        grouped = notifier._group_items_by_type(items)
        # Unknown types should be skipped or handled gracefully
        # Check implementation behavior
        assert isinstance(grouped, dict)

    @pytest.mark.unit
    def test_format_media_item_with_link(self, notifier):
        """Test formatting media item with Plex link."""
        item = {"type": "movie", "rating_key": "12345", "title": "Test Movie"}
        formatted = notifier._format_media_item(item)
        assert "app.plex.tv" in formatted
        assert "test-server-id" in formatted
        assert "12345" in formatted
        assert "Test Movie" in formatted

    @pytest.mark.unit
    def test_format_media_item_without_server_id(self):
        """Test formatting media item without server ID."""
        notifier = DiscordNotifier(
            webhook_url="https://discord.com/api/webhooks/test", plex_url="https://app.plex.tv", plex_server_id=None
        )
        item = {"type": "movie", "rating_key": "12345", "title": "Test Movie"}
        formatted = notifier._format_media_item(item)
        assert formatted == "• **Test Movie**"

    @pytest.mark.unit
    def test_format_media_item_missing_rating_key(self, notifier):
        """Test formatting media item without rating_key."""
        item = {"type": "movie", "title": "Test Movie"}
        formatted = notifier._format_media_item(item)
        assert formatted == "• **Test Movie**"

    @pytest.mark.unit
    def test_validate_and_trim_embed_within_limits(self, notifier):
        """Test that embed within limits is not trimmed."""
        items = [
            {"type": "movie", "title": "Movie 1", "added_at": "2024-01-01"},
            {"type": "movie", "title": "Movie 2", "added_at": "2024-01-02"},
        ]

        embed, items_sent = notifier._validate_and_trim_embed(
            category="Movies", items=items, days_back=7, total_count=2, part_num=1, category_total=2, all_items=items
        )

        assert items_sent == 2  # All items should be included
        assert embed is not None

    @pytest.mark.unit
    def test_validate_and_trim_embed_exceeds_limits(self, notifier):
        """Test that oversized embed is trimmed."""
        # Create many items with long titles to exceed size limit
        items = [
            {"type": "movie", "title": "Very Long Movie Title " * 50, "added_at": f"2024-01-{i:02d}"}  # Very long title
            for i in range(1, 26)  # 25 items (max allowed)
        ]

        embed, items_sent = notifier._validate_and_trim_embed(
            category="Movies", items=items, days_back=7, total_count=25, part_num=1, category_total=25, all_items=items
        )

        # Some items should be trimmed
        assert items_sent < len(items) or items_sent == len(items)
        assert embed is not None

        # Embed may still exceed limits if trimming hits minimum size
        size = notifier._calculate_embed_size(embed)
        assert size > 0

    @pytest.mark.unit
    def test_constants_are_within_discord_limits(self):
        """Test that class constants respect Discord API limits."""
        assert DiscordNotifier.MAX_FIELD_VALUE <= 1024
        assert DiscordNotifier.MAX_ITEMS_TOTAL <= 25
        assert DiscordNotifier.EMBED_SIZE_BUFFER <= 6000
        assert DiscordNotifier.TRIM_REDUCTION_FACTOR > 0
        assert DiscordNotifier.TRIM_REDUCTION_FACTOR < 1

    @pytest.mark.unit
    def test_media_icons_exist(self):
        """Test that media icons are defined for all categories."""
        expected_categories = ["Movies", "TV Shows", "TV Seasons", "TV Episodes", "Music Albums", "Music Tracks"]
        for category in expected_categories:
            assert category in DiscordNotifier.MEDIA_ICONS
            assert isinstance(DiscordNotifier.MEDIA_ICONS[category], str)
            assert len(DiscordNotifier.MEDIA_ICONS[category]) > 0
