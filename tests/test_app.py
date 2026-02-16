"""Unit tests for app module formatting logic."""

import pytest

from src.app import _calculate_batch_params, _format_display_title


class TestCalculateBatchParams:
    """Tests for _calculate_batch_params function."""

    @pytest.mark.unit
    def test_batch_params_7_days(self):
        """Test batch parameters for 7 days or less."""
        initial, increment = _calculate_batch_params(7)
        assert initial == 100
        assert increment == 100

        initial, increment = _calculate_batch_params(3)
        assert initial == 100
        assert increment == 100

    @pytest.mark.unit
    def test_batch_params_30_days(self):
        """Test batch parameters for 8-30 days."""
        initial, increment = _calculate_batch_params(30)
        assert initial == 200
        assert increment == 200

        initial, increment = _calculate_batch_params(15)
        assert initial == 200
        assert increment == 200

    @pytest.mark.unit
    def test_batch_params_over_30_days(self):
        """Test batch parameters for more than 30 days."""
        initial, increment = _calculate_batch_params(31)
        assert initial == 500
        assert increment == 500

        initial, increment = _calculate_batch_params(90)
        assert initial == 500
        assert increment == 500

    @pytest.mark.unit
    def test_batch_params_with_override(self):
        """Test that override parameter takes precedence."""
        initial, increment = _calculate_batch_params(7, override=1000)
        assert initial == 1000
        assert increment == 1000

        initial, increment = _calculate_batch_params(90, override=50)
        assert initial == 50
        assert increment == 50


class TestFormatDisplayTitle:
    """Tests for _format_display_title function."""

    @pytest.mark.unit
    def test_format_episode_with_valid_numbers(self):
        """Test formatting episode with valid season/episode numbers."""
        item = {
            "media_type": "episode",
            "grandparent_title": "Breaking Bad",
            "parent_media_index": "5",
            "media_index": "14",
            "title": "Ozymandias",
        }
        result = _format_display_title(item)
        assert result == "Breaking Bad - S05E14 - Ozymandias"

    @pytest.mark.unit
    def test_format_episode_with_integer_numbers(self):
        """Test formatting episode with integer season/episode numbers."""
        item = {
            "media_type": "episode",
            "grandparent_title": "The Wire",
            "parent_media_index": 1,
            "media_index": 1,
            "title": "The Target",
        }
        result = _format_display_title(item)
        assert result == "The Wire - S01E01 - The Target"

    @pytest.mark.unit
    def test_format_episode_with_missing_numbers(self):
        """Test formatting episode with missing season/episode numbers."""
        item = {
            "media_type": "episode",
            "grandparent_title": "Unknown Show",
            "parent_media_index": "?",
            "media_index": "?",
            "title": "Episode Title",
        }
        result = _format_display_title(item)
        assert result == "Unknown Show - S00E00 - Episode Title"

    @pytest.mark.unit
    def test_format_episode_with_invalid_numbers(self):
        """Test formatting episode with non-numeric season/episode values."""
        item = {
            "media_type": "episode",
            "grandparent_title": "Show Name",
            "parent_media_index": "invalid",
            "media_index": "abc",
            "title": "Episode",
        }
        result = _format_display_title(item)
        assert result == "Show Name - SinvalidEabc - Episode"

    @pytest.mark.unit
    def test_format_episode_missing_fields(self):
        """Test formatting episode with missing fields."""
        item = {
            "media_type": "episode",
            # Missing grandparent_title, parent_media_index, etc.
        }
        result = _format_display_title(item)
        assert "Unknown Show" in result
        assert "Unknown Episode" in result

    @pytest.mark.unit
    def test_format_season(self):
        """Test formatting season."""
        item = {"media_type": "season", "parent_title": "The Sopranos", "media_index": "3"}
        result = _format_display_title(item)
        assert result == "The Sopranos - Season 3"

    @pytest.mark.unit
    def test_format_season_missing_fields(self):
        """Test formatting season with missing fields."""
        item = {"media_type": "season", "media_index": "1"}
        result = _format_display_title(item)
        assert "Unknown Show" in result
        assert "Season 1" in result

    @pytest.mark.unit
    def test_format_show_with_year(self):
        """Test formatting show with year."""
        item = {"media_type": "show", "title": "Stranger Things", "year": "2016"}
        result = _format_display_title(item)
        assert result == "Stranger Things (2016)"

    @pytest.mark.unit
    def test_format_show_without_year(self):
        """Test formatting show without year."""
        item = {"media_type": "show", "title": "New Show"}
        result = _format_display_title(item)
        assert result == "New Show (New Series)"

    @pytest.mark.unit
    def test_format_track(self):
        """Test formatting music track."""
        item = {
            "media_type": "track",
            "grandparent_title": "The Beatles",
            "parent_title": "Abbey Road",
            "title": "Come Together",
        }
        result = _format_display_title(item)
        assert result == "The Beatles - Abbey Road - Come Together"

    @pytest.mark.unit
    def test_format_track_missing_fields(self):
        """Test formatting track with missing fields."""
        item = {"media_type": "track", "title": "Song Name"}
        result = _format_display_title(item)
        assert "Unknown Artist" in result
        assert "Unknown Album" in result
        assert "Song Name" in result

    @pytest.mark.unit
    def test_format_album(self):
        """Test formatting music album."""
        item = {"media_type": "album", "parent_title": "Pink Floyd", "title": "Dark Side of the Moon"}
        result = _format_display_title(item)
        assert result == "Pink Floyd - Dark Side of the Moon"

    @pytest.mark.unit
    def test_format_album_missing_fields(self):
        """Test formatting album with missing fields."""
        item = {"media_type": "album", "title": "Album Name"}
        result = _format_display_title(item)
        assert "Unknown Artist" in result
        assert "Album Name" in result

    @pytest.mark.unit
    def test_format_movie_with_year(self):
        """Test formatting movie with year."""
        item = {"media_type": "movie", "title": "The Shawshank Redemption", "year": "1994"}
        result = _format_display_title(item)
        assert result == "The Shawshank Redemption (1994)"

    @pytest.mark.unit
    def test_format_movie_without_year(self):
        """Test formatting movie without year."""
        item = {"media_type": "movie", "title": "New Movie"}
        result = _format_display_title(item)
        assert result == "New Movie"

    @pytest.mark.unit
    def test_format_movie_missing_fields(self):
        """Test formatting movie with missing fields."""
        item = {"media_type": "movie"}
        result = _format_display_title(item)
        assert result == "Unknown Movie"

    @pytest.mark.unit
    def test_format_unknown_media_type(self):
        """Test formatting unknown media type."""
        item = {"media_type": "unknown_type", "title": "Some Media"}
        result = _format_display_title(item)
        assert result == "Some Media"

    @pytest.mark.unit
    def test_format_no_media_type(self):
        """Test formatting when media_type is missing."""
        item = {"title": "Some Title"}
        result = _format_display_title(item)
        assert result == "Some Title"

    @pytest.mark.unit
    def test_format_no_title_at_all(self):
        """Test formatting when title is completely missing."""
        item = {"media_type": "movie"}
        result = _format_display_title(item)
        assert result == "Unknown Movie"

        item = {"media_type": "unknown"}
        result = _format_display_title(item)
        assert result == "Unknown"
