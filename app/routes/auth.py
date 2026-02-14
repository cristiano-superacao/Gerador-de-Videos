from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.user import User


router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciais inválidas"},
            status_code=400,
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": None},
    )


@router.post("/register")
def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    normalized_email = email.lower().strip()

    if db.query(User).filter(User.email == normalized_email).first():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "E-mail já cadastrado"},
            status_code=400,
        )

    is_admin = False
    admin_email = request.app.state.admin_email
    if admin_email and normalized_email == admin_email:
        is_admin = True

    user = User(
        email=normalized_email,
        hashed_password=hash_password(password),
        is_admin=is_admin,
        credits=10 if is_admin else 5,
    )
    db.add(user)
    db.commit()

    return RedirectResponse(url="/login", status_code=302)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)
