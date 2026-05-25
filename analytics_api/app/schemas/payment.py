from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class PaymentFilter(BaseModel):
    partner_id: int | None = None
    date_from: str | None = None
    date_to: str | None = None
    sort_by: str = "date"
    sort_order: str = "desc"


class PaymentListItem(BaseModel):
    id: int
    move_id: int | None
    partner_id: int | None
    product_id: int | None
    payment_date: date | None
    debit: Decimal | None
    credit: Decimal | None
    balance: Decimal | None
    description: str | None
