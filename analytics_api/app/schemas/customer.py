from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CustomerFilter(BaseModel):
    search: str | None = None
    country: str | None = None
    is_company: bool | None = None
    sort_by: str = "name"
    sort_order: str = "asc"


class CustomerListItem(BaseModel):
    id: int
    name: str | None
    email: str | None
    phone: str | None
    city: str | None
    country_code: str | None
    is_company: bool | None
    active: bool | None
    create_date: datetime | None


class CustomerDetailSchema(CustomerListItem):
    customer_rank: int | None
    total_invoices: int
    total_orders: int
    total_revenue: Decimal
