from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.config.env import load_environment
from interfaces.http.errors import register_exception_handlers
from interfaces.http.routes import admin, auth

load_environment()

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Reps API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(admin.router, prefix=API_PREFIX)
    return app


app = create_app()
