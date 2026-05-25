from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_dashboard_service, require_roles
from app.models.security import RoleEnum
from app.schemas.common import EnvelopeResponse
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(dependencies=[Depends(require_roles(RoleEnum.ADMIN, RoleEnum.ANALYST, RoleEnum.READ_ONLY))])


@router.get("", response_model=EnvelopeResponse[DashboardResponse])
async def get_dashboard(
    year: int | None = Query(None, ge=2000),
    month: int | None = Query(None, ge=1, le=12),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_dashboard(year=year, month=month)
