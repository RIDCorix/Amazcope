"""APScheduler configuration for periodic task scheduling."""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


def create_scheduler() -> BlockingScheduler:
    """Create and configure the APScheduler instance.

    Returns:
        BlockingScheduler: Configured scheduler instance
    """
    scheduler = BlockingScheduler(
        timezone="UTC",
        job_defaults={
            "coalesce": True,  # Combine multiple pending executions
            "max_instances": 1,  # Only one instance per job at a time
            "misfire_grace_time": 300,  # 5 minutes grace period for missed jobs
        },
    )

    return scheduler


def setup_periodic_tasks(scheduler: BlockingScheduler) -> None:
    """Setup all periodic tasks with their schedules.

    Args:
        scheduler: The APScheduler instance to add jobs to
    """
    # Import actor functions here to avoid circular imports
    from products.tasks import (
        cleanup_old_snapshots,
        daily_ai_suggestions,
        daily_product_update,
    )

    # Daily product update at 2 AM
    scheduler.add_job(
        func=daily_product_update.send,
        trigger=CronTrigger(hour=2, minute=0, timezone="UTC"),
        id="daily-product-update",
        name="Update all products daily",
        replace_existing=True,
    )

    # Weekly snapshot cleanup at 4 AM on Sundays
    scheduler.add_job(
        func=lambda: cleanup_old_snapshots.send(days=90),
        trigger=CronTrigger(hour=4, minute=0, day_of_week=0, timezone="UTC"),
        id="weekly-snapshot-cleanup",
        name="Cleanup old snapshots weekly",
        replace_existing=True,
    )

    # Daily AI suggestions at 8 AM
    scheduler.add_job(
        func=daily_ai_suggestions.send,
        trigger=CronTrigger(hour=8, minute=0, timezone="UTC"),
        id="daily-ai-suggestions",
        name="Generate AI suggestions daily",
        replace_existing=True,
    )

    logger.info("Periodic tasks configured:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} ({job.id}): {job.trigger}")


def start_scheduler() -> None:
    """Start the scheduler (blocking operation)."""
    scheduler = create_scheduler()
    setup_periodic_tasks(scheduler)

    logger.info("Starting APScheduler...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutdown requested")
        scheduler.shutdown()


if __name__ == "__main__":
    # Allow running scheduler as a standalone process
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    start_scheduler()
