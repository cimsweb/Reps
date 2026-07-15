from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt_template(name: str) -> str:
    """Load a prompt template file from infrastructure/ai/prompts/."""
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8")


def render_prompt_template(name: str, **context: str) -> str:
    """Load and format a prompt template with simple str.format placeholders."""
    template = load_prompt_template(name)
    return template.format(**context)
