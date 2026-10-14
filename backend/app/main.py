import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware
from app.database import Base, engine, SessionLocal
import app.models  # Ensure all models are registered with Base metadata
from app.models.job import Job
from app.api.v1 import (
    health,
    audit,
    auth,
    videos,
    jobs,
    evidence,
    rules,
    events,
    venue,
    routes,
    incidents,
    resources,
    analytics,
    reports
)
from app.services.crowd_rules_engine import seed_default_rules
from app.services.venue_service import VenueService
from app.services.resource_service import ResourceService

logger = logging.getLogger("nexora.app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise database tables on startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_rules(db)
        VenueService.seed_default_venue(db)
        ResourceService.seed_default_resources(db)

        # Stage 6 Reliability: Sweep and recover any jobs interrupted by previous abrupt restart
        interrupted_jobs = db.query(Job).filter(Job.status.in_(["processing", "queued"])).all()
        for j in interrupted_jobs:
            j.status = "failed"
            j.error_message = "Processing interrupted by application restart. Re-submission required."
            j.completed_at = datetime.now(timezone.utc)
        if interrupted_jobs:
            db.commit()
            logger.warning("Recovered %d interrupted background jobs upon application startup.", len(interrupted_jobs))
    finally:
        db.close()
    yield
    # Cleanup on shutdown if needed

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="NEXORA — AI-Powered Crowd Safety Intelligence and Emergency Response Coordination API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Apply Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS configuration
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Safe Global Exception Handler preventing path and stack trace disclosure
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal operational error occurred. The incident has been recorded."}
    )

# Register API v1 Routers
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(audit.router, prefix=settings.API_V1_PREFIX)
app.include_router(videos.router, prefix=settings.API_V1_PREFIX)
app.include_router(jobs.router, prefix=settings.API_V1_PREFIX)
app.include_router(evidence.router, prefix=settings.API_V1_PREFIX)
app.include_router(rules.router, prefix=settings.API_V1_PREFIX)
app.include_router(events.router, prefix=settings.API_V1_PREFIX)
app.include_router(venue.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(incidents.router, prefix=settings.API_V1_PREFIX)
app.include_router(resources.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }
