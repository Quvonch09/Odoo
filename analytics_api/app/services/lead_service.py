from __future__ import annotations

from app.core.responses import success_response
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.common import PaginationParams
from app.schemas.lead import LeadFilter, LeadListItem


class LeadService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    async def list_leads(self, pagination: PaginationParams, filters: LeadFilter):
        rows, total = await self.repository.list_leads(pagination.page, pagination.size, filters)
        data = [LeadListItem.model_validate(row, from_attributes=True).model_dump() for row in rows]
        return success_response(
            message="Data fetched successfully",
            data=data,
            pagination={"page": pagination.page, "size": pagination.size, "total": total},
        )
