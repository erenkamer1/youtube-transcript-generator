from app.config import settings
from app.services.model_resolver import resolve_model
from app.services.ollama_client import generate_text


async def summarize_text(
    *,
    text: str,
    language: str = "Turkish",
    model: str | None = None,
) -> str:
    selected_model = await resolve_model(model)
    clipped = text[: settings.summary_max_input_chars]
    system = (
        "You summarize long transcripts clearly. Keep headings, bullet points, and key takeaways."
    )
    prompt = (
        f"Summarize the following transcript in {language}. "
        "Include main topics, key points, and actionable insights.\n\n"
        f"Transcript:\n{clipped}"
    )
    return await generate_text(model=selected_model, prompt=prompt, system=system)
