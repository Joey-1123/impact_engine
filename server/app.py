from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server import __version__
from server.routers import health, overview, graph, health_score, costs, decisions, workspace, impact, webhook

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Impact Engine server starting")
    yield
    logger.info("Impact Engine server shutting down")


def create_app(repo_path: str | None = None) -> FastAPI:
    app = FastAPI(
        title="Impact Engine",
        version=__version__,
        lifespan=lifespan,
    )

    app.state.repo_path = repo_path

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(overview.router)
    app.include_router(graph.router)
    app.include_router(health_score.router)
    app.include_router(costs.router)
    app.include_router(decisions.router)
    app.include_router(workspace.router)
    app.include_router(impact.router)
    app.include_router(webhook.router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app
