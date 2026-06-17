from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.db import get_db, get_transcript, save_translation
from app.schemas import TranslateRequest
from app.services.model_resolver import resolve_model
from app.services.translator import stream_translate_text, translate_text
from app.utils.sse import sse_event

router = APIRouter(prefix="/api", tags=["translate"])


def _resolve_text(payload: TranslateRequest, db: Session) -> tuple[str, int | None]:
    if payload.text:
        return payload.text, payload.transcript_id

    if payload.transcript_id is None:
        raise HTTPException(status_code=400, detail="Metin veya transcript_id gerekli.")

    record = get_transcript(db, payload.transcript_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Transkript bulunamadı.")

    return record.full_text, record.id


@router.post("/translate")
async def translate(payload: TranslateRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    text, transcript_id = _resolve_text(payload, db)
    model = await resolve_model(payload.model)

    async def event_stream() -> AsyncIterator[str]:
        try:
            translated_parts: list[str] = []
            async for token in stream_translate_text(
                text=text,
                target_language=payload.target_language,
                model=model,
                tone=payload.tone,
            ):
                translated_parts.append(token)
                yield sse_event("token", {"token": token})

            translated_text = "".join(translated_parts)
            if transcript_id is not None:
                save_translation(
                    db,
                    transcript_id=transcript_id,
                    target_language=payload.target_language,
                    model=model,
                    tone=payload.tone,
                    translated_text=translated_text,
                )

            yield sse_event("complete", {"text": translated_text})
        except Exception as exc:  # noqa: BLE001
            yield sse_event("error", {"message": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/translate/sync")
async def translate_sync(payload: TranslateRequest, db: Session = Depends(get_db)) -> dict:
    text, transcript_id = _resolve_text(payload, db)
    model = await resolve_model(payload.model)
    translated_text = await translate_text(
        text=text,
        target_language=payload.target_language,
        model=model,
        tone=payload.tone,
    )

    if transcript_id is not None:
        save_translation(
            db,
            transcript_id=transcript_id,
            target_language=payload.target_language,
            model=model,
            tone=payload.tone,
            translated_text=translated_text,
        )

    return {"text": translated_text}
