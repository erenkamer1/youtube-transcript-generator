from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from app.config import settings


class OllamaError(RuntimeError):
    pass


async def list_models() -> list[dict]:
    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=30.0) as client:
        response = await client.get("/api/tags")
        response.raise_for_status()
        payload = response.json()
        return payload.get("models", [])


async def generate_text(
    *,
    model: str,
    prompt: str,
    system: str | None = None,
    temperature: float = 0.2,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=None) as client:
        response = await client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature},
            },
        )
        if response.status_code >= 400:
            raise OllamaError(response.text)
        payload = response.json()
        return payload.get("message", {}).get("content", "").strip()


async def stream_generate_text(
    *,
    model: str,
    prompt: str,
    system: str | None = None,
    temperature: float = 0.2,
) -> AsyncIterator[str]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=None) as client:
        async with client.stream(
            "POST",
            "/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temperature},
            },
        ) as response:
            if response.status_code >= 400:
                body = await response.aread()
                raise OllamaError(body.decode("utf-8", errors="ignore"))

            async for line in response.aiter_lines():
                if not line:
                    continue
                payload = json.loads(line)
                message = payload.get("message", {})
                content = message.get("content")
                if content:
                    yield content
                if payload.get("done"):
                    break
