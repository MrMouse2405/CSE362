"""

Top Level API Router

"""

from fastapi import APIRouter

from api.routes import example

v0_router = APIRouter(prefix="/v0")
v0_router.include_router(example.router)

api_router = APIRouter(prefix="/api")
api_router.include_router(v0_router)
