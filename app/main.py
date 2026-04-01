from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import init_db
from app.runtime.redis_client import close_redis, init_redis
from app.ui.routes import router as ui_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    await init_db()
    await init_redis()
    yield
    await close_redis()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount(
    "/assets",
    StaticFiles(directory=Path(__file__).resolve().parent / "ui" / "dist" / "assets", check_dir=False),
    name="assets",
)
app.mount(
    "/dashboard-assets",
    StaticFiles(directory=Path(__file__).resolve().parent / "ui" / "static"),
    name="dashboard-assets",
)
app.include_router(router, prefix=settings.api_prefix)
app.include_router(ui_router)
