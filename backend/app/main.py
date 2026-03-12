"""
Main Application Module.

This module initializes the FastAPI application, sets up standard API routes
like health checks, and configures fallback routing to serve the Svelte SPA
from static files.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel
from starlette.responses import FileResponse

import app.models  # noqa: F401 - ensures all models are registered with SQLModel metadata
from app.database import engine
from app.routes.auth import router as auth_router
from app.services.user_manager import register_superuser


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await register_superuser()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)


@app.get("/api/health")
async def health_check():
    """
    Checks the health status of the API.

    Returns:
        dict: A dictionary indicating the API status and a confirmation message.
    """
    return {"status": "ok", "message": "FastAPI is running"}


# 2. Catch-all for Svelte SPA and static files
static_dir = os.path.join(os.path.dirname(__file__), "static")


@app.get("/{catchall:path}")
async def serve_spa(catchall: str):
    """
    Catch-all route handler for serving static files and the Svelte SPA.

    This function prevents directory traversal attacks and routes unmatched
    requests either to specific static files or to the `index.html` fallback
    for client-side routing.

    Args:
        catchall (str): The requested URL path.

    Returns:
        FileResponse: The requested static file or `index.html`.
    """
    # Prevent directory traversal attacks
    safe_path = os.path.normpath(os.path.join(static_dir, catchall))
    if not safe_path.startswith(static_dir):
        return FileResponse(os.path.join(static_dir, "index.html"))

    if os.path.isfile(safe_path):
        return FileResponse(safe_path)

    # Fallback to Svelte's router
    return FileResponse(os.path.join(static_dir, "index.html"))
