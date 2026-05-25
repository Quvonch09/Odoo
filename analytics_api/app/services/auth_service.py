from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from jose import JWTError

from app.core.config import get_settings
from app.core.responses import success_response
from app.core.security import (
    api_key_prefix,
    create_access_token,
    decode_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
)
from app.db.session import SessionLocal
from app.models.security import AnalyticsAPIKey, AnalyticsUser, AuthContext, RoleEnum
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import APIKeyCreateRequest, LoginRequest

settings = get_settings()


class AuthService:
    def __init__(self, repository: AuthRepository):
        self.repository = repository

    async def login(self, payload: LoginRequest):
        user = await self.repository.get_user_by_email(payload.email)
        if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_access_token(subject=str(user.id), role=user.role)
        return success_response(
            message="Login successful",
            data={
                "access_token": token,
                "token_type": "bearer",
                "expires_in": settings.jwt_access_token_expire_minutes * 60,
                "role": user.role,
            },
        )

    async def create_api_key(self, payload: APIKeyCreateRequest):
        user = await self.repository.get_user_by_email(payload.user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        raw_key = generate_api_key()
        entity = AnalyticsAPIKey(
            user_id=user.id,
            name=payload.name,
            key_prefix=api_key_prefix(raw_key),
            key_hash=hash_api_key(raw_key),
            expires_at=payload.expires_at,
        )
        await self.repository.create_api_key(entity)
        return success_response(
            message="API key created successfully",
            data={"api_key": raw_key, "key_prefix": entity.key_prefix, "name": entity.name},
        )

    async def authenticate_request(self, request: Request) -> AuthContext | None:
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi") or request.url.path.startswith("/health"):
            return None
        auth_header = request.headers.get("Authorization")
        api_key = request.headers.get("X-API-Key")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = decode_token(token)
                user = await self.repository.get_user_by_id(int(payload["sub"]))
                if not user or not user.is_active:
                    raise HTTPException(status_code=401, detail="Inactive user")
                return AuthContext(user_id=user.id, email=user.email, role=RoleEnum(user.role), auth_type="jwt")
            except (JWTError, ValueError):
                raise HTTPException(status_code=401, detail="Invalid token")
        if api_key:
            entity = await self.repository.get_api_key(hash_api_key(api_key))
            if not entity or not entity.is_active:
                raise HTTPException(status_code=401, detail="Invalid API key")
            if entity.expires_at and entity.expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail="Expired API key")
            user = await self.repository.get_user_by_id(entity.user_id)
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="Inactive user")
            await self.repository.touch_api_key(entity)
            return AuthContext(user_id=user.id, email=user.email, role=RoleEnum(user.role), auth_type="api_key")
        if request.url.path.startswith("/api/") or request.url.path.startswith("/auth/api-keys"):
            raise HTTPException(status_code=401, detail="Authentication required")
        return None


async def bootstrap_admin_user() -> None:
    async with SessionLocal() as session:
        repository = AuthRepository(session)
        existing = await repository.get_user_by_email(settings.admin_email)
        if existing:
            return
        user = AnalyticsUser(
            email=settings.admin_email,
            full_name=settings.admin_full_name,
            password_hash=hash_password(settings.admin_password),
            role=RoleEnum.ADMIN.value,
            is_active=True,
        )
        await repository.create_user(user)
