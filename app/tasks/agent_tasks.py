from __future__ import annotations

import asyncio

from app.core.celery_app import celery_app
from app.services.runtime import RunService


@celery_app.task(name="agent_runtime.execute_agent_run")
def execute_agent_run_task(run_id: str) -> None:
    asyncio.run(RunService.execute_queued_run(run_id))
