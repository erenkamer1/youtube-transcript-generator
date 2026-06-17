from __future__ import annotations

from collections.abc import AsyncIterator

from app.config import settings
from app.services.model_resolver import resolve_model
from app.services.ollama_client import generate_text, stream_generate_text


TONE_INSTRUCTIONS = {
    "formal": "Use a clear, formal, and natural tone.",
    "casual": "Use a simple, conversational, and easy-to-read tone.",
}


def split_text_into_chunks(text: str, max_chars: int | None = None) -> list[str]:
    limit = max_chars or settings.translation_chunk_chars
    paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= limit:
            current = paragraph
            continue

        start = 0
        while start < len(paragraph):
            chunks.append(paragraph[start : start + limit])
            start += limit

    if current:
        chunks.append(current)

    return chunks


def build_translation_prompt(
    *,
    chunk: str,
    target_language: str,
    tone: str,
    previous_context: str | None = None,
) -> tuple[str, str]:
    tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["formal"])
    system = (
        "You are a professional translator. Preserve meaning, terminology, names, "
        "numbers, and formatting. Do not add commentary."
    )
    context_block = (
        f"\n\nPrevious translated context for consistency:\n{previous_context}\n"
        if previous_context
        else ""
    )
    prompt = (
        f"Translate the following transcript text into {target_language}. "
        f"{tone_instruction}{context_block}\n\n"
        "Return only the translated text.\n\n"
        f"Text:\n{chunk}"
    )
    return system, prompt


async def translate_text(
    *,
    text: str,
    target_language: str,
    model: str | None = None,
    tone: str = "formal",
) -> str:
    selected_model = await resolve_model(model)
    chunks = split_text_into_chunks(text)
    translated_parts: list[str] = []
    previous_context = None

    for chunk in chunks:
        system, prompt = build_translation_prompt(
            chunk=chunk,
            target_language=target_language,
            tone=tone,
            previous_context=previous_context,
        )
        translated = await generate_text(model=selected_model, prompt=prompt, system=system)
        translated_parts.append(translated.strip())
        previous_context = translated_parts[-1][-500:]

    return "\n\n".join(translated_parts)


async def stream_translate_text(
    *,
    text: str,
    target_language: str,
    model: str | None = None,
    tone: str = "formal",
) -> AsyncIterator[str]:
    selected_model = await resolve_model(model)
    chunks = split_text_into_chunks(text)
    previous_context = None

    for index, chunk in enumerate(chunks):
        if index > 0:
            yield "\n\n"

        system, prompt = build_translation_prompt(
            chunk=chunk,
            target_language=target_language,
            tone=tone,
            previous_context=previous_context,
        )

        chunk_output = ""
        async for token in stream_generate_text(
            model=selected_model,
            prompt=prompt,
            system=system,
        ):
            chunk_output += token
            yield token

        previous_context = chunk_output[-500:]
