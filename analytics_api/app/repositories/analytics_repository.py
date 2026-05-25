from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, and_, case, cast, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.odoo import (
    AccountMove,
    AccountMoveLine,
    CrmLead,
    HREmployee,
    ProductProduct,
    ProductTemplate,
    ResPartner,
    SaleOrder,
    SaleOrderLine,
)
from app.schemas.customer import CustomerFilter
from app.schemas.invoice import InvoiceFilter
from app.schemas.lead import LeadFilter
from app.schemas.order import OrderFilter
from app.schemas.payment import PaymentFilter
from app.schemas.product import ProductFilter


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_customers(self, page: int, size: int, filters: CustomerFilter):
        query = select(ResPartner).where(ResPartner.customer_rank > 0)
        if filters.search:
            like = f"%{filters.search.lower()}%"
            query = query.where(
                or_(
                    func.lower(ResPartner.name).like(like),
                    func.lower(ResPartner.email).like(like),
                    func.lower(ResPartner.phone).like(like),
                )
            )
        if filters.country:
            query = query.where(ResPartner.country_code == filters.country.upper())
        if filters.is_company is not None:
            query = query.where(ResPartner.is_company == filters.is_company)
        order_column = getattr(ResPartner, filters.sort_by, ResPartner.name)
        query = query.order_by(desc(order_column) if filters.sort_order == "desc" else order_column)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self.session.scalars(query.offset((page - 1) * size).limit(size))
        return list(rows), total or 0

    async def get_customer(self, customer_id: int):
        customer = await self.session.scalar(
            select(ResPartner).where(ResPartner.id == customer_id, ResPartner.customer_rank > 0)
        )
        if not customer:
            return None

        invoice_count = await self.session.scalar(
            select(func.count()).select_from(AccountMove).where(AccountMove.partner_id == customer_id)
        )
        revenue = await self.session.scalar(
            select(func.coalesce(func.sum(AccountMove.amount_total), 0)).where(
                AccountMove.partner_id == customer_id,
                AccountMove.move_type == "out_invoice",
                AccountMove.state == "posted",
            )
        )
        order_count = await self.session.scalar(
            select(func.count()).select_from(SaleOrder).where(SaleOrder.partner_id == customer_id)
        )
        return customer, int(invoice_count or 0), Decimal(revenue or 0), int(order_count or 0)

    async def list_invoices(self, page: int, size: int, filters: InvoiceFilter):
        query = select(AccountMove).where(AccountMove.move_type == filters.move_type)
        if filters.partner_id:
            query = query.where(AccountMove.partner_id == filters.partner_id)
        if filters.payment_state:
            query = query.where(AccountMove.payment_state == filters.payment_state)
        if filters.date_from:
            query = query.where(AccountMove.invoice_date >= cast(filters.date_from, Date))
        if filters.date_to:
            query = query.where(AccountMove.invoice_date <= cast(filters.date_to, Date))
        order_column = getattr(AccountMove, filters.sort_by, AccountMove.invoice_date)
        query = query.order_by(desc(order_column) if filters.sort_order == "desc" else order_column)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self.session.scalars(query.offset((page - 1) * size).limit(size))
        return list(rows), total or 0

    async def list_payments(self, page: int, size: int, filters: PaymentFilter):
        query = select(AccountMoveLine).where(AccountMoveLine.credit > 0)
        if filters.partner_id:
            query = query.where(AccountMoveLine.partner_id == filters.partner_id)
        if filters.date_from:
            query = query.where(AccountMoveLine.date >= cast(filters.date_from, Date))
        if filters.date_to:
            query = query.where(AccountMoveLine.date <= cast(filters.date_to, Date))
        order_column = getattr(AccountMoveLine, filters.sort_by, AccountMoveLine.date)
        query = query.order_by(desc(order_column) if filters.sort_order == "desc" else order_column)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self.session.scalars(query.offset((page - 1) * size).limit(size))
        return list(rows), total or 0

    async def list_leads(self, page: int, size: int, filters: LeadFilter):
        query = select(CrmLead).where(CrmLead.type == "opportunity")
        if filters.search:
            like = f"%{filters.search.lower()}%"
            query = query.where(
                or_(func.lower(CrmLead.name).like(like), func.lower(CrmLead.partner_name).like(like))
            )
        if filters.stage and filters.stage.isdigit():
            query = query.where(CrmLead.stage_id == int(filters.stage))
        if filters.salesperson_id:
            query = query.where(CrmLead.user_id == filters.salesperson_id)
        order_column = getattr(CrmLead, filters.sort_by, CrmLead.create_date)
        query = query.order_by(desc(order_column) if filters.sort_order == "desc" else order_column)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self.session.scalars(query.offset((page - 1) * size).limit(size))
        return list(rows), total or 0

    async def list_products(self, page: int, size: int, filters: ProductFilter):
        query = select(ProductProduct).join(ProductTemplate, ProductProduct.product_tmpl_id == ProductTemplate.id)
        if filters.search:
            like = f"%{filters.search.lower()}%"
            query = query.where(
                or_(
                    func.lower(ProductTemplate.name).like(like),
                    func.lower(ProductTemplate.default_code).like(like),
                )
            )
        if filters.active is not None:
            query = query.where(ProductTemplate.active == filters.active)
        if filters.sale_ok is not None:
            query = query.where(ProductTemplate.sale_ok == filters.sale_ok)
        order_column = ProductTemplate.name if filters.sort_by == "name" else ProductTemplate.list_price
        query = query.order_by(desc(order_column) if filters.sort_order == "desc" else order_column)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self.session.scalars(query.offset((page - 1) * size).limit(size))
        return list(rows), total or 0

    async def list_orders(self, page: int, size: int, filters: OrderFilter):
        query = select(SaleOrder)
        if filters.partner_id:
            query = query.where(SaleOrder.partner_id == filters.partner_id)
        if filters.state:
            query = query.where(SaleOrder.state == filters.state)
        if filters.date_from:
            query = query.where(SaleOrder.date_order >= cast(filters.date_from, Date))
        if filters.date_to:
            query = query.where(SaleOrder.date_order <= cast(filters.date_to, Date))
        order_column = getattr(SaleOrder, filters.sort_by, SaleOrder.date_order)
        query = query.order_by(desc(order_column) if filters.sort_order == "desc" else order_column)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self.session.scalars(query.offset((page - 1) * size).limit(size))
        return list(rows), total or 0

    async def dashboard_metrics(self, year: int, month: int | None):
        month_condition = []
        if month:
            month_condition.append(func.extract("month", AccountMove.invoice_date) == month)

        total_customers = await self.session.scalar(
            select(func.count()).select_from(ResPartner).where(ResPartner.customer_rank > 0)
        )
        active_customers = await self.session.scalar(
            select(func.count()).select_from(ResPartner).where(
                ResPartner.customer_rank > 0, ResPartner.active.is_(True)
            )
        )
        total_invoices = await self.session.scalar(
            select(func.count()).select_from(AccountMove).where(AccountMove.move_type == "out_invoice")
        )
        paid_invoices = await self.session.scalar(
            select(func.count()).select_from(AccountMove).where(
                AccountMove.move_type == "out_invoice", AccountMove.payment_state == "paid"
            )
        )
        unpaid_invoices = await self.session.scalar(
            select(func.count()).select_from(AccountMove).where(
                AccountMove.move_type == "out_invoice", AccountMove.payment_state != "paid"
            )
        )
        total_revenue = await self.session.scalar(
            select(func.coalesce(func.sum(AccountMove.amount_total), 0)).where(
                AccountMove.move_type == "out_invoice", AccountMove.state == "posted"
            )
        )
        yearly_revenue = await self.session.scalar(
            select(func.coalesce(func.sum(AccountMove.amount_total), 0)).where(
                AccountMove.move_type == "out_invoice",
                AccountMove.state == "posted",
                func.extract("year", AccountMove.invoice_date) == year,
            )
        )
        monthly_revenue = await self.session.scalar(
            select(func.coalesce(func.sum(AccountMove.amount_total), 0)).where(
                AccountMove.move_type == "out_invoice",
                AccountMove.state == "posted",
                func.extract("year", AccountMove.invoice_date) == year,
                *month_condition,
            )
        )
        total_leads = await self.session.scalar(
            select(func.count()).select_from(CrmLead).where(CrmLead.type == "opportunity")
        )
        won_leads = await self.session.scalar(
            select(func.count()).select_from(CrmLead).where(
                CrmLead.type == "opportunity", CrmLead.probability == 100
            )
        )
        lost_leads = await self.session.scalar(
            select(func.count()).select_from(CrmLead).where(
                CrmLead.type == "opportunity", CrmLead.active.is_(False)
            )
        )

        top_products = await self.session.execute(
            select(
                ProductTemplate.id,
                ProductTemplate.name,
                func.coalesce(func.sum(SaleOrderLine.product_uom_qty), 0).label("qty"),
                func.coalesce(func.sum(SaleOrderLine.price_total), 0).label("revenue"),
            )
            .join(ProductProduct, ProductProduct.product_tmpl_id == ProductTemplate.id)
            .join(SaleOrderLine, SaleOrderLine.product_id == ProductProduct.id)
            .group_by(ProductTemplate.id, ProductTemplate.name)
            .order_by(desc("revenue"))
            .limit(5)
        )

        top_customers = await self.session.execute(
            select(
                ResPartner.id,
                ResPartner.name,
                func.coalesce(func.sum(AccountMove.amount_total), 0).label("revenue"),
            )
            .join(AccountMove, AccountMove.partner_id == ResPartner.id)
            .where(AccountMove.move_type == "out_invoice", AccountMove.state == "posted")
            .group_by(ResPartner.id, ResPartner.name)
            .order_by(desc("revenue"))
            .limit(5)
        )

        employee_stats = await self.session.execute(
            select(
                HREmployee.id,
                HREmployee.name,
                func.count(CrmLead.id).label("lead_count"),
                func.coalesce(func.sum(case((CrmLead.probability == 100, 1), else_=0)), 0).label("won_count"),
            )
            .outerjoin(CrmLead, CrmLead.user_id == HREmployee.user_id)
            .group_by(HREmployee.id, HREmployee.name)
            .order_by(desc("won_count"))
            .limit(10)
        )

        return {
            "total_customers": int(total_customers or 0),
            "active_customers": int(active_customers or 0),
            "total_invoices": int(total_invoices or 0),
            "paid_invoices": int(paid_invoices or 0),
            "unpaid_invoices": int(unpaid_invoices or 0),
            "total_revenue": Decimal(total_revenue or 0),
            "yearly_revenue": Decimal(yearly_revenue or 0),
            "monthly_revenue": Decimal(monthly_revenue or 0),
            "total_leads": int(total_leads or 0),
            "won_leads": int(won_leads or 0),
            "lost_leads": int(lost_leads or 0),
            "top_products": list(top_products.mappings().all()),
            "top_customers": list(top_customers.mappings().all()),
            "employee_stats": list(employee_stats.mappings().all()),
        }
