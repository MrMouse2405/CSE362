"""

Top Level API Router

"""

from fastapi import APIRouter
from loguru import logger

from api.routes import example, user

v0_router = APIRouter(prefix="/v0")
v0_router.include_router(example.router)
v0_router.include_router(user.router)

api_router = APIRouter(prefix="/api")
api_router.include_router(v0_router)
logger.info("Initialized Routes")
