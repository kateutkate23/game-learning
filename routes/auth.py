from fastapi import APIRouter, Depends, HTTPException, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.models import User
from passlib.context import CryptContext

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
def register(
        email: str = Form(...),
        login: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db),
        request: Request = None
):
    if db.query(User).filter(User.login == login).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Логин уже занят"})
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email уже зарегистрирован"})

    hashed_password = pwd_context.hash(password)
    new_user = User(email=email, login=login, password=hashed_password, role="student")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return templates.TemplateResponse("register.html", {"request": request, "success": "Регистрация успешна"})


@router.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
def login(
        login: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db),
        request: Request = None
):
    user = db.query(User).filter(User.login == login).first()
    if not user or not pwd_context.verify(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})

    request.session["user_id"] = user.id
    return templates.TemplateResponse("login.html",
                                      {"request": request, "success": "Вход успешен, user_id: " + str(user.id)})


@router.get("/logout", response_class=RedirectResponse)
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)
