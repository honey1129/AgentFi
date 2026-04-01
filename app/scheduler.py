from __future__ import annotations

import asyncio

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.config import get_settings
from app.runtime.redis_client import init_redis
from app.services.runtime import ScheduleService


def dispatch_due_schedules_job() -> None:
    asyncio.run(ScheduleService.dispatch_due_schedules())


def main() -> None:
    settings = get_settings()
    asyncio.run(init_redis())

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        dispatch_due_schedules_job,
        "interval",
        seconds=settings.scheduler_tick_seconds,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()


if __name__ == "__main__":
    main()
