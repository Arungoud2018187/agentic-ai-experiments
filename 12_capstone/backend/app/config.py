"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent


def _env_list(name, default):
    value = os.getenv(name)
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "NovaDesk Agentic Assistant"
    version: str = "1.0.0"
    description: str = "Multi-agent capstone: SQL, RAG and research behind one API."

    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "offline").lower())
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    )
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2"))
    openai_base_url: str = field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    )
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    llm_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    )

    database_path: Path = field(
        default_factory=lambda: Path(os.getenv("DATABASE_PATH", str(BACKEND_DIR / "data" / "demo.db")))
    )
    knowledge_base_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("KNOWLEDGE_BASE_PATH", str(BACKEND_DIR / "app" / "data" / "knowledge_base.json"))
        )
    )
    web_index_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("WEB_INDEX_PATH", str(BACKEND_DIR / "app" / "data" / "web_index.json"))
        )
    )

    cors_origins: tuple = field(
        default_factory=lambda: tuple(
            _env_list(
                "CORS_ORIGINS",
                [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "http://localhost:8000",
                    "http://127.0.0.1:8000",
                ],
            )
        )
    )
    static_dir: Path = field(
        default_factory=lambda: Path(os.getenv("STATIC_DIR", str(PROJECT_DIR / "frontend" / "dist")))
    )


settings = Settings()
