"""Main FastAPI application for ISR Platform."""

import logging
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import get_settings

from .routers import alerts, analytics, auth, dashboard, entities, events, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting ISR Platform API...")
    yield
    # Shutdown
    logger.info("Shutting down ISR Platform API...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Military-Grade ISR Simulation & Analysis Platform API",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Register routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"])
    app.include_router(
        entities.router, prefix=f"{settings.api_prefix}/entities", tags=["Entities"]
    )
    app.include_router(events.router, prefix=f"{settings.api_prefix}/events", tags=["Events"])
    app.include_router(alerts.router, prefix=f"{settings.api_prefix}/alerts", tags=["Alerts"])
    app.include_router(
        analytics.router, prefix=f"{settings.api_prefix}/analytics", tags=["Analytics"]
    )
    app.include_router(
        dashboard.router, prefix=f"{settings.api_prefix}/dashboard", tags=["Dashboard"]
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "ISR-5000",
                    "message": "Internal server error",
                    "trace_id": getattr(request.state, "request_id", None),
                }
            },
        )

    return app


# Create the application instance
app = create_app()


def main() -> None:
    """Run the application."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
