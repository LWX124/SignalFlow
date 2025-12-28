"""SignalFlow Backend Application Entry Point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import configure_logging, get_logger
from src.infra.database import init_db, close_db
from src.api.v1 import router as api_v1_router
from src.api.exceptions import register_exception_handlers
from src.api.middleware import register_middleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    configure_logging(settings.log_level, settings.log_format)
    logger.info("Starting SignalFlow Backend", env=settings.app_env)

    await init_db()

    yield

    # Shutdown
    await close_db()
    logger.info("SignalFlow Backend shutdown complete")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Stock Strategy Subscription Platform API",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    register_middleware(app)

    # Exception handlers
    register_exception_handlers(app)

    # Routes
    app.include_router(api_v1_router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )
