import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root
load_dotenv(BASE_DIR / ".env")


class Settings:
    # ------------------------------------------------------------------
    # LLM Provider Selection
    # Supported values: "ollama" | "openai" | "anthropic" | "google" | "gemini"
    # ------------------------------------------------------------------
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

    # Ollama (local — no API key needed)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str    = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

    # Single API key — shared across all cloud providers
    API_KEY: str  = os.getenv("API_KEY", "")

    # Optional gateway — custom base URL, proxy, or Azure endpoint
    GATEWAY: str  = os.getenv("GATEWAY", "")

    # Built-in model defaults (not exposed in .env)
    OPENAI_MODEL:    str = "gpt-4o-mini"
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"
    GOOGLE_MODEL:    str = "gemini-1.5-flash"

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    DATA_DIR: Path = BASE_DIR / "data"
    DOCUMENTS_DIR: Path = DATA_DIR / "documents"
    VECTOR_STORE_DIR: Path = DATA_DIR / "vector_store"
    REPORTS_DIR: Path = DATA_DIR / "reports"

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR}/app.db"

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    def __init__(self):
        for d in [self.DOCUMENTS_DIR, self.VECTOR_STORE_DIR, self.REPORTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)
        self._validate()

    def _validate(self):
        """Warn at startup if a cloud provider is selected but API_KEY is missing."""
        provider = self.LLM_PROVIDER.lower()
        cloud_providers = {"openai", "anthropic", "google", "gemini"}
        if provider in cloud_providers and not self.API_KEY:
            import warnings
            warnings.warn(
                f"[NexaAI] LLM_PROVIDER is '{provider}' but API_KEY is not set in .env. "
                "Add your API key or switch to LLM_PROVIDER=ollama.",
                stacklevel=2,
            )


settings = Settings()
