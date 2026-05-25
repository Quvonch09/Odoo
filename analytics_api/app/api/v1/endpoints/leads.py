from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_lead_service, require_roles
from app.models.security import RoleEnum
from app.schemas.common import EnvelopeResponse, PaginationParams
from app.schemas.lead import LeadFilter, LeadListItem
from app.services.lead_service import LeadService

router = APIRouter(dependencies=[Depends(require_roles(RoleEnum.ADMIN, RoleEnum.ANALYST, RoleEnum.READ_ONLY))])


@router.get("", response_model=EnvelopeResponse[list[LeadListItem]])
async def list_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None),
    stage: str | None = Query(None),
    salesperson_id: int | None = Query(None),
    sort_by: str = Query("create_date"),
    sort_order: str = Query("desc"),
    service: LeadService = Depends(get_lead_service),
):
    return await service.list_leads(
        PaginationParams(page=page, size=size),
        LeadFilter(
            search=search,
            stage=stage,
            salesperson_id=salesperson_id,
            sort_by=sort_by,
            sort_order=sort_order,
        ),
    )
