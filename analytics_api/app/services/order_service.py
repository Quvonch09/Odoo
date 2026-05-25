from __future__ import annotations

from app.core.responses import success_response
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.common import PaginationParams
from app.schemas.order import OrderFilter, OrderListItem


class OrderService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    async def list_orders(self, pagination: PaginationParams, filters: OrderFilter):
        rows, total = await self.repository.list_orders(pagination.page, pagination.size, filters)
        data = [
            OrderListItem(
                id=row.id,
                name=row.name,
                partner_id=row.partner_id,
                partner_name=row.partner.name if row.partner else None,
                user_id=row.user_id,
                state=row.state,
                amount_total=row.amount_total,
                date_order=row.date_order,
            ).model_dump()
            for row in rows
        ]
        return success_response(
            message="Data fetched successfully",
            data=data,
            pagination={"page": pagination.page, "size": pagination.size, "total": total},
        )
