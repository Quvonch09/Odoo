from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    size: int
    total: int


class EnvelopeResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    timestamp: datetime
    data: T
    pagination: PaginationMeta | None = None


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=200)
