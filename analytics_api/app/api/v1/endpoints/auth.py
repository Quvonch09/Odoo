from fastapi import APIRouter, Depends
from starlette.requests import Request

from app.core.dependencies import get_auth_service, get_auth_write_service, require_roles
from app.core.limiter import limiter
from app.models.security import RoleEnum
from app.schemas.auth import APIKeyCreateRequest, LoginRequest, TokenResponse
from app.schemas.common import EnvelopeResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=EnvelopeResponse[TokenResponse])
@limiter.limit("20/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    del request
    return await service.login(payload)


@router.post("/api-keys", response_model=EnvelopeResponse[dict])
async def create_api_key(
    payload: APIKeyCreateRequest,
    _: object = Depends(require_roles(RoleEnum.ADMIN)),
    service: AuthService = Depends(get_auth_write_service),
):
    return await service.create_api_key(payload)
