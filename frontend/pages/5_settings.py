import streamlit as st
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
from ui import apply_theme, page_header

# Load .env so the status table reflects the actual file values
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Nexa AI | Settings",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
page_header(
    "Platform settings",
    "Configure your LLM provider, review API key status, and manage platform options.",
    "SETTINGS",
)

# ---------------------------------------------------------------------------
# Live provider status card
# ---------------------------------------------------------------------------
st.subheader("LLM provider")
st.caption(
    "NexaAI supports local Ollama models and cloud API providers. "
    "Switch providers by editing `LLM_PROVIDER` in your `.env` file."
)

try:
    resp = requests.get(f"{API_BASE}/llm-info", timeout=4)
    info = resp.json()

    provider  = info.get("provider_label", "Unknown")
    model     = info.get("model", "unknown")
    key_needed = info.get("api_key_required", False)
    key_set   = info.get("api_key_set", True)
    gateway   = info.get("gateway") or None
    ready     = info.get("ready", False)

    status_col, detail_col = st.columns([1, 2])

    with status_col:
        with st.container(border=True):
            st.success("✅ Provider ready") if ready else st.error("❌ API key missing")
            st.markdown(f"**Provider**  \n{provider}")
            st.markdown(f"**Model**  \n`{model}`")
            if key_needed:
                st.markdown("**API key**  \n🔑 Configured" if key_set else "**API key**  \n⚠️ Not set")
            else:
                st.markdown("**API key**  \n🏠 Not required (local)")
            if gateway:
                st.markdown(f"**Gateway**  \n`{gateway}`")

    with detail_col:
        with st.container(border=True):
            st.markdown("#### How to switch providers")
            st.markdown(
                "Open **`.env`** in the project root, set `LLM_PROVIDER` and the "
                "matching API key, then restart the server. Model names are built-in "
                "defaults — no need to set them."
            )
            st.code(
                "# .env\n"
                "\n"
                "# Choose one: ollama | openai | anthropic | google\n"
                "LLM_PROVIDER=openai\n"
                "\n"
                "# OpenAI\n"
                "OPENAI_API_KEY=sk-...\n"
                "OPENAI_BASE_URL=          # optional — custom gateway\n"
                "\n"
                "# Anthropic\n"
                "ANTHROPIC_API_KEY=sk-ant-...\n"
                "ANTHROPIC_BASE_URL=       # optional — custom gateway\n"
                "\n"
                "# Google Gemini\n"
                "GOOGLE_API_KEY=AIza...\n"
                "\n"
                "# Ollama (local)\n"
                "OLLAMA_BASE_URL=http://localhost:11434\n"
                "OLLAMA_MODEL=qwen2.5:1.5b",
                language="ini",
            )

except Exception:
    st.warning("Could not reach the API server. Start it first, then refresh.")

st.divider()

# ---------------------------------------------------------------------------
# Provider cards
# ---------------------------------------------------------------------------
st.subheader("Supported providers")
st.caption("All providers share the same agent workflow — only the LLM backend changes.")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    with st.container(border=True):
        st.markdown("### 🏠 Ollama")
        st.markdown("**Local · No API key**")
        st.caption("Run open-weight models on your own machine. Best for privacy-sensitive workloads.")
        st.code("LLM_PROVIDER=ollama", language="ini")

with col_b:
    with st.container(border=True):
        st.markdown("### 🟢 OpenAI")
        st.markdown("**Cloud · API key required**")
        st.caption("GPT-4o-mini by default. Custom gateway supported via `OPENAI_BASE_URL`.")
        st.code("LLM_PROVIDER=openai", language="ini")

with col_c:
    with st.container(border=True):
        st.markdown("### 🟣 Anthropic")
        st.markdown("**Cloud · API key required**")
        st.caption("Claude 3 Haiku by default. Custom gateway supported via `ANTHROPIC_BASE_URL`.")
        st.code("LLM_PROVIDER=anthropic", language="ini")

with col_d:
    with st.container(border=True):
        st.markdown("### 🔵 Google")
        st.markdown("**Cloud · API key required**")
        st.caption("Gemini 1.5 Flash by default. Get a free key at Google AI Studio.")
        st.code("LLM_PROVIDER=google", language="ini")

st.divider()

# ---------------------------------------------------------------------------
# Where to get API keys
# ---------------------------------------------------------------------------
st.subheader("Where to get your API keys")

k1, k2, k3 = st.columns(3)
with k1:
    with st.container(border=True):
        st.markdown("**OpenAI**")
        st.caption("platform.openai.com → API Keys")
        st.code("OPENAI_API_KEY=sk-...", language="ini")

with k2:
    with st.container(border=True):
        st.markdown("**Anthropic**")
        st.caption("console.anthropic.com → Settings → Keys")
        st.code("ANTHROPIC_API_KEY=sk-ant-...", language="ini")

with k3:
    with st.container(border=True):
        st.markdown("**Google Gemini**")
        st.caption("aistudio.google.com → Get API key")
        st.code("GOOGLE_API_KEY=AIza...", language="ini")

st.divider()

# ---------------------------------------------------------------------------
# .env variable status (masked)
# ---------------------------------------------------------------------------
st.subheader(".env status")
st.caption("API keys are masked. Model names are built-in defaults and not read from `.env`.")

rows = [
    ("LLM_PROVIDER",      os.getenv("LLM_PROVIDER", "ollama"),                  ""),
    ("OLLAMA_BASE_URL",   os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), ""),
    ("OLLAMA_MODEL",      os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),             ""),
    ("OPENAI_API_KEY",    "✅ Set" if os.getenv("OPENAI_API_KEY") else "❌ Not set", "required for openai"),
    ("OPENAI_BASE_URL",   os.getenv("OPENAI_BASE_URL") or "— (default)",          "optional gateway"),
    ("ANTHROPIC_API_KEY", "✅ Set" if os.getenv("ANTHROPIC_API_KEY") else "❌ Not set", "required for anthropic"),
    ("ANTHROPIC_BASE_URL",os.getenv("ANTHROPIC_BASE_URL") or "— (default)",       "optional gateway"),
    ("GOOGLE_API_KEY",    "✅ Set" if os.getenv("GOOGLE_API_KEY") else "❌ Not set", "required for google"),
]

hdr1, hdr2, hdr3 = st.columns([2, 3, 2])
hdr1.markdown("**Variable**")
hdr2.markdown("**Value**")
hdr3.markdown("**Notes**")
st.markdown("---")

for var, val, note in rows:
    c1, c2, c3 = st.columns([2, 3, 2])
    c1.markdown(f"`{var}`")
    c2.markdown(val)
    c3.markdown(f"*{note}*" if note else "")
