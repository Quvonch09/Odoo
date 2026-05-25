from __future__ import annotations

from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.security import AuthContext
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import AuthService

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        request.state.auth_context = None

        async with SessionLocal() as session:
            service = AuthService(AuthRepository(session))
            request.state.auth_context = await service.authenticate_request(request)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info("request", path=request.url.path, method=request.method, request_id=request_id)
        return response
