import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

    # Paths
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
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    def __init__(self):
        for d in [self.DOCUMENTS_DIR, self.VECTOR_STORE_DIR, self.REPORTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

settings = Settings()
