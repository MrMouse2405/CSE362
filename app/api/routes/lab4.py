from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/lab4",
    tags=["Lab 4 - Templates"],
)

templates = Jinja2Templates(directory="app/templates")


@router.get("/form", response_class=HTMLResponse)
async def form_page_get(request: Request):
    """GET: Show the form page"""
    return templates.TemplateResponse(request=request, name="form.html")