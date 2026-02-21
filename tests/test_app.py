"""Unit tests for app module formatting logic."""

import importlib.metadata
from datetime import UTC, datetime

import pytest
import requests

from src.app import _calculate_batch_params, _format_display_title, main, run_summary
from src.config import Config
from src.tautulli_client import TautulliMediaItem


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
        item: TautulliMediaItem = {
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
        item: TautulliMediaItem = {
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
        item: TautulliMediaItem = {
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
        item: TautulliMediaItem = {
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
        item: TautulliMediaItem = {
            "media_type": "episode",
            # Missing grandparent_title, parent_media_index, etc.
        }
        result = _format_display_title(item)
        assert "Unknown Show" in result
        assert "Unknown Episode" in result

    @pytest.mark.unit
    def test_format_season(self):
        """Test formatting season."""
        item: TautulliMediaItem = {"media_type": "season", "parent_title": "The Sopranos", "media_index": "3"}
        result = _format_display_title(item)
        assert result == "The Sopranos - Season 3"

    @pytest.mark.unit
    def test_format_season_missing_fields(self):
        """Test formatting season with missing fields."""
        item: TautulliMediaItem = {"media_type": "season", "media_index": "1"}
        result = _format_display_title(item)
        assert "Unknown Show" in result
        assert "Season 1" in result

    @pytest.mark.unit
    def test_format_show_with_year(self):
        """Test formatting show with year."""
        item: TautulliMediaItem = {"media_type": "show", "title": "Stranger Things", "year": "2016"}
        result = _format_display_title(item)
        assert result == "Stranger Things (2016)"

    @pytest.mark.unit
    def test_format_show_without_year(self):
        """Test formatting show without year."""
        item: TautulliMediaItem = {"media_type": "show", "title": "New Show"}
        result = _format_display_title(item)
        assert result == "New Show (New Series)"

    @pytest.mark.unit
    def test_format_track(self):
        """Test formatting music track."""
        item: TautulliMediaItem = {
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
        item: TautulliMediaItem = {"media_type": "track", "title": "Song Name"}
        result = _format_display_title(item)
        assert "Unknown Artist" in result
        assert "Unknown Album" in result
        assert "Song Name" in result

    @pytest.mark.unit
    def test_format_album(self):
        """Test formatting music album."""
        item: TautulliMediaItem = {
            "media_type": "album",
            "parent_title": "Pink Floyd",
            "title": "Dark Side of the Moon",
        }
        result = _format_display_title(item)
        assert result == "Pink Floyd - Dark Side of the Moon"

    @pytest.mark.unit
    def test_format_album_missing_fields(self):
        """Test formatting album with missing fields."""
        item: TautulliMediaItem = {"media_type": "album", "title": "Album Name"}
        result = _format_display_title(item)
        assert "Unknown Artist" in result
        assert "Album Name" in result

    @pytest.mark.unit
    def test_format_movie_with_year(self):
        """Test formatting movie with year."""
        item: TautulliMediaItem = {"media_type": "movie", "title": "The Shawshank Redemption", "year": "1994"}
        result = _format_display_title(item)
        assert result == "The Shawshank Redemption (1994)"

    @pytest.mark.unit
    def test_format_movie_without_year(self):
        """Test formatting movie without year."""
        item: TautulliMediaItem = {"media_type": "movie", "title": "New Movie"}
        result = _format_display_title(item)
        assert result == "New Movie"

    @pytest.mark.unit
    def test_format_movie_missing_fields(self):
        """Test formatting movie with missing fields."""
        item: TautulliMediaItem = {"media_type": "movie"}
        result = _format_display_title(item)
        assert result == "Unknown Movie"

    @pytest.mark.unit
    def test_format_unknown_media_type(self):
        """Test formatting unknown media type."""
        item: TautulliMediaItem = {"media_type": "unknown_type", "title": "Some Media"}
        result = _format_display_title(item)
        assert result == "Some Media"

    @pytest.mark.unit
    def test_format_no_media_type(self):
        """Test formatting when media_type is missing."""
        item: TautulliMediaItem = {"title": "Some Title"}
        result = _format_display_title(item)
        assert result == "Some Title"

    @pytest.mark.unit
    def test_format_no_title_at_all(self):
        """Test formatting when title is completely missing."""
        item: TautulliMediaItem = {"media_type": "movie"}
        result = _format_display_title(item)
        assert result == "Unknown Movie"

        item: TautulliMediaItem = {"media_type": "unknown"}
        result = _format_display_title(item)
        assert result == "Unknown"


class TestRunSummary:
    """Tests for run_summary behavior and operational guarantees."""

    @pytest.mark.unit
    def test_run_summary_fails_in_run_once_when_discord_send_fails(self, monkeypatch):
        """Discord delivery errors should produce non-zero exit code in one-shot mode."""

        class StubTautulliClient:
            def get_recently_added(self, days, count):
                timestamp = int(datetime.now(UTC).timestamp())
                return {"recently_added": [{"media_type": "movie", "title": "Movie", "added_at": timestamp}]}

            def get_server_identity(self):
                return {"machine_identifier": "server-id"}

        class StubDiscordNotifier:
            def __init__(self, webhook_url, plex_url, plex_server_id):
                self.webhook_url = webhook_url
                self.plex_url = plex_url
                self.plex_server_id = plex_server_id

            def send_summary(self, media_items, days_back, total_count):
                raise requests.RequestException("network timeout")

        monkeypatch.setattr("src.app.TautulliClient", lambda *args, **kwargs: StubTautulliClient())
        monkeypatch.setattr("src.app.DiscordNotifier", StubDiscordNotifier)

        config = Config.model_validate(
            {
                "tautulli_url": "http://tautulli:8181",
                "tautulli_api_key": "secret",
                "run_once": True,
                "discord_webhook_url": "https://discord.example/webhook",
            }
        )

        assert run_summary(config) == 1

    @pytest.mark.unit
    def test_run_summary_keeps_scheduled_mode_non_fatal_on_discord_error(self, monkeypatch):
        """Discord errors should not fail scheduled executions."""

        class StubTautulliClient:
            def get_recently_added(self, days, count):
                timestamp = int(datetime.now(UTC).timestamp())
                return {"recently_added": [{"media_type": "movie", "title": "Movie", "added_at": timestamp}]}

            def get_server_identity(self):
                return {"machine_identifier": "server-id"}

        class StubDiscordNotifier:
            def __init__(self, webhook_url, plex_url, plex_server_id):
                self.webhook_url = webhook_url
                self.plex_url = plex_url
                self.plex_server_id = plex_server_id

            def send_summary(self, media_items, days_back, total_count):
                raise requests.RequestException("network timeout")

        monkeypatch.setattr("src.app.TautulliClient", lambda *args, **kwargs: StubTautulliClient())
        monkeypatch.setattr("src.app.DiscordNotifier", StubDiscordNotifier)

        config = Config.model_validate(
            {
                "tautulli_url": "http://tautulli:8181",
                "tautulli_api_key": "secret",
                "run_once": False,
                "discord_webhook_url": "https://discord.example/webhook",
            }
        )

        assert run_summary(config) == 0

    @pytest.mark.unit
    def test_run_summary_limits_info_output_per_media_type(self, monkeypatch, caplog):
        """INFO logging should show at most 10 entries per media type."""

        class StubTautulliClient:
            def get_recently_added(self, days, count):
                timestamp = int(datetime.now(UTC).timestamp())
                movies = [{"media_type": "movie", "title": f"Movie {i}", "added_at": timestamp} for i in range(1, 13)]
                shows = [{"media_type": "show", "title": f"Show {i}", "added_at": timestamp} for i in range(1, 12)]
                return {"recently_added": movies + shows}

        monkeypatch.setattr("src.app.TautulliClient", lambda *args, **kwargs: StubTautulliClient())

        config = Config.model_validate(
            {
                "tautulli_url": "http://tautulli:8181",
                "tautulli_api_key": "secret",
                "run_once": True,
                "discord_webhook_url": None,
            }
        )

        caplog.set_level("INFO")
        assert run_summary(config) == 0

        added_lines = [record.message for record in caplog.records if record.message.startswith("➕")]
        assert len(added_lines) == 20
        assert any("movie: 2" in record.message and "show: 1" in record.message for record in caplog.records)

    @pytest.mark.unit
    def test_run_summary_stops_when_api_returns_fewer_items_than_requested(self, monkeypatch):
        """Fetching should stop when the API returns fewer items than requested (hit its limit)."""
        call_counts = {"n": 0}

        class StubTautulliClient:
            def get_recently_added(self, days, count):
                call_counts["n"] += 1
                timestamp = int(datetime.now(UTC).timestamp())
                # Always return 5 items regardless of how many were requested
                return {
                    "recently_added": [
                        {"media_type": "movie", "title": f"Movie {i}", "added_at": timestamp} for i in range(5)
                    ]
                }

        monkeypatch.setattr("src.app.TautulliClient", lambda *args, **kwargs: StubTautulliClient())

        config = Config.model_validate(
            {
                "tautulli_url": "http://tautulli:8181",
                "tautulli_api_key": "secret",
                "run_once": True,
                "discord_webhook_url": None,
                "initial_batch_size": 100,  # request 100, get 5 → stop after first batch
            }
        )

        assert run_summary(config) == 0
        assert call_counts["n"] == 1  # exactly one API call

    @pytest.mark.unit
    def test_run_summary_expands_batch_when_oldest_item_still_in_range(self, monkeypatch):
        """Fetching should expand the batch size when the oldest returned item is still within the date range."""
        call_counts = {"n": 0}
        timestamps = {
            # First batch: all items are recent (within range), oldest still in range → expand
            1: int(datetime.now(UTC).timestamp()),
            # Second batch: oldest item is old (outside range) → stop
            2: 0,
        }

        class StubTautulliClient:
            def get_recently_added(self, days, count):
                call_counts["n"] += 1
                oldest_ts = timestamps.get(call_counts["n"], 0)
                items = [
                    {"media_type": "movie", "title": f"Movie {i}", "added_at": int(datetime.now(UTC).timestamp())}
                    for i in range(count - 1)
                ]
                # Last item has the controlled timestamp
                items.append({"media_type": "movie", "title": "Oldest", "added_at": oldest_ts})
                return {"recently_added": items}

        monkeypatch.setattr("src.app.TautulliClient", lambda *args, **kwargs: StubTautulliClient())
        monkeypatch.setattr("src.app.time.sleep", lambda _: None)

        config = Config.model_validate(
            {
                "tautulli_url": "http://tautulli:8181",
                "tautulli_api_key": "secret",
                "run_once": True,
                "discord_webhook_url": None,
                "initial_batch_size": 5,
            }
        )

        assert run_summary(config) == 0
        assert call_counts["n"] == 2  # expanded once, then stopped

    @pytest.mark.unit
    def test_run_summary_stops_at_max_iterations(self, monkeypatch, caplog):
        """Fetching should stop and warn when the max iteration guardrail (50) is reached."""

        class StubTautulliClient:
            def get_recently_added(self, days, count):
                # Always return exactly `count` items, all recent → always triggers another iteration
                timestamp = int(datetime.now(UTC).timestamp())
                return {
                    "recently_added": [
                        {"media_type": "movie", "title": f"Movie {i}", "added_at": timestamp} for i in range(count)
                    ]
                }

        monkeypatch.setattr("src.app.TautulliClient", lambda *args, **kwargs: StubTautulliClient())
        monkeypatch.setattr("src.app.time.sleep", lambda _: None)

        config = Config.model_validate(
            {
                "tautulli_url": "http://tautulli:8181",
                "tautulli_api_key": "secret",
                "run_once": True,
                "discord_webhook_url": None,
                "initial_batch_size": 1,
            }
        )

        caplog.set_level("WARNING")
        assert run_summary(config) == 0
        assert any("max fetch iterations" in r.message.lower() for r in caplog.records)

    @pytest.mark.unit
    def test_run_summary_stops_when_max_fetch_count_reached(self, monkeypatch):
        """Iterative fetching should stop once the max fetch count guardrail is reached."""

        class StubTautulliClient:
            def get_recently_added(self, days, count):
                timestamp = int(datetime.now(UTC).timestamp())
                return {
                    "recently_added": [
                        {"media_type": "movie", "title": f"Movie {i}", "added_at": timestamp} for i in range(count)
                    ]
                }

        monkeypatch.setattr("src.app.TautulliClient", lambda *args, **kwargs: StubTautulliClient())
        monkeypatch.setattr("src.app.time.sleep", lambda _seconds: None)

        config = Config.model_validate(
            {
                "tautulli_url": "http://tautulli:8181",
                "tautulli_api_key": "secret",
                "run_once": True,
                "discord_webhook_url": None,
                "initial_batch_size": 9990,
            }
        )

        assert run_summary(config) == 0


class TestMain:
    """Tests for main() startup behavior: banner and version resolution."""

    @staticmethod
    def _stub_config():
        return Config.model_validate(
            {
                "tautulli_url": "http://tautulli:8181",
                "tautulli_api_key": "secret",
                "run_once": True,
                "discord_webhook_url": None,
            }
        )

    @pytest.mark.unit
    def test_main_prints_banner_and_logs_version(self, monkeypatch, caplog, capsys):
        """main() prints the ASCII banner to stdout and logs the version."""
        monkeypatch.setattr("src.app._get_config_path", lambda: "/config.yml")
        monkeypatch.setattr("src.app.setup_logging", lambda *a, **kw: None)
        monkeypatch.setattr("src.app.get_bootstrap_log_level", lambda _: "INFO")
        monkeypatch.setattr("importlib.metadata.version", lambda _pkg: "1.2.3")
        monkeypatch.setattr("src.app.load_config", lambda _: TestMain._stub_config())
        monkeypatch.setattr("src.app.run_summary", lambda _: 0)

        caplog.set_level("INFO", logger="app")
        main()

        stdout = capsys.readouterr().out
        assert "PRS" in stdout or "Plex Releases Summary" in stdout, "Expected banner in stdout"
        assert "v1.2.3" in stdout

        log_records = [r.message for r in caplog.records if "Plex Releases Summary" in r.message]
        assert log_records, "Expected version log line"
        assert "v1.2.3" in log_records[0]

    @pytest.mark.unit
    def test_main_falls_back_to_unknown_version_when_package_not_installed(self, monkeypatch, caplog, capsys):
        """main() falls back to 'unknown' in both banner and log when package is not installed."""
        monkeypatch.setattr("src.app._get_config_path", lambda: "/config.yml")
        monkeypatch.setattr("src.app.setup_logging", lambda *a, **kw: None)
        monkeypatch.setattr("src.app.get_bootstrap_log_level", lambda _: "INFO")

        def _raise_not_found(_pkg):
            raise importlib.metadata.PackageNotFoundError("plex-releases-summary")

        monkeypatch.setattr("importlib.metadata.version", _raise_not_found)
        monkeypatch.setattr("src.app.load_config", lambda _: TestMain._stub_config())
        monkeypatch.setattr("src.app.run_summary", lambda _: 0)

        caplog.set_level("INFO", logger="app")
        main()

        stdout = capsys.readouterr().out
        assert "unknown" in stdout, "Expected 'unknown' version in printed banner"

        log_records = [r.message for r in caplog.records if "Plex Releases Summary" in r.message]
        assert log_records, "Expected version log line"
        assert "vunknown" in log_records[0]
