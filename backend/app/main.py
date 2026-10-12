from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.models.database import init_db, SessionLocal
from app.services.operator_catalog import seed_operator_catalog
from app.api.endpoints import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    init_db()
    # Seed default PyTorch operator catalog
    db = SessionLocal()
    try:
        seed_operator_catalog(db)
    finally:
        db.close()
    yield

def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        description="Orbit Station: dynamic neural networks and tensor execution backend evaluation platform",
        version="1.0.0",
        lifespan=lifespan
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/api/health")
    def health_check():
        return {
            "status": "healthy",
            "environment": settings.environment,
            "demo_mode": settings.demo_mode,
            "version": "1.0.0"
        }

    application.include_router(api_router, prefix="/api")

    # Ensure tables are initialized on app creation
    init_db()
    db = SessionLocal()
    try:
        seed_operator_catalog(db)
    finally:
        db.close()

    return application

app = create_app()
