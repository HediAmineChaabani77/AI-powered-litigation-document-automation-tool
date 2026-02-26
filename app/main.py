"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router as api_router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    description="AI-powered litigation document analysis and response generation tool",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Litigation AI Tool API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
