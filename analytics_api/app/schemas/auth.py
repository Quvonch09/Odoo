from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str


class APIKeyCreateRequest(BaseModel):
    name: str
    user_email: EmailStr
    expires_at: datetime | None = None
