from fastapi import APIRouter

from app.api.v1.endpoints import auth, customers, dashboard, health, invoices, leads, orders, payments, products

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(health.router, tags=["Health"])
router.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
router.include_router(invoices.router, prefix="/api/v1/invoices", tags=["Invoices"])
router.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
router.include_router(leads.router, prefix="/api/v1/leads", tags=["Leads"])
router.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
router.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
router.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
