"""

Top Level API Router

"""

from fastapi import APIRouter

from api.routes import numbers

api_router = APIRouter(prefix="/api")
api_router.include_router(numbers.router)
