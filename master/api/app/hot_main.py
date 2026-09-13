"""Standalone Master process for the hot desk on :9001. Not used by :9000."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.hot_routes import router

logger = logging.getLogger(__name__)

app = FastAPI(title="TradeMind Hot Desk", version="0.1.0")
register_exception_handlers(app)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/health")
def health():
    from app.service import cursor_cloud as cc
    return {
        "status": "healthy",
        "service": "trademind-hot-desk",
        "version": "0.1.0",
        "cursor_key": cc.key_present(),
    }


@app.on_event("startup")
def startup():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    logger.info("Hot desk on :9001 — frozen paper stays on :9000")
