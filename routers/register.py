from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/registerUser", name="register_user", response_class=HTMLResponse)
def show_register_user(request: Request, message: str = "", error: str = ""):
    return templates.TemplateResponse(
        "registerUser.html",
        {"request": request, "message": message, "error": error},
    )