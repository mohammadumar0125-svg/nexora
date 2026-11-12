import logging
import os

from app.api import (
    auth_enterprise,
    commerce,
    crm,
    intelligence_automation,
    public,
    team_enterprise,
    workspace_bi,
)
from app.core.config import settings
from app.core.database import SessionLocal
from app.seed_enterprise import seed_sample_workspace
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("nexora")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="NEXORA Enterprise Business Operating System — CRM, Orders, Inventory, Analytics, Tasks, AI & Automation.",
    docs_url="/api/docs" if settings.APP_ENV != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Authorization"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    if settings.APP_ENV in ("staging", "production"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.on_event("startup")
def on_startup():
    if not settings.SEED_SAMPLE_WORKSPACE:
        return
    try:
        seed_sample_workspace()
        logger.info("PostgreSQL sample evaluation workspace verified cleanly.")
    except Exception as exc:
        logger.warning("Startup seed check skipped/failed (run setup_postgres.py if fresh): %s", exc)


app.include_router(public.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_enterprise.router, prefix=settings.API_V1_PREFIX)
app.include_router(team_enterprise.router, prefix=settings.API_V1_PREFIX)
app.include_router(crm.router, prefix=settings.API_V1_PREFIX)
app.include_router(commerce.router, prefix=settings.API_V1_PREFIX)
app.include_router(workspace_bi.router, prefix=settings.API_V1_PREFIX)
app.include_router(intelligence_automation.router, prefix=settings.API_V1_PREFIX)


@app.get("/api/health")
def health_check():
    db_status = "disconnected"
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            db_status = "postgresql_connected"
    except Exception as exc:
        logger.error("Health check DB error: %s", exc)
    return {
        "status": "healthy" if db_status == "postgresql_connected" else "degraded",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "database": db_status,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
    }


frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_root():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API endpoint not found.")
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend bundle not built.")
