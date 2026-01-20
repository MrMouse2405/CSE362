"""

CSE362 Lab Project

"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlmodel import select

from api import api_router
from auth.password import hash_password
from config import ROOT_USER_NAME, ROOT_USER_PASSWORD
from models import make_db_session
from models.users import Role, User

"""

    Register Root User

"""


def register_root_user():
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


register_root_user()
logger.info("Root user registered")

"""

FastAPI

"""


app = FastAPI(
    title="CSE362 Lab Project",
    version="0.1.0",
    description="API for the CSE362 lab project.",
)

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

"""

    1. Define API Routes


"""

app.include_router(api_router)

"""

    Mount static files

"""

static_path = "../static"

# Check if directory exists to avoid startup errors
if os.path.isdir(static_path):
    # html=True ensures that:
    # 1. Visiting / serves index.html
    # 2. Visiting /about serves about.html (or about/index.html)
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
else:
    print(f"WARNING: Directory '{static_path}' not found. Did you run 'bun run build'?")
