import json
from collections.abc import AsyncIterator

from app.schemas import ProgressEvent


def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def progress(stage: str, message: str, progress: float | None = None) -> AsyncIterator[str]:
    payload = ProgressEvent(stage=stage, message=message, progress=progress).model_dump()
    yield sse_event("progress", payload)
