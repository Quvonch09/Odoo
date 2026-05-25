from __future__ import annotations

from app.core.responses import success_response
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.common import PaginationParams
from app.schemas.product import ProductFilter, ProductListItem


class ProductService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    async def list_products(self, pagination: PaginationParams, filters: ProductFilter):
        rows, total = await self.repository.list_products(pagination.page, pagination.size, filters)
        data = [
            ProductListItem(
                id=row.id,
                template_id=row.product_tmpl_id,
                name=row.template.name if row.template else None,
                default_code=row.template.default_code if row.template else row.default_code,
                active=row.active,
                sale_ok=row.template.sale_ok if row.template else None,
                type=row.template.type if row.template else None,
                list_price=row.template.list_price if row.template else None,
            ).model_dump()
            for row in rows
        ]
        return success_response(
            message="Data fetched successfully",
            data=data,
            pagination={"page": pagination.page, "size": pagination.size, "total": total},
        )
