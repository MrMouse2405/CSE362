import random
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse
from pydantic.dataclasses import dataclass

from app.auth import (
    allow_admin,
    allow_authorized,
    allow_root,
    allow_student,
    allow_teacher,
)

router = APIRouter(
    prefix="/Westfall",
    tags=["morning practice"],
)


@dataclass
class RandomValue:
    number: int


# Anyone, authonticated or not, Can Call THIS!
@router.get(
    "/rand",
    summary="Get a random number",
    description="Returns a random integer between 0 and 10. No authentication required.",
)
async def rand():
    return RandomValue(number=random.randint(0, 10))



@dataclass
class FormResponse:
    field1: str
    field2: str


@router.post(
    "/form",
    summary="Form route",
    description="Form Example",
)
async def form_route(field1: Annotated[str, Form()], field2: Annotated[str, Form()]):
    return {"result": FormResponse(field1=field1, field2=field2)}
