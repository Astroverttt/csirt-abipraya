"""
PatchOps Backend — FastAPI Application Entry Point.

Production-ready backend for Wazuh Patch Management dashboard.
All Wazuh/Indexer credentials stay server-side.
"""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers.agents import router as agents_router
from .routers.auth import router as auth_router
from .routers.indexer import router as indexer_router
from .routers.nvd import router as nvd_router
from .routers.packages import router as packages_router
from .routers.playbooks import router as playbooks_router
from .routers.tickets import router as tickets_router
from .routers.vulnerabilities import router as vulnerabilities_router

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("patchops")

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="PatchOps API",
    description="Backend API for Wazuh Patch Management Dashboard",
    version="1.0.0",
    docs_url="/api/docs" if settings.APP_DEBUG else None,
    redoc_url="/api/redoc" if settings.APP_DEBUG else None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(vulnerabilities_router)
app.include_router(packages_router)
app.include_router(indexer_router)
app.include_router(tickets_router)
app.include_router(playbooks_router)
app.include_router(nvd_router)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "PatchOps Backend",
        "version": "1.0.0",
    }


# ── Startup event ─────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    logger.info("PatchOps Backend starting...")
    logger.info("Environment: %s", settings.APP_ENV)
    logger.info("Wazuh API: %s", settings.WAZUH_API_URL)
    logger.info("Indexer: %s", settings.INDEXER_URL)
    logger.info("Database URL: %s", settings.DATABASE_URL)
    logger.info("CORS origins: %s", settings.cors_origin_list)

    # Initialize Database Tables
    try:
        from .db.database import engine, Base
        from .db import models # noqa Ensure models are imported
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error("Error connecting to database: %s", e)
        raise e

    # Seed default playbooks
    from .storage import playbooks as pb_store
    try:
        pb_store.seed_defaults()
        logger.info("Ensured default playbooks are seeded.")
    except Exception as e:
        logger.error("Error seeding default playbooks: %s", e)

    logger.info("Backend ready.")
