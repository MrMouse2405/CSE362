import random
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from pydantic.dataclasses import dataclass

from app.auth import (
    allow_admin,
    allow_authorized,
    allow_root,
    allow_student,
    allow_teacher,
)

router = APIRouter(
    prefix="/example",
    tags=["Examples"],
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


# Only if user is authenticated as root and above
@router.get(
    "/root",
    summary="Root route",
    description="This route is only accessible to users with the 'root' role.",
)
async def root_route(user=Depends(allow_root)):
    return {"message": "Root route"}


# Only if user is authenticated as admin and above
@router.get(
    "/admin",
    summary="Admin route",
    description="This route is accessible to users with 'admin' or 'root' roles.",
)
async def admin_route(user=Depends(allow_admin)):
    return {"message": "Admin route"}


# Only if user is authenticated as teacher and above
@router.get(
    "/teacher",
    summary="Teacher route",
    description="This route is accessible to teachers, admins, and root users.",
)
async def teacher_route(user=Depends(allow_teacher)):
    return {"message": "Teacher route"}


# anyone as long as they are authorized
@router.get(
    "/student",
    summary="Student route",
    description="This route is accessible to students, admins, and root user.",
)
async def student_route(user=Depends(allow_student)):
    return {"message": "Student route"}


@router.get(
    "/authenticated",
    summary="Authenticated route",
    description="This route is accessible to any authenticated users.",
)
async def authenticated_route(user=Depends(allow_authorized)):
    return {"message": "Authenticated route"}


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
