from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_customer_service, require_roles
from app.models.security import RoleEnum
from app.schemas.common import EnvelopeResponse, PaginationParams
from app.schemas.customer import CustomerDetailSchema, CustomerFilter, CustomerListItem
from app.services.customer_service import CustomerService

router = APIRouter(dependencies=[Depends(require_roles(RoleEnum.ADMIN, RoleEnum.ANALYST, RoleEnum.READ_ONLY))])


@router.get("", response_model=EnvelopeResponse[list[CustomerListItem]])
async def list_customers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None),
    country: str | None = Query(None),
    is_company: bool | None = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    service: CustomerService = Depends(get_customer_service),
):
    return await service.list_customers(
        pagination=PaginationParams(page=page, size=size),
        filters=CustomerFilter(
            search=search,
            country=country,
            is_company=is_company,
            sort_by=sort_by,
            sort_order=sort_order,
        ),
    )


@router.get("/{customer_id}", response_model=EnvelopeResponse[CustomerDetailSchema])
async def get_customer(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
):
    return await service.get_customer(customer_id)
