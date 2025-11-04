from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from deps import get_db
from services.login_service import LoginService
from utils.flash import set_flash, pop_flash
import logging

logger = logging.getLogger("myapp." + __name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = LoginService(db).login(email=email, password=password)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "メールアドレスまたはパスワードが違います"}
        )

    request.session["user_id"] = user.id
    request.session["user_email"] = user.email

    set_flash(request, "ログインしました。")

    return RedirectResponse(url="/top", status_code=303)


@router.get("/top", response_class=HTMLResponse)
async def top_page(request: Request):
    message = pop_flash(request)
    user_email = request.session.get("user_email")

    ctx = {
        "request": request,
        "user_email": user_email,
        "message": message,
    }
    return templates.TemplateResponse("top.html", ctx)