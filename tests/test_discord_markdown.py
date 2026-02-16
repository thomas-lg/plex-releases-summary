"""Unit tests for Discord markdown escaping."""

import pytest

from src.discord_client import _escape_markdown


class TestEscapeMarkdown:
    """Tests for _escape_markdown function."""

    @pytest.mark.unit
    def test_escape_asterisks(self):
        """Test escaping asterisks."""
        assert _escape_markdown("*bold*") == "\\*bold\\*"
        assert _escape_markdown("**double**") == "\\*\\*double\\*\\*"

    @pytest.mark.unit
    def test_escape_underscores(self):
        """Test escaping underscores."""
        assert _escape_markdown("_italic_") == "\\_italic\\_"
        assert _escape_markdown("__double__") == "\\_\\_double\\_\\_"

    @pytest.mark.unit
    def test_escape_brackets(self):
        """Test escaping square brackets."""
        assert _escape_markdown("[Title]") == "\\[Title\\]"
        assert _escape_markdown("[Link](url)") == "\\[Link\\]\\(url\\)"

    @pytest.mark.unit
    def test_escape_parentheses(self):
        """Test escaping parentheses."""
        assert _escape_markdown("(Year 2020)") == "\\(Year 2020\\)"

    @pytest.mark.unit
    def test_escape_backticks(self):
        """Test escaping backticks."""
        assert _escape_markdown("`code`") == "\\`code\\`"

    @pytest.mark.unit
    def test_escape_pipes(self):
        """Test escaping pipes."""
        assert _escape_markdown("A | B") == "A \\| B"

    @pytest.mark.unit
    def test_escape_tildes(self):
        """Test escaping tildes."""
        assert _escape_markdown("~~strikethrough~~") == "\\~\\~strikethrough\\~\\~"

    @pytest.mark.unit
    def test_escape_backslashes(self):
        """Test escaping backslashes."""
        assert _escape_markdown("path\\to\\file") == "path\\\\to\\\\file"

    @pytest.mark.unit
    def test_escape_mixed_characters(self):
        """Test escaping multiple markdown characters."""
        text = "Movie: [Title] (2020) - *Action* | _Drama_"
        expected = "Movie: \\[Title\\] \\(2020\\) - \\*Action\\* \\| \\_Drama\\_"
        assert _escape_markdown(text) == expected

    @pytest.mark.unit
    def test_no_escape_needed(self):
        """Test that plain text is unchanged."""
        assert _escape_markdown("Simple Title") == "Simple Title"
        assert _escape_markdown("Movie Title 2020") == "Movie Title 2020"

    @pytest.mark.unit
    def test_empty_string(self):
        """Test escaping empty string."""
        assert _escape_markdown("") == ""

    @pytest.mark.unit
    def test_unicode_characters_preserved(self):
        """Test that unicode characters are preserved."""
        assert _escape_markdown("Movie 🎬") == "Movie 🎬"
        assert _escape_markdown("Café ☕") == "Café ☕"

    @pytest.mark.unit
    def test_real_world_titles(self):
        """Test escaping real-world problematic titles."""
        # Title with brackets
        assert _escape_markdown("Marvel's The Avengers [2012]") == "Marvel's The Avengers \\[2012\\]"
        
        # Title with asterisk
        assert _escape_markdown("Monty Python's Life of Brian *Best Comedy*") == \
            "Monty Python's Life of Brian \\*Best Comedy\\*"
        
        # Title with parentheses
        assert _escape_markdown("The Good (The Bad & The Ugly)") == \
            "The Good \\(The Bad & The Ugly\\)"
