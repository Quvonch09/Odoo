from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session, get_rw_session
from app.models.security import AuthContext, RoleEnum
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.dashboard_service import DashboardService
from app.services.invoice_service import InvoiceService
from app.services.lead_service import LeadService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.product_service import ProductService


async def get_current_auth_context(request: Request) -> AuthContext:
    context = getattr(request.state, "auth_context", None)
    if context is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return context


def require_roles(*roles: RoleEnum) -> Callable:
    async def dependency(auth: AuthContext = Depends(get_current_auth_context)) -> AuthContext:
        if auth.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return auth

    return dependency


def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(AuthRepository(session))


def get_auth_write_service(session: AsyncSession = Depends(get_rw_session)) -> AuthService:
    return AuthService(AuthRepository(session))


def get_customer_service(session: AsyncSession = Depends(get_db_session)) -> CustomerService:
    return CustomerService(AnalyticsRepository(session))


def get_invoice_service(session: AsyncSession = Depends(get_db_session)) -> InvoiceService:
    return InvoiceService(AnalyticsRepository(session))


def get_payment_service(session: AsyncSession = Depends(get_db_session)) -> PaymentService:
    return PaymentService(AnalyticsRepository(session))


def get_lead_service(session: AsyncSession = Depends(get_db_session)) -> LeadService:
    return LeadService(AnalyticsRepository(session))


def get_product_service(session: AsyncSession = Depends(get_db_session)) -> ProductService:
    return ProductService(AnalyticsRepository(session))


def get_order_service(session: AsyncSession = Depends(get_db_session)) -> OrderService:
    return OrderService(AnalyticsRepository(session))


def get_dashboard_service(session: AsyncSession = Depends(get_db_session)) -> DashboardService:
    return DashboardService(AnalyticsRepository(session))
