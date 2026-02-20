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
