from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class LeadFilter(BaseModel):
    search: str | None = None
    stage: str | None = None
    salesperson_id: int | None = None
    sort_by: str = "create_date"
    sort_order: str = "desc"


class LeadListItem(BaseModel):
    id: int
    name: str | None
    partner_name: str | None
    email_from: str | None
    phone: str | None
    user_id: int | None
    expected_revenue: Decimal | None
    probability: Decimal | None
    active: bool | None
    create_date: datetime | None
