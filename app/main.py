"""

CSE362 Lab Project

"""

import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlmodel import select

from app.api import api_router
from app.auth.password import hash_password
from app.config import DATABASE_URL, ROOT_USER_NAME, ROOT_USER_PASSWORD
from app.models import init_db, make_db_session
from app.models.users import Role, User


def register_root_user():
    """Creates the root user if one does not exist."""
    with make_db_session() as session:
        user: User | None = session.exec(
            select(User).where(User.username == ROOT_USER_NAME)
        ).first()
        if not user:
            root_user = User(
                username=ROOT_USER_NAME,
                password_hash=hash_password(ROOT_USER_PASSWORD),
                role=Role.ROOT,
            )
            session.add(root_user)
            session.commit()
            logger.info("Root user registered")


def create_app(db_url: str = DATABASE_URL, run_startup_events: bool = True) -> FastAPI:
    """Create the FastAPI app instance."""
    app = FastAPI(
        title="CSE362 Lab Project",
        version="0.1.0",
        description="API for the CSE362 lab project.",
    )

    if run_startup_events:
        init_db(db_url=db_url)
        register_root_user()

    """

        Cross Origin Resource Sharing

        Only for development.

    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],  # Allow your frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Define API Routes
    app.include_router(api_router)

    # Mount static files
    static_path = "html"
    if os.path.isdir(static_path):
        app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

    return app


app = create_app()
