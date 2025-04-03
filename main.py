from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from database import engine, Base
from routes.auth import router as auth_router
from routes.modules import router as modules_router
from routes.characters import router as characters_router
from routes.profile import router as profile_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key="my-super-secret-key")

app.include_router(auth_router)
app.include_router(modules_router)
app.include_router(characters_router)
app.include_router(profile_router)
Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в систему обучения на основе игр"}


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})
