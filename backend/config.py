import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root
load_dotenv(BASE_DIR / ".env")


class Settings:
    # ------------------------------------------------------------------
    # LLM Provider Selection
    # Supported values: "ollama" | "openai" | "anthropic" | "google"
    # ------------------------------------------------------------------
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

    # Ollama (local)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

    # OpenAI — API key required; base URL is optional (custom gateway / Azure proxy)
    OPENAI_API_KEY: str  = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")   # optional
    OPENAI_MODEL: str    = "gpt-4o-mini"                       # default, not in .env

    # Anthropic — API key required; base URL is optional (custom gateway)
    ANTHROPIC_API_KEY: str  = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_BASE_URL: str = os.getenv("ANTHROPIC_BASE_URL", "")  # optional
    ANTHROPIC_MODEL: str    = "claude-3-haiku-20240307"             # default, not in .env

    # Google Gemini — API key required
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_MODEL: str   = "gemini-1.5-flash"                   # default, not in .env

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
        """Warn at startup if the selected provider has no API key configured."""
        provider = self.LLM_PROVIDER.lower()
        missing = {
            "openai":    not self.OPENAI_API_KEY,
            "anthropic": not self.ANTHROPIC_API_KEY,
            "google":    not self.GOOGLE_API_KEY,
        }
        if provider in missing and missing[provider]:
            import warnings
            warnings.warn(
                f"[NexaAI] LLM_PROVIDER is '{provider}' but the corresponding "
                f"API key is not set in .env. Set the key or switch to 'ollama'.",
                stacklevel=2,
            )


settings = Settings()
