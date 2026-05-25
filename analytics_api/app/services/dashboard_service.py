from __future__ import annotations

from datetime import datetime

from app.core.responses import success_response
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.dashboard import DashboardResponse, EmployeeStat, TopCustomer, TopProduct
from app.services.cache_service import get_cache, set_cache


class DashboardService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    async def get_dashboard(self, year: int | None, month: int | None):
        now = datetime.utcnow()
        effective_year = year or now.year
        cache_key = f"dashboard:{effective_year}:{month or 'all'}"
        cached = await get_cache(cache_key)
        if cached:
            return success_response(message="Data fetched successfully", data=cached)

        metrics = await self.repository.dashboard_metrics(effective_year, month)
        conversion_rate = (
            round((metrics["won_leads"] / metrics["total_leads"]) * 100, 2)
            if metrics["total_leads"]
            else 0.0
        )
        payload = DashboardResponse(
            total_customers=metrics["total_customers"],
            active_customers=metrics["active_customers"],
            total_invoices=metrics["total_invoices"],
            paid_invoices=metrics["paid_invoices"],
            unpaid_invoices=metrics["unpaid_invoices"],
            total_revenue=metrics["total_revenue"],
            monthly_revenue=metrics["monthly_revenue"],
            yearly_revenue=metrics["yearly_revenue"],
            total_leads=metrics["total_leads"],
            won_leads=metrics["won_leads"],
            lost_leads=metrics["lost_leads"],
            conversion_rate=conversion_rate,
            top_products=[TopProduct(**row) for row in metrics["top_products"]],
            top_customers=[TopCustomer(**row) for row in metrics["top_customers"]],
            employee_statistics=[
                EmployeeStat(
                    id=row["id"],
                    name=row["name"],
                    lead_count=int(row["lead_count"] or 0),
                    won_count=int(row["won_count"] or 0),
                )
                for row in metrics["employee_stats"]
            ],
        ).model_dump(mode="json")
        await set_cache(cache_key, payload, ttl=300)
        return success_response(message="Data fetched successfully", data=payload)
