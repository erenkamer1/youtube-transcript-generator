"""Smoke test for core API flows."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

BASE_URL = "http://127.0.0.1:8000"
SHORT_VIDEO = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


def consume_transcribe(url: str) -> dict:
    with httpx.Client(timeout=None) as client:
        with client.stream(
            "POST",
            f"{BASE_URL}/api/transcribe",
            json={"url": url},
        ) as response:
            response.raise_for_status()
            buffer = ""
            for chunk in response.iter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    part, buffer = buffer.split("\n\n", 1)
                    if not part.strip():
                        continue
                    event = None
                    data = None
                    for line in part.split("\n"):
                        if line.startswith("event:"):
                            event = line.replace("event:", "").strip()
                        if line.startswith("data:"):
                            data = json.loads(line.replace("data:", "").strip())
                    if event == "complete":
                        return data
                    if event == "error":
                        raise RuntimeError(data.get("message", "Transcribe failed"))
    raise RuntimeError("Transcribe stream ended without complete event")


def main() -> int:
    print("Health check...")
    health = httpx.get(f"{BASE_URL}/api/health", timeout=10)
    health.raise_for_status()
    print(health.json())

    print("Transcribe short video...")
    result = consume_transcribe(SHORT_VIDEO)
    print(
        f"OK transcript id={result['id']} title={result['title']!r} "
        f"segments={len(result['segments'])} language={result.get('language')}"
    )

    print("Generate prompt...")
    prompt_resp = httpx.post(
        f"{BASE_URL}/api/generate-prompt",
        json={
            "transcript_id": result["id"],
            "template": "rules_tips",
            "language": "Turkish",
        },
        timeout=30,
    )
    prompt_resp.raise_for_status()
    assert len(prompt_resp.json()["prompt"]) > 100

    print("Translate sync sample...")
    translate_resp = httpx.post(
        f"{BASE_URL}/api/translate/sync",
        json={
            "text": result["full_text"][:500],
            "target_language": "Turkish",
            "tone": "formal",
        },
        timeout=None,
    )
    translate_resp.raise_for_status()
    translated = translate_resp.json()["text"]
    print(f"Translation sample length: {len(translated)}")

    print("History...")
    history = httpx.get(f"{BASE_URL}/api/history", timeout=10)
    history.raise_for_status()
    print(f"History count: {len(history.json())}")

    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
