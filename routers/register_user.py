from fastapi import APIRouter, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from config import JST
from deps import get_db
from services.registration_service import RegistrationService
from mailer import send_mail
import logging

logger = logging.getLogger("myapp")
router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/registerUser", response_class=HTMLResponse)
def show_register_user(request: Request, message: str = "", error: str = ""):
    return templates.TemplateResponse("registerUser.html", {"request": request, "message": message, "error": error})

@router.post("/registerUser")
async def register_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    profile_image: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    svc = RegistrationService(db)

    try:
        await svc.register_temp_user(
            request=request,
            name=name,
            email=email,
            password=password,
            profile_image=profile_image,
        )
    except ValueError as e:
        logger.error(e)
        return templates.TemplateResponse(
            "registerUser.html",
            {"request": request, "error": str(e)},
            status_code=400,
        )
    except Exception as e:
        logger.exception("Unhandled exception in /registerUser")
        return templates.TemplateResponse(
            "registerUser.html",
            {"request": request, "error": "内部エラーが発生しました。"},
            status_code=500,
        )

    return RedirectResponse(url="/registerUserMailSent", status_code=303)

@router.get("/registerUserMailSent", response_class=HTMLResponse)
def show_register_user_mail_sent(request: Request):
    return templates.TemplateResponse("registerUserMailSent.html", {"request": request})

@router.get("/completeUserRegistration/{token}", response_class=HTMLResponse)
async def complete_user_registration(request: Request, token: str, db: Session = Depends(get_db)):
    return templates.TemplateResponse("registerUserMailSent.html", {"request": request})