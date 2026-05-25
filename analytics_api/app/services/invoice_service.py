from __future__ import annotations

from app.core.responses import success_response
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.common import PaginationParams
from app.schemas.invoice import InvoiceFilter, InvoiceListItem


class InvoiceService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    async def list_invoices(self, pagination: PaginationParams, filters: InvoiceFilter):
        rows, total = await self.repository.list_invoices(pagination.page, pagination.size, filters)
        data = [
            InvoiceListItem(
                id=row.id,
                name=row.name,
                partner_id=row.partner_id,
                partner_name=row.partner.name if row.partner else None,
                invoice_date=row.invoice_date,
                invoice_date_due=row.invoice_date_due,
                state=row.state,
                payment_state=row.payment_state,
                amount_total=row.amount_total,
                amount_residual=row.amount_residual,
            ).model_dump()
            for row in rows
        ]
        return success_response(
            message="Data fetched successfully",
            data=data,
            pagination={"page": pagination.page, "size": pagination.size, "total": total},
        )
