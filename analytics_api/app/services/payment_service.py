from __future__ import annotations

from app.core.responses import success_response
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.common import PaginationParams
from app.schemas.payment import PaymentFilter, PaymentListItem


class PaymentService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    async def list_payments(self, pagination: PaginationParams, filters: PaymentFilter):
        rows, total = await self.repository.list_payments(pagination.page, pagination.size, filters)
        data = [
            PaymentListItem(
                id=row.id,
                move_id=row.move_id,
                partner_id=row.partner_id,
                product_id=row.product_id,
                payment_date=row.date,
                debit=row.debit,
                credit=row.credit,
                balance=row.balance,
                description=row.name,
            ).model_dump()
            for row in rows
        ]
        return success_response(
            message="Data fetched successfully",
            data=data,
            pagination={"page": pagination.page, "size": pagination.size, "total": total},
        )
