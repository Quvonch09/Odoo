from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_product_service, require_roles
from app.models.security import RoleEnum
from app.schemas.common import EnvelopeResponse, PaginationParams
from app.schemas.product import ProductFilter, ProductListItem
from app.services.product_service import ProductService

router = APIRouter(dependencies=[Depends(require_roles(RoleEnum.ADMIN, RoleEnum.ANALYST, RoleEnum.READ_ONLY))])


@router.get("", response_model=EnvelopeResponse[list[ProductListItem]])
async def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None),
    active: bool | None = Query(True),
    sale_ok: bool | None = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    service: ProductService = Depends(get_product_service),
):
    return await service.list_products(
        PaginationParams(page=page, size=size),
        ProductFilter(
            search=search,
            active=active,
            sale_ok=sale_ok,
            sort_by=sort_by,
            sort_order=sort_order,
        ),
    )
