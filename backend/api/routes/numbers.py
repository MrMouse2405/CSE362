import random

from fastapi import APIRouter

router = APIRouter(prefix="/numbers", tags=["numbers"])


@router.get("/rand")
def rand():
    return {"number": random.randint(0, 10)}
