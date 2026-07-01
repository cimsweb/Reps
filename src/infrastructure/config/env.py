from pathlib import Path

from dotenv import load_dotenv


def load_environment() -> None:
    """Load variables from the project .env file when present."""
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env", override=False)
