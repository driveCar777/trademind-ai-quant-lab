"""TradeMind Master API v1.2 - FastAPI application entrypoint."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.routes import router
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="TradeMind Master API",
        version=settings.version,
        description="TradeMind Master REST API (v1.3)",
    )
    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()


@app.on_event("startup")
def startup():
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    settings.tasks_path.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Starting %s v%s on %s:%s",
        settings.service_name,
        settings.version,
        settings.host,
        settings.port,
    )