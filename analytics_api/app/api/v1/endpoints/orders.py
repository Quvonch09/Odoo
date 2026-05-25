from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_order_service, require_roles
from app.models.security import RoleEnum
from app.schemas.common import EnvelopeResponse, PaginationParams
from app.schemas.order import OrderFilter, OrderListItem
from app.services.order_service import OrderService

router = APIRouter(dependencies=[Depends(require_roles(RoleEnum.ADMIN, RoleEnum.ANALYST, RoleEnum.READ_ONLY))])


@router.get("", response_model=EnvelopeResponse[list[OrderListItem]])
async def list_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    partner_id: int | None = Query(None),
    state: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    sort_by: str = Query("date_order"),
    sort_order: str = Query("desc"),
    service: OrderService = Depends(get_order_service),
):
    return await service.list_orders(
        PaginationParams(page=page, size=size),
        OrderFilter(
            partner_id=partner_id,
            state=state,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        ),
    )
