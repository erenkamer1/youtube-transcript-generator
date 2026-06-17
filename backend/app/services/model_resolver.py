from __future__ import annotations

from app.config import settings
from app.services.ollama_client import list_models

PREFERRED_MODELS = [
    settings.default_ollama_model,
    "qwen2.5:14b",
    "qwen2.5:32b",
    "qwen2.5-coder:14b-instruct-q5_K_M",
    "llama3.2:latest",
]


async def resolve_model(requested: str | None = None) -> str:
    if requested:
        return requested

    try:
        models = await list_models()
    except Exception:  # noqa: BLE001
        return settings.default_ollama_model

    names = [item.get("name", "") for item in models if item.get("name")]
    for candidate in PREFERRED_MODELS:
        if candidate in names:
            return candidate

    for name in names:
        if "qwen" in name.lower():
            return name

    return names[0] if names else settings.default_ollama_model
