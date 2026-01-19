"""

CSE362 Lab Project

"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import api_router

app = FastAPI()

"""

    Cross Origin Resource Sharing

    Only for development.

"""
# Add this middleware block immediately after creating 'app'
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
