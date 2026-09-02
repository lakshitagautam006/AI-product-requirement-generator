import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
import groq

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
CHROMA_PERSIST_DIR = PROJECT_ROOT / ".chroma_db"

# Load .env file if present
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

# Standard fallback models list for chat completion on Groq
FALLBACK_GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "deepseek-r1-distill-llama-70b",
    "gemma2-9b-it"
]
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_groq_api_key(override_key: Optional[str] = None) -> str:
    """
    Retrieve Groq API key securely with deployment-safe precedence:
    1. Direct override argument (if provided and valid)
    2. Streamlit Secrets (st.secrets["GROQ_API_KEY"]) when deployed on Streamlit Community Cloud
    3. Local .env file or system environment variable (os.getenv("GROQ_API_KEY"))
    """
    # 1. Check direct override parameter
    if override_key and override_key.strip():
        val = override_key.strip()
        return "" if val == "your_groq_api_key_here" else val

    # 2. Check Streamlit secrets (for Streamlit Community Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            # Direct key in secrets
            if "GROQ_API_KEY" in st.secrets:
                val = str(st.secrets["GROQ_API_KEY"]).strip()
                if val and val != "your_groq_api_key_here":
                    return val

            # Also check common nested sections (e.g., [general] or [groq])
            for section in ["general", "groq"]:
                if section in st.secrets:
                    sec_obj = st.secrets[section]
                    if hasattr(sec_obj, "get"):
                        sec_val = str(sec_obj.get("GROQ_API_KEY", "") or sec_obj.get("api_key", "")).strip()
                        if sec_val and sec_val != "your_groq_api_key_here":
                            return sec_val
    except Exception:
        # Ignore when secrets.toml is not present (e.g. during local runs or non-streamlit CLI scripts)
        pass

    # 3. Reload and check local .env / environment variables
    try:
        load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
    except Exception:
        pass

    val = os.getenv("GROQ_API_KEY", "").strip()
    return "" if val == "your_groq_api_key_here" else val


def get_api_key_source() -> str:
    """
    Identify the source of the active API key for deployment observability:
    Returns 'Streamlit Secrets', '.env', or '' (if key not configured).
    """
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "GROQ_API_KEY" in st.secrets:
                val = str(st.secrets["GROQ_API_KEY"]).strip()
                if val and val != "your_groq_api_key_here":
                    return "Streamlit Secrets"
            for section in ["general", "groq"]:
                if section in st.secrets and hasattr(st.secrets[section], "get"):
                    sec_val = str(st.secrets[section].get("GROQ_API_KEY", "") or st.secrets[section].get("api_key", "")).strip()
                    if sec_val and sec_val != "your_groq_api_key_here":
                        return "Streamlit Secrets"
    except Exception:
        pass

    val = os.getenv("GROQ_API_KEY", "").strip()
    if val and val != "your_groq_api_key_here":
        return ".env"

    return ""


def get_available_groq_models(api_key: Optional[str] = None) -> List[str]:
    """
    Query the Groq API dynamically to verify models actually available to this specific key/project.
    Filters out audio, whisper, vision, and guardrail models to retain chat completion models.
    Falls back to verified standard models if the API key is not yet set or query fails.
    """
    key = get_groq_api_key(api_key)
    if not key:
        return FALLBACK_GROQ_MODELS

    try:
        client = groq.Groq(api_key=key)
        model_list = client.models.list()
        
        valid_models = []
        for m in model_list.data:
            model_id = getattr(m, "id", "")
            is_active = getattr(m, "active", True)
            
            if not is_active:
                continue
            
            # Exclude non-text/chat models
            lower_id = model_id.lower()
            if any(excluded in lower_id for excluded in ["whisper", "audio", "guard", "vision", "embed", "tts", "stt", "distil-whisper"]):
                continue
            
            valid_models.append(model_id)

        if valid_models:
            # Preferred priority order for flagship PRD reasoning
            preferred_order = [
                "llama-3.3-70b-versatile",
                "openai/gpt-oss-120b",
                "qwen/qwen3.6-27b",
                "llama-3.1-8b-instant",
                "openai/gpt-oss-20b",
                "deepseek-r1-distill-llama-70b",
                "gemma2-9b-it"
            ]
            
            def sort_rank(m_name: str) -> int:
                try:
                    return preferred_order.index(m_name)
                except ValueError:
                    return 999

            sorted_models = sorted(valid_models, key=sort_rank)
            return sorted_models

    except Exception as e:
        print(f"Notice: Could not fetch dynamic model list from Groq API ({e}). Using standard models.")

    return FALLBACK_GROQ_MODELS


def get_default_model(api_key: Optional[str] = None) -> str:
    """Return the optimal verified model available for the key."""
    models = get_available_groq_models(api_key)
    return models[0] if models else DEFAULT_GROQ_MODEL
