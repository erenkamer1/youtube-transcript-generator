import json
from collections.abc import Generator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base, TranscriptRecord, TranslationRecord
from app.schemas import SegmentSchema

db_path = settings.data_dir / "app.db"
engine = create_engine(
    f"sqlite:///{db_path.as_posix()}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_transcript(
    db: Session,
    *,
    url: str,
    title: str,
    duration: float | None,
    language: str | None,
    segments: list[SegmentSchema],
    full_text: str,
) -> TranscriptRecord:
    record = TranscriptRecord(
        url=url,
        title=title,
        duration=duration,
        language=language,
        full_text=full_text,
        segments_json=json.dumps([segment.model_dump() for segment in segments]),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_transcript(db: Session, transcript_id: int) -> TranscriptRecord | None:
    return db.get(TranscriptRecord, transcript_id)


def list_transcripts(db: Session, limit: int = 50) -> list[TranscriptRecord]:
    stmt = (
        select(TranscriptRecord)
        .order_by(TranscriptRecord.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def save_translation(
    db: Session,
    *,
    transcript_id: int,
    target_language: str,
    model: str,
    tone: str,
    translated_text: str,
) -> TranslationRecord:
    record = TranslationRecord(
        transcript_id=transcript_id,
        target_language=target_language,
        model=model,
        tone=tone,
        translated_text=translated_text,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def load_segments(record: TranscriptRecord) -> list[SegmentSchema]:
    raw = json.loads(record.segments_json)
    return [SegmentSchema.model_validate(item) for item in raw]
