"""Unit tests for scheduler module."""

from datetime import UTC, datetime
from typing import cast

import pytest
from apscheduler.schedulers.blocking import BlockingScheduler

from src.scheduler import GracefulScheduler, run_scheduled


class TestGracefulScheduler:
    """Tests for GracefulScheduler behavior."""

    @pytest.mark.unit
    def test_handle_shutdown_requests_scheduler_stop(self, monkeypatch):
        """Shutdown handler should mark shutdown and stop running scheduler."""

        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_args, **_kwargs: None)

        scheduler = GracefulScheduler("0 9 * * *", lambda: 0)

        class StubBlockingScheduler:
            running = True

            def __init__(self):
                self.shutdown_called = False

            def shutdown(self, wait=False):
                self.shutdown_called = True
                self.wait_arg = wait

        stub = StubBlockingScheduler()
        scheduler.scheduler = cast(BlockingScheduler, stub)

        scheduler._handle_shutdown(15, None)

        assert scheduler._shutdown_requested is True
        assert stub.shutdown_called is True
        assert stub.wait_arg is False

    @pytest.mark.unit
    def test_handle_shutdown_skips_stop_when_scheduler_not_running(self, monkeypatch):
        """Shutdown handler should not call scheduler.shutdown() if it is not running."""

        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_args, **_kwargs: None)

        scheduler = GracefulScheduler("0 9 * * *", lambda: 0)

        class StubBlockingScheduler:
            running = False  # not started yet

            def __init__(self):
                self.shutdown_called = False

            def shutdown(self, wait=False):
                self.shutdown_called = True

        stub = StubBlockingScheduler()
        scheduler.scheduler = cast(BlockingScheduler, stub)

        scheduler._handle_shutdown(15, None)

        assert scheduler._shutdown_requested is True
        assert stub.shutdown_called is False  # should NOT call shutdown

    @pytest.mark.unit
    def test_start_invalid_cron_exits_with_code_1(self, monkeypatch):
        """Invalid cron schedule should cause controlled process exit."""

        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(
            "src.scheduler.CronTrigger.from_crontab", lambda _cron: (_ for _ in ()).throw(ValueError("bad cron"))
        )

        scheduler = GracefulScheduler("invalid cron", lambda: 0)

        with pytest.raises(SystemExit) as exc_info:
            scheduler.start()

        assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_run_scheduled_returns_zero_after_start(self, monkeypatch):
        """run_scheduled should return zero once scheduler.start returns."""

        class StubGracefulScheduler:
            def __init__(self, cron_schedule, task_func):
                self.cron_schedule = cron_schedule
                self.task_func = task_func

            def start(self):
                return None

        monkeypatch.setattr("src.scheduler.GracefulScheduler", StubGracefulScheduler)

        assert run_scheduled(lambda: 0, "0 9 * * *") == 0

    @pytest.mark.unit
    def test_start_adds_job_and_starts_scheduler(self, monkeypatch):
        """Scheduler start should register the job and start the blocking scheduler."""

        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_args, **_kwargs: None)

        class StubTrigger:
            timezone = UTC

            def get_next_fire_time(self, previous, now):
                return datetime(2026, 1, 1, tzinfo=UTC)

        monkeypatch.setattr("src.scheduler.CronTrigger.from_crontab", lambda _cron: StubTrigger())

        scheduler = GracefulScheduler("0 9 * * *", lambda: 0)

        class StubBlockingScheduler:
            def __init__(self):
                self.add_job_called = False
                self.start_called = False

            def add_job(self, func, trigger, id, name, coalesce, max_instances):
                self.add_job_called = True
                self.func = func
                self.trigger = trigger
                self.id = id
                self.name = name
                self.coalesce = coalesce
                self.max_instances = max_instances

            def start(self):
                self.start_called = True

        stub = StubBlockingScheduler()
        scheduler.scheduler = cast(BlockingScheduler, stub)

        scheduler.start()

        assert stub.add_job_called is True
        assert stub.start_called is True
        assert stub.id == "plex_summary_task"
        assert stub.name == "Plex Summary Task"
        assert stub.coalesce is True
        assert stub.max_instances == 1


class TestSafeTaskWrapper:
    """Tests for GracefulScheduler._safe_task_wrapper exception containment."""

    @pytest.mark.unit
    def test_successful_task_runs_without_error(self, monkeypatch):
        """Wrapper should run task and not raise when it completes normally."""
        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_a, **_kw: None)
        scheduler = GracefulScheduler("0 9 * * *", lambda: 0)
        scheduler._safe_task_wrapper()  # must not raise

    @pytest.mark.unit
    def test_non_zero_return_logs_warning(self, monkeypatch, caplog):
        """Non-zero return code from task should be logged as a warning."""
        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_a, **_kw: None)
        scheduler = GracefulScheduler("0 9 * * *", lambda: 2)
        caplog.set_level("WARNING")
        scheduler._safe_task_wrapper()
        assert any("non-zero" in r.message for r in caplog.records)

    @pytest.mark.unit
    def test_connection_error_is_caught_not_reraised(self, monkeypatch, caplog):
        """ConnectionError raised by task should be logged and swallowed."""
        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_a, **_kw: None)

        def failing():
            raise ConnectionError("host unreachable")

        scheduler = GracefulScheduler("0 9 * * *", failing)
        caplog.set_level("ERROR")
        scheduler._safe_task_wrapper()  # must not raise
        assert any("Network error" in r.message for r in caplog.records)

    @pytest.mark.unit
    def test_timeout_error_is_caught_not_reraised(self, monkeypatch, caplog):
        """TimeoutError raised by task should be logged and swallowed."""
        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_a, **_kw: None)

        def failing():
            raise TimeoutError("request timed out")

        scheduler = GracefulScheduler("0 9 * * *", failing)
        caplog.set_level("ERROR")
        scheduler._safe_task_wrapper()  # must not raise
        assert any("Network error" in r.message for r in caplog.records)

    @pytest.mark.unit
    def test_value_error_is_caught_not_reraised(self, monkeypatch, caplog):
        """ValueError raised by task should be logged and swallowed."""
        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_a, **_kw: None)

        def failing():
            raise ValueError("bad config")

        scheduler = GracefulScheduler("0 9 * * *", failing)
        caplog.set_level("ERROR")
        scheduler._safe_task_wrapper()  # must not raise
        assert any("Configuration or data error" in r.message for r in caplog.records)

    @pytest.mark.unit
    def test_generic_exception_is_caught_not_reraised(self, monkeypatch, caplog):
        """Unexpected Exception raised by task should be logged and swallowed."""
        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_a, **_kw: None)

        def failing():
            raise RuntimeError("something unexpected")

        scheduler = GracefulScheduler("0 9 * * *", failing)
        caplog.set_level("ERROR")
        scheduler._safe_task_wrapper()  # must not raise
        assert any("Unexpected error" in r.message for r in caplog.records)


class TestSchedulerStartFinallyBlocks:
    """Tests for GracefulScheduler.start() finally-block log branches."""

    @pytest.mark.unit
    def test_unexpected_exception_exits_with_code_1(self, monkeypatch):
        """Non-ValueError exception during startup should cause sys.exit(1)."""
        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_a, **_kw: None)

        def raise_runtime(cron):
            raise RuntimeError("unexpected scheduler failure")

        monkeypatch.setattr("src.scheduler.CronTrigger.from_crontab", raise_runtime)
        scheduler = GracefulScheduler("0 9 * * *", lambda: 0)

        with pytest.raises(SystemExit) as exc_info:
            scheduler.start()

        assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_finally_warns_when_stopped_unexpectedly(self, monkeypatch, caplog):
        """Scheduler stopping without a shutdown signal should log a warning."""
        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_a, **_kw: None)

        class StubTrigger:
            timezone = UTC

            def get_next_fire_time(self, prev, now):
                return datetime(2026, 1, 1, tzinfo=UTC)

        monkeypatch.setattr("src.scheduler.CronTrigger.from_crontab", lambda _: StubTrigger())

        scheduler = GracefulScheduler("0 9 * * *", lambda: 0)
        # _shutdown_requested remains False (default)

        class StubBlockingScheduler:
            def add_job(self, *a, **kw):
                pass

            def start(self):
                pass  # returns normally -> scheduler stopped without a signal

        scheduler.scheduler = cast(BlockingScheduler, StubBlockingScheduler())
        caplog.set_level("WARNING")
        scheduler.start()

        assert any("stopped unexpectedly" in r.message for r in caplog.records)

    @pytest.mark.unit
    def test_finally_info_on_graceful_shutdown(self, monkeypatch, caplog):
        """Scheduler stopping after a shutdown signal should log a completion info line."""
        monkeypatch.setattr("src.scheduler.signal.signal", lambda *_a, **_kw: None)

        class StubTrigger:
            timezone = UTC

            def get_next_fire_time(self, prev, now):
                return datetime(2026, 1, 1, tzinfo=UTC)

        monkeypatch.setattr("src.scheduler.CronTrigger.from_crontab", lambda _: StubTrigger())

        scheduler = GracefulScheduler("0 9 * * *", lambda: 0)
        scheduler._shutdown_requested = True  # pre-set as if signal was received

        class StubBlockingScheduler:
            def add_job(self, *a, **kw):
                pass

            def start(self):
                pass

        scheduler.scheduler = cast(BlockingScheduler, StubBlockingScheduler())
        caplog.set_level("INFO")
        scheduler.start()

        assert any("shutdown complete" in r.message for r in caplog.records)
