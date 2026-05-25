from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class TopProduct(BaseModel):
    id: int
    name: str | None
    qty: Decimal
    revenue: Decimal


class TopCustomer(BaseModel):
    id: int
    name: str | None
    revenue: Decimal


class EmployeeStat(BaseModel):
    id: int
    name: str | None
    lead_count: int
    won_count: int


class DashboardResponse(BaseModel):
    total_customers: int
    active_customers: int
    total_invoices: int
    paid_invoices: int
    unpaid_invoices: int
    total_revenue: Decimal
    monthly_revenue: Decimal
    yearly_revenue: Decimal
    total_leads: int
    won_leads: int
    lost_leads: int
    conversion_rate: float
    top_products: list[TopProduct]
    top_customers: list[TopCustomer]
    employee_statistics: list[EmployeeStat]
