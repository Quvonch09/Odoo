from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class InvoiceFilter(BaseModel):
    partner_id: int | None = None
    payment_state: str | None = None
    move_type: str = "out_invoice"
    date_from: str | None = None
    date_to: str | None = None
    sort_by: str = "invoice_date"
    sort_order: str = "desc"


class InvoiceListItem(BaseModel):
    id: int
    name: str | None
    partner_id: int | None
    partner_name: str | None
    invoice_date: date | None
    invoice_date_due: date | None
    state: str | None
    payment_state: str | None
    amount_total: Decimal | None
    amount_residual: Decimal | None
