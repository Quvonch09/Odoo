from __future__ import annotations

from fastapi import HTTPException

from app.core.responses import success_response
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.common import PaginationParams
from app.schemas.customer import CustomerDetailSchema, CustomerFilter, CustomerListItem


class CustomerService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    async def list_customers(self, pagination: PaginationParams, filters: CustomerFilter):
        rows, total = await self.repository.list_customers(pagination.page, pagination.size, filters)
        data = [CustomerListItem.model_validate(row, from_attributes=True).model_dump() for row in rows]
        return success_response(
            message="Data fetched successfully",
            data=data,
            pagination={"page": pagination.page, "size": pagination.size, "total": total},
        )

    async def get_customer(self, customer_id: int):
        result = await self.repository.get_customer(customer_id)
        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer, invoice_count, revenue, order_count = result
        schema = CustomerDetailSchema(
            **CustomerListItem.model_validate(customer, from_attributes=True).model_dump(),
            customer_rank=customer.customer_rank,
            total_invoices=invoice_count,
            total_orders=order_count,
            total_revenue=revenue,
        )
        return success_response(message="Data fetched successfully", data=schema.model_dump())
