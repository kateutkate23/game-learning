from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.models import Module, User, Progress
from typing import Optional  # Добавляем для Optional[int]

router = APIRouter(prefix="/modules", tags=["modules"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def get_modules(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if user.role == "teacher":
        modules = db.query(Module).filter(Module.user_id == user_id).all()
        return templates.TemplateResponse("modules_teacher.html", {"request": request, "modules": modules})
    else:
        modules = db.query(Module).all()
        progress = db.query(Progress).filter(Progress.user_id == user_id).all()
        completed_modules = {p.module_id for p in progress if p.completed}
        return templates.TemplateResponse("modules_student.html", {"request": request, "modules": modules,
                                                                   "completed_modules": completed_modules})

@router.get("/create", response_class=HTMLResponse)
def get_create_module(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if user.role != "teacher":
        return RedirectResponse(url="/modules", status_code=302)

    return templates.TemplateResponse("module_create.html", {"request": request})

@router.post("/create", response_class=RedirectResponse)
async def create_module(
        type: str = Form(...),
        title: str = Form(...),
        text: str = Form(None),
        question: str = Form(None),
        options: str = Form(None),
        correct: Optional[int] = Form(None),  # Изменяем на Optional[int]
        points: int = Form(...),
        image: UploadFile = File(None),
        request: Request = None,
        db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if user.role != "teacher":
        return RedirectResponse(url="/modules", status_code=302)

    # Валидация
    if len(title) < 5 or len(title) > 100:
        return templates.TemplateResponse("module_create.html",
                                          {"request": request, "error": "Заголовок должен быть от 5 до 100 символов"})
    if type == "theory" and (not text or len(text) < 50):
        return templates.TemplateResponse("module_create.html",
                                          {"request": request, "error": "Текст должен быть не менее 50 символов"})
    if type == "test" and (not question or not options or correct is None):
        return templates.TemplateResponse("module_create.html", {"request": request,
                                                                 "error": "Заполните вопрос, варианты ответа и правильный ответ"})
    if type == "theory" and (points < 0 or points > 20):
        return templates.TemplateResponse("module_create.html", {"request": request, "error": "Баллы для теории: 0-20"})
    if type == "test" and (points < 0 or points > 50):
        return templates.TemplateResponse("module_create.html", {"request": request, "error": "Баллы для теста: 0-50"})

    # Сохранение изображения
    image_path = None
    if image and image.filename:
        if image.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
            return templates.TemplateResponse("module_create.html", {"request": request,
                                                                     "error": "Формат изображения должен быть PNG, JPEG или JPG"})
        if image.size > 5 * 1024 * 1024:
            return templates.TemplateResponse("module_create.html", {"request": request,
                                                                     "error": "Размер изображения не должен превышать 5 МБ"})
        image_path = f"static/uploads/{image.filename}"
        with open(image_path, "wb") as f:
            f.write(await image.read())

    # Формирование содержимого
    content = {}
    if type == "theory":
        content = {"text": text}
    else:
        options_list = options.split(",")
        content = {"question": question, "options": options_list, "correct": correct}

    new_module = Module(
        title=title,
        type=type,
        content=content,
        image=image_path,
        points=points,
        user_id=user_id
    )
    db.add(new_module)
    db.commit()
    return RedirectResponse(url="/modules", status_code=302)

# Остальные маршруты без изменений
@router.get("/edit/{module_id}", response_class=HTMLResponse)
def get_edit_module(module_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if user.role != "teacher":
        return RedirectResponse(url="/modules", status_code=302)

    module = db.query(Module).filter(Module.id == module_id, Module.user_id == user_id).first()
    if not module:
        return RedirectResponse(url="/modules", status_code=302)

    return templates.TemplateResponse("module_edit.html", {"request": request, "module": module})

@router.post("/edit/{module_id}", response_class=RedirectResponse)
async def edit_module(
        module_id: int,
        title: str = Form(...),
        text: str = Form(None),
        question: str = Form(None),
        options: str = Form(None),
        correct: Optional[int] = Form(None),  # Аналогично для edit
        points: int = Form(...),
        image: UploadFile = File(None),
        request: Request = None,
        db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if user.role != "teacher":
        return RedirectResponse(url="/modules", status_code=302)

    module = db.query(Module).filter(Module.id == module_id, Module.user_id == user_id).first()
    if not module:
        return RedirectResponse(url="/modules", status_code=302)

    # Валидация
    if len(title) < 5 or len(title) > 100:
        return templates.TemplateResponse("module_edit.html", {"request": request, "module": module,
                                                               "error": "Заголовок должен быть от 5 до 100 символов"})
    if module.type == "theory" and (not text or len(text) < 50):
        return templates.TemplateResponse("module_edit.html", {"request": request, "module": module,
                                                               "error": "Текст должен быть не менее 50 символов"})
    if module.type == "test" and (not question or not options or correct is None):
        return templates.TemplateResponse("module_edit.html", {"request": request, "module": module,
                                                               "error": "Заполните вопрос, варианты ответа и правильный ответ"})
    if module.type == "theory" and (points < 0 or points > 20):
        return templates.TemplateResponse("module_edit.html",
                                          {"request": request, "module": module, "error": "Баллы для теории: 0-20"})
    if module.type == "test" and (points < 0 or points > 50):
        return templates.TemplateResponse("module_edit.html",
                                          {"request": request, "module": module, "error": "Баллы для теста: 0-50"})

    # Обновление изображения
    if image and image.filename:
        if image.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
            return templates.TemplateResponse("module_edit.html", {"request": request, "module": module,
                                                                   "error": "Формат изображения должен быть PNG, JPEG или JPG"})
        if image.size > 5 * 1024 * 1024:
            return templates.TemplateResponse("module_edit.html", {"request": request, "module": module,
                                                                   "error": "Размер изображения не должен превышать 5 МБ"})
        if module.image and os.path.exists(module.image):
            os.remove(module.image)
        image_path = f"static/uploads/{image.filename}"
        with open(image_path, "wb") as f:
            f.write(await image.read())
        module.image = image_path

    # Обновление содержимого
    if module.type == "theory":
        module.content = {"text": text}
    else:
        options_list = options.split(",")
        module.content = {"question": question, "options": options_list, "correct": correct}

    module.title = title
    module.points = points
    db.commit()
    return RedirectResponse(url="/modules", status_code=302)

@router.get("/delete/{module_id}", response_class=RedirectResponse)
def delete_module(module_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if user.role != "teacher":
        return RedirectResponse(url="/modules", status_code=302)

    module = db.query(Module).filter(Module.id == module_id, Module.user_id == user_id).first()
    if module:
        if module.image and os.path.exists(module.image):
            os.remove(module.image)
        db.delete(module)
        db.commit()
    return RedirectResponse(url="/modules", status_code=302)

@router.get("/view/{module_id}", response_class=HTMLResponse)
def view_module(module_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if user.role == "teacher":
        return RedirectResponse(url="/modules", status_code=302)

    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        return RedirectResponse(url="/modules", status_code=302)

    progress = db.query(Progress).filter(Progress.user_id == user_id, Progress.module_id == module_id).first()
    completed = progress.completed if progress else False

    return templates.TemplateResponse("module_view.html",
                                      {"request": request, "module": module, "completed": completed})

@router.post("/complete/{module_id}", response_class=RedirectResponse)
def complete_module(
        module_id: int,
        answer: int = Form(None),
        request: Request = None,
        db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if user.role == "teacher":
        return RedirectResponse(url="/modules", status_code=302)

    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        return RedirectResponse(url="/modules", status_code=302)

    progress = db.query(Progress).filter(Progress.user_id == user_id, Progress.module_id == module_id).first()
    if progress and progress.completed:
        return RedirectResponse(url="/modules", status_code=302)

    if module.type == "test":
        if answer is None:
            return templates.TemplateResponse("module_view.html",
                                              {"request": request, "module": module, "error": "Выберите ответ"})
        correct_answer = module.content.get("correct")
        if answer != correct_answer:
            return templates.TemplateResponse("module_view.html", {"request": request, "module": module,
                                                                   "error": "Неправильный ответ. Попробуйте снова"})

    if not progress:
        progress = Progress(user_id=user_id, module_id=module_id, completed=True)
        db.add(progress)
    else:
        progress.completed = True

    user.points += module.points
    db.commit()
    return RedirectResponse(url="/modules?success=Модуль успешно пройден! Баллы начислены: " + str(module.points),
                            status_code=302)