from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OrderFilter(BaseModel):
    partner_id: int | None = None
    state: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    sort_by: str = "date_order"
    sort_order: str = "desc"


class OrderListItem(BaseModel):
    id: int
    name: str | None
    partner_id: int | None
    partner_name: str | None
    user_id: int | None
    state: str | None
    amount_total: Decimal | None
    date_order: datetime | None
