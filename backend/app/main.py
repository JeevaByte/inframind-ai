from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import analysis, files, health, repo_scan

logging.basicConfig(
    level=logging.DEBUG if get_settings().app_debug else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info("InfraMind AI backend started (env=%s)", settings.app_env)
    yield
    logger.info("InfraMind AI backend shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="InfraMind AI",
        description=(
            "REST API for infrastructure file analysis, security scanning, "
            "cost estimation, and compliance checking powered by AI."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(files.router)
    app.include_router(analysis.router)
    app.include_router(repo_scan.router)

    return app


app = create_app()
