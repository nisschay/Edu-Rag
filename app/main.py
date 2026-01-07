"""
FastAPI application entry point.

This module:
- Creates and configures the FastAPI application
- Registers middleware
- Includes API routers
- Sets up event handlers
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, users, subjects, units, topics, files, rag
from app.api.routes import summaries, chat
from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.base import Base
from app.db.session import engine

# Import models to ensure they are registered with SQLAlchemy
from app.models import User, Subject, Unit, Topic, File, Chunk, TopicSummary, UnitSummary  # noqa: F401

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Create database tables, initialize connections
    - Shutdown: Clean up resources
    """
    settings = get_settings()
    
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode")
    
    # Create database tables (development only)
    # In production, use Alembic migrations
    if settings.is_development:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


def create_application() -> FastAPI:
    """
    Application factory function.
    
    Creates and configures the FastAPI application with:
    - Metadata configuration
    - CORS middleware
    - Route registration
    
    Returns:
        FastAPI: Configured application instance.
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="College-level educational AI system with RAG-based retrieval",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # Configure CORS
    # In production, restrict origins appropriately
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    app.include_router(
        health.router,
        prefix=settings.API_V1_PREFIX,
    )
    app.include_router(
        users.router,
        prefix=settings.API_V1_PREFIX,
    )
    app.include_router(
        subjects.router,
        prefix=settings.API_V1_PREFIX,
    )
    app.include_router(
        units.router,
        prefix=settings.API_V1_PREFIX,
    )
    app.include_router(
        topics.router,
        prefix=settings.API_V1_PREFIX,
    )
    app.include_router(
        files.router,
        prefix=settings.API_V1_PREFIX,
    )
    app.include_router(
        rag.router,
        prefix=settings.API_V1_PREFIX,
        tags=["RAG"],
    )
    app.include_router(
        summaries.router,
        prefix=settings.API_V1_PREFIX,
        tags=["Summaries"],
    )
    app.include_router(
        chat.router,
        prefix=settings.API_V1_PREFIX,
        tags=["Chat"],
    )
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    def root() -> dict[str, str]:
        """Root endpoint returning basic API info."""
        return {
            "name": settings.PROJECT_NAME,
            "version": "0.1.0",
            "docs": "/docs",
        }
    
    return app


# Create application instance
app = create_application()
