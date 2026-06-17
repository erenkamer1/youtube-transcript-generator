from app.cuda_setup import setup_cuda_libs

setup_cuda_libs()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers import history, models, prompts, transcribe, translate


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcribe.router)
app.include_router(translate.router)
app.include_router(prompts.router)
app.include_router(history.router)
app.include_router(models.router)


@app.get("/api/health")
def health() -> dict:
    from app.services.transcriber import get_cuda_status

    return {
        "status": "ok",
        "app": settings.app_name,
        "build": "2026-06-17-gpu-progress",
        "cuda": get_cuda_status(),
    }
