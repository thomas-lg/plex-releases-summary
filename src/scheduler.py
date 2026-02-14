import os
import sys
import signal
import logging
from typing import Callable
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("plex-weekly.scheduler")


class GracefulScheduler:
    """Scheduler with graceful shutdown handling for containerized environments."""

    def __init__(self, cron_schedule: str, task_func: Callable):
        """
        Initialize scheduler with CRON schedule and task function.

        Args:
            cron_schedule: CRON expression (e.g., "0 9 * * MON" for Mondays at 9 AM)
            task_func: Function to execute on schedule
        """
        self.cron_schedule = cron_schedule
        self.task_func = task_func
        self.scheduler = BlockingScheduler()
        self._shutdown_requested = False

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame) -> None:
        """Handle shutdown signals gracefully."""
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        logger.info("Received %s, initiating graceful shutdown...", sig_name)
        self._shutdown_requested = True
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _safe_task_wrapper(self) -> None:
        """Wrapper that catches exceptions to prevent scheduler crash."""
        try:
            logger.info("⏰ Scheduled execution triggered")
            result = self.task_func()
            if result != 0:
                logger.warning("Task completed with non-zero exit code: %d", result)
        except Exception as e:
            logger.exception("Error during scheduled task execution: %s", e)
            # Don't propagate - scheduler should continue running

    def start(self) -> None:
        """Start the scheduler and run indefinitely until shutdown signal."""
        try:
            # Parse and validate CRON expression
            trigger = CronTrigger.from_crontab(self.cron_schedule)
            logger.info("Scheduler initialized with CRON schedule: %s", self.cron_schedule)

            # Calculate next run time
            now = datetime.now(trigger.timezone)
            next_run = trigger.get_next_fire_time(None, now)
            logger.info("Next run time: %s", next_run)

            # Add the job to scheduler
            self.scheduler.add_job(
                self._safe_task_wrapper,
                trigger=trigger,
                id="plex_summary_task",
                name="Plex Summary Task",
                coalesce=True,  # Skip missed runs if previous run is still executing
                max_instances=1  # Only one instance at a time
            )

            logger.info("🕐 Scheduler started - waiting for scheduled executions")
            logger.info("Press Ctrl+C or send SIGTERM to stop")

            # Start blocking scheduler
            self.scheduler.start()

        except ValueError as e:
            logger.error("Invalid CRON schedule '%s': %s", self.cron_schedule, e)
            logger.error("CRON format: 'minute hour day month day_of_week'")
            logger.error("Examples: '0 9 * * *' (daily at 9 AM), '0 9 * * MON' (Mondays at 9 AM)")
            sys.exit(1)
        except Exception as e:
            logger.exception("Failed to start scheduler: %s", e)
            sys.exit(1)
        finally:
            if not self._shutdown_requested:
                logger.info("Scheduler stopped unexpectedly")
            else:
                logger.info("✅ Scheduler shutdown complete")


def run_scheduled(task_func: Callable) -> int:
    """
    Run task function on a CRON schedule defined by CRON_SCHEDULE environment variable.

    Args:
        task_func: Function to execute on schedule (should return exit code)

    Returns:
        Exit code (normally doesn't return, runs until shutdown signal)
    """
    cron_schedule = os.environ.get("CRON_SCHEDULE")

    if not cron_schedule:
        logger.error("CRON_SCHEDULE environment variable is required for scheduled mode")
        return 1

    scheduler = GracefulScheduler(cron_schedule, task_func)
    scheduler.start()

    return 0  # Only reached on graceful shutdown
