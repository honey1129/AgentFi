from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter()
STATIC_DIR = Path(__file__).resolve().parent / "static"
DIST_DIR = Path(__file__).resolve().parent / "dist"


def _dashboard_entrypoint() -> Path:
    dist_index = DIST_DIR / "index.html"
    if dist_index.exists():
        return dist_index
    return STATIC_DIR / "index.html"


@router.get("/", include_in_schema=False)
async def dashboard() -> FileResponse:
    return FileResponse(_dashboard_entrypoint())


@router.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str) -> FileResponse:
    if full_path.startswith("v1/") or full_path.startswith("assets/") or full_path.startswith("dashboard-assets/"):
        raise HTTPException(status_code=404)
    return FileResponse(_dashboard_entrypoint())
