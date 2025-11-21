"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from src.config import settings
from src.api.routes import health
from src.api.middleware.logging import LoggingMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}',
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Report Scheduler API",
    description="Multi-tenant report scheduling and delivery platform",
    version="1.0.0",
    docs_url="/api-docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Logging Middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health.router, tags=["Health"])

# Phase 2: Schedule API
from src.api.routes import schedules
app.include_router(schedules.router, tags=["Schedules"])

# Future routers (to be implemented in Phase 3+)
# app.include_router(reports.router, prefix="/v1", tags=["Reports"])
# app.include_router(artifacts.router, prefix="/v1", tags=["Artifacts"])


@app.on_event("startup")
async def startup_event() -> None:
    """Application startup event handler."""
    logger.info(
        "Starting Report Scheduler API",
        extra={"environment": settings.ENVIRONMENT, "version": "1.0.0"},
    )
    
    # Start scheduler loop (Phase 2)
    if settings.ENABLE_SCHEDULER:
        from src.scheduler.scheduler_loop import start_scheduler_loop
        await start_scheduler_loop()
        logger.info("Scheduler loop started")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Application shutdown event handler."""
    logger.info("Shutting down Report Scheduler API")
    
    # Stop scheduler loop (Phase 2)
    if settings.ENABLE_SCHEDULER:
        from src.scheduler.scheduler_loop import stop_scheduler_loop
        await stop_scheduler_loop()
        logger.info("Scheduler loop stopped")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"path": request.url.path, "method": request.method},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            }
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
