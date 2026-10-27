import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.api.router import router as api_router
from backend.app.models.all_models import User
from backend.app.security.auth import get_password_hash

# Create tables automatically on startup
Base.metadata.create_all(bind=engine)

# Seed default admin and analyst users if not present
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
        print(f"User seed error: {e}")
    finally:
        db.close()

seed_initial_users()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-Grade Business Intelligence, Predictive Analytics & Safe Natural-Language Data Platform",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler to prevent exposing raw stack traces
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log detailed error server-side
    print(f"Unhandled Server Error at {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please verify your dataset input parameters."}
    )

@app.get("/")
def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": "/docs"
    }

app.include_router(api_router, prefix=settings.API_V1_STR)
