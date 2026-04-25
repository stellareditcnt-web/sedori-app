from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from routers import research, products, publish, base_auth

load_dotenv()

app = FastAPI(title="せどり自動出品アプリ")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(research.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(publish.router, prefix="/api")
app.include_router(base_auth.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
