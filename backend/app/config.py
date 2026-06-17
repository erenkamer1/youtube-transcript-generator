from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "YouTube Transcript Generator"
    debug: bool = False

    backend_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = backend_dir / "data"
    temp_dir: Path = backend_dir / "temp"
    database_url: str = "sqlite:///./data/app.db"

    ollama_base_url: str = "http://127.0.0.1:11434"
    default_ollama_model: str = "qwen2.5:14b"

    whisper_model: str = "large-v3"
    whisper_cpu_model: str = "medium"
    whisper_device: str = "auto"  # auto | cuda | cpu
    whisper_compute_type: str = "auto"  # auto | float16 | int8

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    translation_chunk_chars: int = 3500
    summary_max_input_chars: int = 12000


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.temp_dir.mkdir(parents=True, exist_ok=True)
