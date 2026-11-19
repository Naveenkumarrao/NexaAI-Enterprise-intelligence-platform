"""
llm_factory.py
==============
Central LLM provider factory for NexaAI.

Reads LLM_PROVIDER from .env (via config.py) and returns the appropriate
LangChain chat model.  All agents import `get_llm()` from here — no
provider-specific code lives in the agents themselves.

Supported providers
-------------------
  ollama    → ChatOllama    (local, no API key needed)
  openai    → ChatOpenAI   (requires OPENAI_API_KEY)
  anthropic → ChatAnthropic (requires ANTHROPIC_API_KEY)
  google    → ChatGoogleGenerativeAI (requires GOOGLE_API_KEY)
"""

from __future__ import annotations
from typing import Optional
from backend.config import settings


def get_llm(temperature: float = 0.1):
    """
    Return a LangChain chat model configured via .env settings.

    Parameters
    ----------
    temperature : float
        Sampling temperature passed to the underlying model.

    Returns
    -------
    A LangChain BaseChatModel instance ready for `.invoke()` calls.

    Raises
    ------
    ValueError
        If LLM_PROVIDER is unrecognised or the required API key is missing.
    """
    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "ollama":
        return _build_ollama(temperature)
    elif provider == "openai":
        return _build_openai(temperature)
    elif provider == "anthropic":
        return _build_anthropic(temperature)
    elif provider in {"google", "gemini"}:
        return _build_google(temperature)
    else:
        raise ValueError(
            f"[NexaAI] Unknown LLM_PROVIDER='{provider}'. "
            "Valid options: ollama | openai | anthropic | google (or gemini)"
        )


# ---------------------------------------------------------------------------
# Provider builders
# ---------------------------------------------------------------------------

def _build_ollama(temperature: float):
    try:
        from langchain_ollama import ChatOllama
    except ImportError as exc:
        raise ImportError(
            "langchain-ollama is not installed. Run: pip install langchain-ollama"
        ) from exc

    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=temperature,
    )


def _build_openai(temperature: float):
    if not settings.API_KEY:
        raise ValueError(
            "[NexaAI] API_KEY is not set in .env. "
            "Add your OpenAI key or set LLM_PROVIDER=ollama."
        )
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise ImportError(
            "langchain-openai is not installed. Run: pip install langchain-openai"
        ) from exc

    kwargs = dict(
        model=settings.OPENAI_MODEL,
        api_key=settings.API_KEY,
        temperature=temperature,
    )
    if settings.GATEWAY:
        kwargs["base_url"] = settings.GATEWAY

    return ChatOpenAI(**kwargs)


def _build_anthropic(temperature: float):
    if not settings.API_KEY:
        raise ValueError(
            "[NexaAI] API_KEY is not set in .env. "
            "Add your Anthropic key or set LLM_PROVIDER=ollama."
        )
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as exc:
        raise ImportError(
            "langchain-anthropic is not installed. Run: pip install langchain-anthropic"
        ) from exc

    kwargs = dict(
        model=settings.ANTHROPIC_MODEL,
        api_key=settings.API_KEY,
        temperature=temperature,
    )
    if settings.GATEWAY:
        kwargs["base_url"] = settings.GATEWAY

    return ChatAnthropic(**kwargs)


def _build_google(temperature: float):
    if not settings.API_KEY:
        raise ValueError(
            "[NexaAI] API_KEY is not set in .env. "
            "Add your Google API key or set LLM_PROVIDER=ollama."
        )
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise ImportError(
            "langchain-google-genai is not installed. "
            "Run: pip install langchain-google-genai"
        ) from exc

    return ChatGoogleGenerativeAI(
        model=settings.GOOGLE_MODEL,
        google_api_key=settings.API_KEY,
        temperature=temperature,
    )


# ---------------------------------------------------------------------------
# Convenience helper — returns a plain dict describing the active provider
# ---------------------------------------------------------------------------

def get_llm_info() -> dict:
    """Return metadata about the currently configured LLM provider."""
    provider = settings.LLM_PROVIDER.lower().strip()
    info_map = {
        "ollama": {
            "provider": "Ollama (Local)",
            "model": settings.OLLAMA_MODEL,
            "api_key_required": False,
            "api_key_set": True,
            "gateway": settings.OLLAMA_BASE_URL,
        },
        "openai": {
            "provider": "OpenAI",
            "model": settings.OPENAI_MODEL,
            "api_key_required": True,
            "api_key_set": bool(settings.API_KEY),
            "gateway": settings.GATEWAY or None,
        },
        "anthropic": {
            "provider": "Anthropic",
            "model": settings.ANTHROPIC_MODEL,
            "api_key_required": True,
            "api_key_set": bool(settings.API_KEY),
            "gateway": settings.GATEWAY or None,
        },
        "google": {
            "provider": "Google Gemini",
            "model": settings.GOOGLE_MODEL,
            "api_key_required": True,
            "api_key_set": bool(settings.API_KEY),
            "gateway": settings.GATEWAY or None,
        },
        "gemini": {
            "provider": "Google Gemini",
            "model": settings.GOOGLE_MODEL,
            "api_key_required": True,
            "api_key_set": bool(settings.API_KEY),
            "gateway": settings.GATEWAY or None,
        },
    }
    return info_map.get(provider, {"provider": provider, "model": "unknown"})
