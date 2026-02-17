"""Unit tests for Discord markdown escaping."""

import pytest

from src.discord_client import _escape_title_markdown


class TestEscapeTitleMarkdown:
    """Tests for _escape_title_markdown function."""

    @pytest.mark.unit
    def test_minimal_does_not_escape_parentheses(self):
        """Test that parentheses remain unchanged."""
        assert _escape_title_markdown("Movie (2025)") == "Movie (2025)"

    @pytest.mark.unit
    def test_minimal_escapes_emphasis(self):
        """Test that emphasis characters are escaped."""
        text = "Title *bold* _italic_ ~strike~ `code`"
        expected = "Title \\*bold\\* \\_italic\\_ \\~strike\\~ \\`code\\`"
        assert _escape_title_markdown(text) == expected

    @pytest.mark.unit
    def test_minimal_escapes_brackets(self):
        """Test that link text brackets are escaped."""
        assert _escape_title_markdown("Movie [Soon]") == "Movie \\[Soon\\]"
