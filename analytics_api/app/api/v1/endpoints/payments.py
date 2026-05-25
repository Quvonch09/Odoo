from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_payment_service, require_roles
from app.models.security import RoleEnum
from app.schemas.common import EnvelopeResponse, PaginationParams
from app.schemas.payment import PaymentFilter, PaymentListItem
from app.services.payment_service import PaymentService

router = APIRouter(dependencies=[Depends(require_roles(RoleEnum.ADMIN, RoleEnum.ANALYST, RoleEnum.READ_ONLY))])


@router.get("", response_model=EnvelopeResponse[list[PaymentListItem]])
async def list_payments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    partner_id: int | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    sort_by: str = Query("payment_date"),
    sort_order: str = Query("desc"),
    service: PaymentService = Depends(get_payment_service),
):
    return await service.list_payments(
        PaginationParams(page=page, size=size),
        PaymentFilter(
            partner_id=partner_id,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        ),
    )
