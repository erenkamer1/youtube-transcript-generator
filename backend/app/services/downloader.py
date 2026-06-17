from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import yt_dlp

from app.config import settings


@dataclass
class DownloadResult:
    audio_path: Path
    title: str
    duration: float | None
    url: str


def download_audio(
    url: str,
    on_progress: Callable[[float], None] | None = None,
) -> DownloadResult:
    output_dir = settings.temp_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    token = uuid4().hex
    output_template = str(output_dir / f"{token}.%(ext)s")

    def progress_hook(status: dict) -> None:
        if not on_progress:
            return
        if status.get("status") == "downloading":
            total = status.get("total_bytes") or status.get("total_bytes_estimate")
            downloaded = status.get("downloaded_bytes") or 0
            if total:
                on_progress(min(0.99, downloaded / total))
        elif status.get("status") == "finished":
            on_progress(1.0)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }
    if on_progress:
        ydl_opts["progress_hooks"] = [progress_hook]
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise RuntimeError("Video bilgisi alınamadı.")

        if "entries" in info:
            info = info["entries"][0]

        title = info.get("title") or "Untitled"
        duration = info.get("duration")
        resolved_url = info.get("webpage_url") or url

    candidates = sorted(output_dir.glob(f"{token}.*"))
    audio_files = [path for path in candidates if path.suffix.lower() in {".wav", ".mp3", ".m4a", ".webm", ".opus"}]
    if not audio_files:
        raise RuntimeError("Ses dosyası indirilemedi.")

    return DownloadResult(
        audio_path=audio_files[0],
        title=title,
        duration=float(duration) if duration is not None else None,
        url=resolved_url,
    )
