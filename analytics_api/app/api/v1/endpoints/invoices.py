from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_invoice_service, require_roles
from app.models.security import RoleEnum
from app.schemas.common import EnvelopeResponse, PaginationParams
from app.schemas.invoice import InvoiceFilter, InvoiceListItem
from app.services.invoice_service import InvoiceService

router = APIRouter(dependencies=[Depends(require_roles(RoleEnum.ADMIN, RoleEnum.ANALYST, RoleEnum.READ_ONLY))])


@router.get("", response_model=EnvelopeResponse[list[InvoiceListItem]])
async def list_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    partner_id: int | None = Query(None),
    payment_state: str | None = Query(None),
    move_type: str | None = Query("out_invoice"),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    sort_by: str = Query("invoice_date"),
    sort_order: str = Query("desc"),
    service: InvoiceService = Depends(get_invoice_service),
):
    return await service.list_invoices(
        PaginationParams(page=page, size=size),
        InvoiceFilter(
            partner_id=partner_id,
            payment_state=payment_state,
            move_type=move_type,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        ),
    )
