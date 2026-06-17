import asyncio
import time
from collections.abc import AsyncIterator, Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.db import get_db, load_segments, save_transcript
from app.schemas import TranscribeRequest, TranscribeResult
from app.services.downloader import download_audio
from app.services.transcriber import is_cpu_fallback_active, transcribe_audio
from app.utils.debug_log import debug_log
from app.utils.sse import sse_event

router = APIRouter(prefix="/api", tags=["transcribe"])

DOWNLOAD_START = 0.05
DOWNLOAD_END = 0.30
TRANSCRIBE_START = 0.35
TRANSCRIBE_END = 0.92
SAVE_PROGRESS = 0.95


def _progress_payload(stage: str, message: str, progress: float) -> dict:
    return {
        "stage": stage,
        "message": message,
        "progress": round(progress, 3),
    }


def _format_elapsed(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


async def _poll_task_progress(
    task: asyncio.Task,
    *,
    stage: str,
    message: str,
    start: float,
    end: float,
    get_live_progress: Callable[[], float] | None = None,
    tick_seconds: float = 0.4,
) -> AsyncIterator[str]:
    last_progress = -1.0

    while not task.done():
        if get_live_progress is not None:
            live = get_live_progress()
            progress = start + (end - start) * live
        else:
            progress = start

        if progress - last_progress >= 0.005:
            yield sse_event(
                "progress",
                _progress_payload(stage, message, progress),
            )
            last_progress = progress

        await asyncio.sleep(tick_seconds)

    if last_progress < end:
        yield sse_event(
            "progress",
            _progress_payload(stage, message, end),
        )


@router.post("/transcribe")
async def transcribe_video(
    payload: TranscribeRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        audio_path = None
        download_fraction = {"value": 0.0}

        try:
            yield sse_event(
                "progress",
                _progress_payload("init", "Başlatılıyor...", 0.02),
            )

            def on_download_progress(fraction: float) -> None:
                download_fraction["value"] = fraction

            download_task = asyncio.create_task(
                asyncio.to_thread(
                    download_audio,
                    payload.url,
                    on_download_progress,
                )
            )

            async for item in _poll_task_progress(
                download_task,
                stage="download",
                message="Video sesi indiriliyor...",
                start=DOWNLOAD_START,
                end=DOWNLOAD_END,
                get_live_progress=lambda: download_fraction["value"],
                tick_seconds=0.3,
            ):
                yield item

            download = await download_task
            audio_path = download.audio_path
            duration_label = (
                f"{int(download.duration // 60)} dk" if download.duration else "bilinmiyor"
            )

            yield sse_event(
                "progress",
                _progress_payload(
                    "transcribe",
                    f"Transkript oluşturuluyor ({duration_label} video)...",
                    TRANSCRIBE_START,
                ),
            )

            transcribe_fraction = {"value": 0.0}
            started_at = time.monotonic()

            def run_transcribe():
                return transcribe_audio(
                    str(audio_path),
                    audio_duration=download.duration,
                    on_progress=lambda fraction: transcribe_fraction.update(value=fraction),
                )

            transcribe_task = asyncio.create_task(asyncio.to_thread(run_transcribe))

            tick_count = 0
            while not transcribe_task.done():
                await asyncio.sleep(1.0)
                tick_count += 1
                elapsed = time.monotonic() - started_at

                live = transcribe_fraction["value"]
                if live > 0:
                    progress = TRANSCRIBE_START + (TRANSCRIBE_END - TRANSCRIBE_START) * live
                else:
                    progress = TRANSCRIBE_START + min(
                        0.08,
                        (TRANSCRIBE_END - TRANSCRIBE_START) * (1 - pow(0.985, tick_count)),
                    )

                cpu_active = is_cpu_fallback_active()
                message = (
                    f"Transkript oluşturuluyor — geçen süre {_format_elapsed(elapsed)} "
                    f"(CPU/{duration_label} video, lütfen bekleyin)..."
                    if cpu_active
                    else f"Transkript oluşturuluyor — geçen süre {_format_elapsed(elapsed)}..."
                )

                if tick_count == 1 or tick_count % 10 == 0:
                    debug_log(
                        location="transcribe.py:poll_loop",
                        message="transcribe still running",
                        data={
                            "tick": tick_count,
                            "progress": round(progress, 3),
                            "live_fraction": round(live, 3),
                            "elapsed_sec": round(elapsed, 1),
                            "cpu_fallback": cpu_active,
                        },
                        hypothesis_id="H1-H2",
                        run_id="perf-fix",
                    )

                yield sse_event(
                    "progress",
                    _progress_payload("transcribe", message, progress),
                )

            transcription = await transcribe_task
            debug_log(
                location="transcribe.py:transcribe_done",
                message="transcribe task finished",
                data={
                    "device": transcription.device,
                    "model": transcription.model_name,
                    "segment_count": len(transcription.segments),
                    "language": transcription.language,
                },
                hypothesis_id="H2-H3",
                run_id="perf-fix",
            )

            yield sse_event(
                "progress",
                _progress_payload("transcribe", "Transkript tamamlandı.", TRANSCRIBE_END),
            )

            yield sse_event(
                "progress",
                _progress_payload("save", "Sonuç kaydediliyor...", SAVE_PROGRESS),
            )

            record = save_transcript(
                db,
                url=download.url,
                title=download.title,
                duration=download.duration,
                language=transcription.language,
                segments=transcription.segments,
                full_text=transcription.full_text,
            )

            result = TranscribeResult(
                id=record.id,
                url=record.url,
                title=record.title,
                duration=record.duration,
                language=record.language,
                segments=transcription.segments,
                full_text=record.full_text,
            )

            yield sse_event(
                "progress",
                _progress_payload("complete", "Tamamlandı.", 1.0),
            )
            yield sse_event("complete", result.model_dump())
            debug_log(
                location="transcribe.py:complete_sent",
                message="complete SSE event sent",
                data={"transcript_id": result.id, "title": result.title},
                hypothesis_id="H4",
                run_id="perf-fix",
            )
        except Exception as exc:  # noqa: BLE001
            debug_log(
                location="transcribe.py:exception",
                message="transcribe stream error",
                data={"error": str(exc), "type": type(exc).__name__},
                hypothesis_id="H3",
                run_id="perf-fix",
            )
            yield sse_event("error", {"message": str(exc)})
        finally:
            if audio_path and audio_path.exists():
                audio_path.unlink(missing_ok=True)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/transcripts/{transcript_id}", response_model=TranscribeResult)
def get_transcript(transcript_id: int, db: Session = Depends(get_db)) -> TranscribeResult:
    from app.db import get_transcript as fetch_transcript

    record = fetch_transcript(db, transcript_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Transkript bulunamadı.")

    return TranscribeResult(
        id=record.id,
        url=record.url,
        title=record.title,
        duration=record.duration,
        language=record.language,
        segments=load_segments(record),
        full_text=record.full_text,
    )
