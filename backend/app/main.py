from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .monitoring.logging import configure_logging
from .routes import concepts, graph, learning_path, search, upload


def create_app() -> FastAPI:
    configure_logging()
    init_db()

    app = FastAPI(
        title="Knowledge Vault API",
        description="Local-first API for document ingestion and concept graph exploration.",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.env,
            "database": str(settings.database_url),
        }

    app.include_router(upload.router)
    app.include_router(concepts.router)
    app.include_router(graph.router)
    app.include_router(search.router)
    app.include_router(learning_path.router)
    return app


app = create_app()

