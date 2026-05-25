from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class ProductFilter(BaseModel):
    search: str | None = None
    active: bool | None = True
    sale_ok: bool | None = None
    sort_by: str = "name"
    sort_order: str = "asc"


class ProductListItem(BaseModel):
    id: int
    template_id: int | None
    name: str | None
    default_code: str | None
    active: bool | None
    sale_ok: bool | None
    type: str | None
    list_price: Decimal | None
