from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db, get_transcript
from app.schemas import GeneratePromptRequest, GeneratePromptResponse
from app.services.prompt_generator import build_prompt

router = APIRouter(prefix="/api", tags=["prompts"])


@router.post("/generate-prompt", response_model=GeneratePromptResponse)
def generate_prompt(payload: GeneratePromptRequest, db: Session = Depends(get_db)) -> GeneratePromptResponse:
    text = payload.text
    if not text:
        if payload.transcript_id is None:
            raise HTTPException(status_code=400, detail="Metin veya transcript_id gerekli.")
        record = get_transcript(db, payload.transcript_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Transkript bulunamadı.")
        text = record.full_text

    prompt = build_prompt(
        template_key=payload.template,
        transcript_text=text,
        language=payload.language,
    )
    return GeneratePromptResponse(template=payload.template, prompt=prompt)
