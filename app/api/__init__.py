"""

Top Level API Router

"""

from fastapi import APIRouter
from loguru import logger

from app.api.routes import example, user, westfall, Etest, test

v0_router = APIRouter(prefix="/v0")
v0_router.include_router(example.router)
v0_router.include_router(user.router)
v0_router.include_router(ETest.router)
v0_router.include_router(westfall.router)
v0_router.include_router(test.router)

api_router = APIRouter(prefix="/api")
api_router.include_router(v0_router)
logger.info("Initialized Routes")
