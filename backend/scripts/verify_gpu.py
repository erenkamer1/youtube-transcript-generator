"""GPU and Whisper availability checks."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


def main() -> int:
    print("=== Whisper / GPU Verification ===")

    try:
        import ctranslate2

        cuda_count = ctranslate2.get_cuda_device_count()
        print(f"CTranslate2 CUDA devices: {cuda_count}")
    except Exception as exc:  # noqa: BLE001
        print(f"CTranslate2 CUDA check failed: {exc}")

    try:
        from app.services.transcriber import _resolve_device

        device, compute = _resolve_device()
        print(f"Resolved Whisper device: {device} ({compute})")
    except Exception as exc:  # noqa: BLE001
        print(f"Device resolution failed: {exc}")
        return 1

    try:
        from app.services.transcriber import get_whisper_model

        model, active_device = get_whisper_model()
        print(f"Whisper model loaded on: {active_device}")
        del model
    except Exception as exc:  # noqa: BLE001
        print(f"Whisper model load failed: {exc}")
        print("CPU fallback will be used at runtime if GPU fails.")
        return 1

    print("Verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
