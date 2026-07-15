import os

from domain.services.agent_session_rules import AI_CALL_TIMEOUT_SECONDS


def load_ai_api_key() -> str | None:
    value = os.getenv("AI_API_KEY", "").strip()
    return value or None


def load_ai_use_stub() -> bool:
    value = os.getenv("AI_USE_STUB", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def load_ai_base_url() -> str:
    return os.getenv("AI_BASE_URL", "https://api.openai.com/v1").strip()


def load_ai_model() -> str:
    return os.getenv("AI_MODEL", "gpt-4o-mini").strip()


def load_ai_timeout_seconds() -> int:
    raw = os.getenv("AI_TIMEOUT_SECONDS", str(AI_CALL_TIMEOUT_SECONDS)).strip()
    return int(raw)
