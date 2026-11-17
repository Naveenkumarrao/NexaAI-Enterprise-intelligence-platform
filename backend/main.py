from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.database import init_db
from backend.api.documents import router as documents_router
from backend.api.tasks import router as tasks_router
from backend.api.analysis import router as analysis_router
from backend.llm_factory import get_llm_info
from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Enterprise Agentic AI Platform",
    description="Multi-Agent Document Intelligence, Analysis, Comparison & Recommendation System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(tasks_router)
app.include_router(analysis_router)


@app.get("/")
def root():
    return {"message": "Enterprise Agentic AI Platform API", "status": "running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/llm-info")
def llm_info():
    """Return the currently configured LLM provider and model."""
    info = get_llm_info()
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "provider_label": info.get("provider", settings.LLM_PROVIDER),
        "model": info.get("model", "unknown"),
        "api_key_required": info.get("api_key_required", False),
        "api_key_set": info.get("api_key_set", True),
        "ready": info.get("api_key_set", True),
    }


if __name__ == "__main__":
    import uvicorn
    from backend.config import settings
    uvicorn.run("backend.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
