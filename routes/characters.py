from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.models import Character, User

router = APIRouter(prefix="/character", tags=["characters"])
templates = Jinja2Templates(directory="templates")


@router.get("/edit", response_class=HTMLResponse)
def get_edit_character(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    character = db.query(Character).filter(Character.user_id == user_id).first()
    return templates.TemplateResponse("character_edit.html", {"request": request, "character": character})


@router.post("/edit", response_class=RedirectResponse)
def edit_character(
        name: str = Form(...),
        hair: str = Form(...),
        face: str = Form(...),
        costume: str = Form(...),
        shoes: str = Form(...),
        request: Request = None,
        db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    character = db.query(Character).filter(Character.user_id == user_id).first()
    if not character:
        character = Character(
            name=name,
            hair=hair,
            face=face,
            costume=costume,
            shoes=shoes,
            user_id=user_id
        )
        db.add(character)
    else:
        character.name = name
        character.hair = hair
        character.face = face
        character.costume = costume
        character.shoes = shoes
    db.commit()
    return RedirectResponse(url="/profile", status_code=302)


@router.get("/skills", response_class=HTMLResponse)
def get_skills(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    character = db.query(Character).filter(Character.user_id == user_id).first()
    if not character:
        return RedirectResponse(url="/character/edit", status_code=302)

    return templates.TemplateResponse("character_skills.html",
                                      {"request": request, "user": user, "character": character})


@router.post("/skills", response_class=RedirectResponse)
def update_skills(
        strength: int = Form(...),
        intelligence: int = Form(...),
        agility: int = Form(...),
        request: Request = None,
        db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    character = db.query(Character).filter(Character.user_id == user_id).first()
    if not character:
        return RedirectResponse(url="/character/edit", status_code=302)

    current_skills = character.skills
    new_skills = {"strength": strength, "intelligence": intelligence, "agility": agility}

    # Подсчитываем стоимость изменений
    total_cost = 0
    for skill, new_value in new_skills.items():
        current_value = current_skills.get(skill, 1)
        if new_value > current_value:
            total_cost += (new_value - current_value) * 10  # 10 баллов за уровень

    if total_cost > user.points:
        return templates.TemplateResponse("character_skills.html", {
            "request": request,
            "user": user,
            "character": character,
            "error": "Недостаточно баллов для повышения навыков"
        })

    # Обновляем навыки и баллы
    user.points -= total_cost
    character.skills = new_skills
    db.commit()
    return RedirectResponse(url="/profile", status_code=302)
