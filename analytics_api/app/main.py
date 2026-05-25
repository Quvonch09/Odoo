from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import add_exception_handlers
from app.core.limiter import limiter
from app.core.logging import configure_logging, get_logger
from app.db.session import close_db, ping_database
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.auth_service import bootstrap_admin_user

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("startup", env=settings.app_env, version=settings.app_version)
    await ping_database()
    await bootstrap_admin_user()
    yield
    await close_db()
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
        docs_url="/docs" if settings.swagger_enabled else None,
        redoc_url="/redoc" if settings.swagger_enabled else None,
        openapi_url="/openapi.json" if settings.swagger_enabled else None,
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    add_exception_handlers(app)

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    if settings.enable_metrics:
        Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app, endpoint="/metrics")

    return app


app = create_app()
