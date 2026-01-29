from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services import process_form

router = APIRouter(
    prefix="/lab4",
    tags=["Lab 4 - Templates"],
)

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")


@router.get("/form", response_class=HTMLResponse)
async def form_page_get(request: Request):
    """GET: Show the form page"""
    return templates.TemplateResponse(request=request, name="form.html")


@router.post("/form", response_class=HTMLResponse)
async def form_page_post(
    request: Request,
    field1: Annotated[str, Form()] = "",
    field2: Annotated[str, Form()] = "",
):
    """POST: Process submitted form data"""
    data = {"field1": field1, "field2": field2}
    outcome = process_form(data)
    return templates.TemplateResponse(
        request=request, name="results.html", context={"outcome": outcome}
    )
