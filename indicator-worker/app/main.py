"""TradeMind Worker Template v1.0 - FastAPI application entrypoint."""

import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import router
from app.config.settings import get_settings
from app.core import worker_state

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="TradeMind Worker Template",
        version=settings.version,
        description="TradeMind distributed worker template (indicator-worker instance)",
    )
    app.include_router(router)
    Instrumentator().instrument(app).expose(app)
    return app


app = create_app()


@app.on_event("startup")
def startup():
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    worker_state.mark_ready()
    logger.info(
        "Starting %s v%s (worker=%s, node=%s, role=%s)",
        settings.service_name,
        settings.version,
        settings.worker_id,
        settings.node_name,
        settings.node_role,
    )


@app.on_event("shutdown")
def shutdown():
    worker_state.mark_not_ready()
    logger.info("Worker shutdown complete")
