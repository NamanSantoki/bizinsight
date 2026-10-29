import os
import uuid
import time
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.api.router import router as api_router
from backend.app.api.data_source_router import router as data_source_router
from backend.app.api.auth_router import router as auth_router
from backend.app.api.ml_router import router as ml_router
from backend.app.api.enterprise_router import router as enterprise_router
from backend.app.api.connectors_router import router as connectors_router
from backend.app.observability.metrics_exporter import PrometheusMetricsMiddleware, get_prometheus_metrics_payload
from backend.app.observability.probes import health_probes
from backend.app.models.all_models import User
from backend.app.security.auth import get_password_hash

# Configure production-ready structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("bizinsight.app")

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

# Seed default admin and analyst users with secure defaults if not present
def seed_initial_users():
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin = User(
                username="admin",
                email="admin@bizinsight.local",
                hashed_password=get_password_hash("AdminPass2026!"),
                role="admin"
            )
            db.add(admin)

        analyst_user = db.query(User).filter(User.username == "analyst").first()
        if not analyst_user:
            analyst = User(
                username="analyst",
                email="analyst@bizinsight.local",
                hashed_password=get_password_hash("AnalystPass2026!"),
                role="analyst"
            )
            db.add(analyst)

        db.commit()
    except Exception as e:
        logger.error(f"User seed error: {e}")
    finally:
        db.close()

seed_initial_users()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Business Intelligence, Predictive Analytics & Cryptographically Audited Platform",
    version="1.0.0"
)

# Correlation ID and Request Timing Middleware
@app.middleware("http")
async def correlation_id_and_timing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{process_time}ms"
    return response

# Standard Compliant CORS Middleware
app.add_middleware(PrometheusMetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms"]
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"HTTP {exc.status_code} at {request.url.path} (request_id={request_id}): {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": request_id},
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled Server Exception at {request.url.path} (request_id={request_id}): {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please verify your dataset input parameters.",
            "request_id": request_id
        }
    )

@app.get("/")
def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/health")
@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    """Enterprise Health & Readiness Probe."""
    return health_probes.readiness()

@app.get("/health/live")
@app.get(f"{settings.API_V1_STR}/health/live")
def health_live():
    return health_probes.liveness()

@app.get("/health/ready")
@app.get(f"{settings.API_V1_STR}/health/ready")
def health_ready():
    return health_probes.readiness()

@app.get("/health/database")
@app.get(f"{settings.API_V1_STR}/health/database")
def health_db():
    return health_probes.database_check()

@app.get("/health/ml")
@app.get(f"{settings.API_V1_STR}/health/ml")
def health_ml():
    return health_probes.ml_service_check()

@app.get("/health/queue")
@app.get(f"{settings.API_V1_STR}/health/queue")
def health_queue():
    return health_probes.queue_check()

@app.get("/metrics", summary="Prometheus exposition metrics endpoint")
def metrics():
    return get_prometheus_metrics_payload()

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(data_source_router, prefix=settings.API_V1_STR)
app.include_router(ml_router, prefix=settings.API_V1_STR)
app.include_router(enterprise_router, prefix=settings.API_V1_STR)
app.include_router(connectors_router, prefix=settings.API_V1_STR)
