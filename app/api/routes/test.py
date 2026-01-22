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
    prefix="/test",
    tags=["tests"],
)

@dataclass
class test:
    newNum: float
    
@router.get("/hello")
async def rand():
    newObject = test(newNum = 2.555)
    return newObject




