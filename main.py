from infrastructure.logging.setup import configure_logging


def main() -> None:
    """Application entry point."""
    configure_logging()
    print("Reps backend scaffold is ready. See docs/api/auth.md for API contract.")


if __name__ == "__main__":
    main()
