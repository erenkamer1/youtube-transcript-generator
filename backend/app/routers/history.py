from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db, get_transcript, list_transcripts, load_segments
from app.schemas import HistoryItem, SummarizeRequest
from app.services.model_resolver import resolve_model
from app.services.summarizer import summarize_text
from app.utils.export import export_srt, export_txt, export_vtt

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=list[HistoryItem])
def history(db: Session = Depends(get_db)) -> list[HistoryItem]:
    records = list_transcripts(db)
    items: list[HistoryItem] = []
    for record in records:
        segments = load_segments(record)
        items.append(
            HistoryItem(
                id=record.id,
                url=record.url,
                title=record.title,
                duration=record.duration,
                language=record.language,
                created_at=record.created_at,
                segment_count=len(segments),
            )
        )
    return items


@router.post("/summarize")
async def summarize(payload: SummarizeRequest, db: Session = Depends(get_db)) -> dict:
    text = payload.text
    if not text:
        if payload.transcript_id is None:
            raise HTTPException(status_code=400, detail="Metin veya transcript_id gerekli.")
        record = get_transcript(db, payload.transcript_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Transkript bulunamadı.")
        text = record.full_text

    summary = await summarize_text(
        text=text,
        language=payload.language,
        model=payload.model or await resolve_model(None),
    )
    return {"summary": summary}


@router.get("/export/{transcript_id}/{format_name}")
def export_transcript(transcript_id: int, format_name: str, db: Session = Depends(get_db)) -> dict:
    record = get_transcript(db, transcript_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Transkript bulunamadı.")

    segments = load_segments(record)
    if format_name == "txt":
        content = export_txt(segments)
    elif format_name == "srt":
        content = export_srt(segments)
    elif format_name == "vtt":
        content = export_vtt(segments)
    else:
        raise HTTPException(status_code=400, detail="Desteklenmeyen format.")

    return {"filename": f"transcript-{transcript_id}.{format_name}", "content": content}
