from __future__ import annotations

import logging
import ctypes
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from app.config import settings
from app.schemas import SegmentSchema
from app.utils.debug_log import debug_log

logger = logging.getLogger(__name__)

_model: WhisperModel | None = None
_active_device: str | None = None
_active_model_name: str | None = None
_cuda_runtime_broken = False
_cpu_fallback_active = False


def is_cpu_fallback_active() -> bool:
    return _cpu_fallback_active


def _probe_cuda_runtime() -> None:
    global _cuda_runtime_broken

    if settings.whisper_device == "cpu":
        _cuda_runtime_broken = True
        return

    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() == 0:
            _cuda_runtime_broken = True
            logger.warning("CUDA cihazı yok, CPU kullanılacak.")
            return
    except Exception as exc:  # noqa: BLE001
        _cuda_runtime_broken = True
        logger.warning("CUDA kontrolü başarısız: %s", exc)
        return

    if sys.platform == "win32":
        try:
            ctypes.WinDLL("cublas64_12.dll")
            _cuda_runtime_broken = False
            logger.info("cuBLAS CUDA 12 DLL yüklendi — GPU transkripsiyon aktif.")
            return
        except OSError as exc:
            _cuda_runtime_broken = True
            logger.warning(
                "cublas64_12.dll yüklenemedi (%s). "
                "pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-nvrtc-cu12",
                exc,
            )
            return

    _cuda_runtime_broken = False


def get_cuda_status() -> dict:
    return {
        "cuda_available": not _cuda_runtime_broken and _resolve_device()[0] == "cuda",
        "active_device": _active_device or "not_loaded",
        "active_model": _active_model_name,
        "cuda_runtime_broken": _cuda_runtime_broken,
    }


_probe_cuda_runtime()


@dataclass
class TranscriptionResult:
    language: str | None
    segments: list[SegmentSchema]
    full_text: str
    device: str
    model_name: str


def _resolve_device() -> tuple[str, str]:
    if _cuda_runtime_broken or settings.whisper_device == "cpu":
        return "cpu", "int8"

    if settings.whisper_device != "auto":
        compute = settings.whisper_compute_type
        if compute == "auto":
            compute = "float16" if settings.whisper_device == "cuda" else "int8"
        return settings.whisper_device, compute

    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception as exc:  # noqa: BLE001
        logger.warning("CUDA kontrolü başarısız, CPU kullanılacak: %s", exc)

    return "cpu", "int8"


def _model_name_for_device(device: str) -> str:
    if device == "cpu":
        return settings.whisper_cpu_model
    return settings.whisper_model


def _load_model(device: str, compute_type: str, model_name: str) -> WhisperModel:
    return WhisperModel(model_name, device=device, compute_type=compute_type)


def _switch_to_cpu() -> tuple[WhisperModel, str]:
    global _model, _active_device, _active_model_name, _cuda_runtime_broken, _cpu_fallback_active

    logger.warning("Whisper CPU fallback devreye alınıyor.")
    _cuda_runtime_broken = True
    _cpu_fallback_active = True
    model_name = _model_name_for_device("cpu")
    _model = _load_model("cpu", "int8", model_name)
    _active_device = "cpu"
    _active_model_name = model_name
    return _model, _active_device


def get_whisper_model() -> tuple[WhisperModel, str]:
    global _model, _active_device, _active_model_name

    device, compute_type = _resolve_device()
    model_name = _model_name_for_device(device)

    if _model is None or _active_device != device or _active_model_name != model_name:
        logger.info(
            "Whisper modeli yükleniyor: %s (%s, %s)",
            model_name,
            device,
            compute_type,
        )
        try:
            _model = _load_model(device, compute_type, model_name)
            _active_device = device
            _active_model_name = model_name
        except Exception as exc:  # noqa: BLE001
            if device == "cuda":
                logger.warning("GPU yüklemesi başarısız, CPU fallback: %s", exc)
                return _switch_to_cpu()
            raise

    return _model, _active_device


def _collect_segments(
    model: WhisperModel,
    audio_path: str,
    *,
    audio_duration: float | None = None,
    on_progress: Callable[[float], None] | None = None,
) -> tuple[list[SegmentSchema], object]:
    segments_iter, info = model.transcribe(
        audio_path,
        beam_size=3 if _active_device == "cpu" else 5,
        vad_filter=True,
        word_timestamps=False,
    )

    segments: list[SegmentSchema] = []
    total_duration = audio_duration or getattr(info, "duration", None) or 0.0

    for segment in segments_iter:
        text = segment.text.strip()
        if not text:
            continue
        segments.append(
            SegmentSchema(start=segment.start, end=segment.end, text=text)
        )
        if on_progress and total_duration > 0:
            on_progress(min(0.99, segment.end / total_duration))

    if on_progress:
        on_progress(1.0)

    return segments, info


def transcribe_audio(
    audio_path: str,
    *,
    audio_duration: float | None = None,
    on_progress: Callable[[float], None] | None = None,
) -> TranscriptionResult:
    global _cpu_fallback_active

    _cpu_fallback_active = _cuda_runtime_broken or settings.whisper_device == "cpu"
    model, device = get_whisper_model()
    model_name = _active_model_name or _model_name_for_device(device)

    debug_log(
        location="transcriber.py:start",
        message="transcribe_audio started",
        data={
            "device": device,
            "model": model_name,
            "audio_path_exists": Path(audio_path).exists(),
            "audio_duration": audio_duration,
        },
        hypothesis_id="H5",
        run_id="perf-fix",
    )

    try:
        segments, info = _collect_segments(
            model,
            audio_path,
            audio_duration=audio_duration,
            on_progress=on_progress,
        )
    except Exception as exc:  # noqa: BLE001
        if device != "cuda":
            debug_log(
                location="transcriber.py:cpu_fail",
                message="transcribe failed on non-cuda device",
                data={"device": device, "error": str(exc)},
                hypothesis_id="H3",
                run_id="perf-fix",
            )
            raise

        logger.warning("CUDA transcribe hatası, CPU fallback deneniyor: %s", exc)
        debug_log(
            location="transcriber.py:cuda_fallback",
            message="CUDA failed, switching to CPU",
            data={"error": str(exc)},
            hypothesis_id="H3-H5",
            run_id="perf-fix",
        )
        model, device = _switch_to_cpu()
        model_name = _active_model_name or settings.whisper_cpu_model
        segments, info = _collect_segments(
            model,
            audio_path,
            audio_duration=audio_duration,
            on_progress=on_progress,
        )

    full_text = "\n".join(segment.text for segment in segments)
    debug_log(
        location="transcriber.py:done",
        message="transcribe_audio finished",
        data={
            "device": device,
            "model": model_name,
            "segment_count": len(segments),
            "text_len": len(full_text),
        },
        hypothesis_id="H2-H3",
        run_id="perf-fix",
    )
    return TranscriptionResult(
        language=getattr(info, "language", None),
        segments=segments,
        full_text=full_text,
        device=device,
        model_name=model_name,
    )
