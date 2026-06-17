from fastapi import APIRouter

from app.schemas import OllamaModel
from app.services.ollama_client import list_models

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models", response_model=list[OllamaModel])
async def get_models() -> list[OllamaModel]:
    try:
        models = await list_models()
    except Exception:  # noqa: BLE001
        return []

    return [
        OllamaModel(name=item.get("name", ""), size=item.get("size"))
        for item in models
        if item.get("name")
    ]
