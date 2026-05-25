from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResPartner(Base):
    __tablename__ = "res_partner"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    mobile: Mapped[str | None] = mapped_column(String)
    city: Mapped[str | None] = mapped_column(String)
    country_id: Mapped[int | None] = mapped_column(Integer)
    country_code: Mapped[str | None] = mapped_column(String)
    is_company: Mapped[bool | None] = mapped_column(Boolean)
    active: Mapped[bool | None] = mapped_column(Boolean)
    create_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    customer_rank: Mapped[int | None] = mapped_column(Integer)


class SaleOrder(Base):
    __tablename__ = "sale_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    partner_id: Mapped[int | None] = mapped_column(ForeignKey("res_partner.id"))
    user_id: Mapped[int | None] = mapped_column(Integer)
    state: Mapped[str | None] = mapped_column(String)
    amount_total: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    date_order: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    partner = relationship("ResPartner", lazy="joined")


class SaleOrderLine(Base):
    __tablename__ = "sale_order_line"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("sale_order.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("product_product.id"))
    name: Mapped[str | None] = mapped_column(Text)
    product_uom_qty: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    price_total: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))


class AccountMove(Base):
    __tablename__ = "account_move"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    partner_id: Mapped[int | None] = mapped_column(ForeignKey("res_partner.id"))
    invoice_date: Mapped[date | None] = mapped_column(Date)
    invoice_date_due: Mapped[date | None] = mapped_column(Date)
    state: Mapped[str | None] = mapped_column(String)
    payment_state: Mapped[str | None] = mapped_column(String)
    move_type: Mapped[str | None] = mapped_column(String)
    amount_total: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    amount_residual: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    currency_id: Mapped[int | None] = mapped_column(Integer)
    partner = relationship("ResPartner", lazy="joined")


class AccountMoveLine(Base):
    __tablename__ = "account_move_line"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    move_id: Mapped[int | None] = mapped_column(ForeignKey("account_move.id"))
    partner_id: Mapped[int | None] = mapped_column(Integer)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("product_product.id"))
    date: Mapped[date | None] = mapped_column(Date)
    debit: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    credit: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    balance: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    name: Mapped[str | None] = mapped_column(Text)


class CrmLead(Base):
    __tablename__ = "crm_lead"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    partner_name: Mapped[str | None] = mapped_column(String)
    email_from: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    stage_id: Mapped[int | None] = mapped_column(Integer)
    user_id: Mapped[int | None] = mapped_column(Integer)
    expected_revenue: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    probability: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    active: Mapped[bool | None] = mapped_column(Boolean)
    type: Mapped[str | None] = mapped_column(String)
    create_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProductTemplate(Base):
    __tablename__ = "product_template"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    default_code: Mapped[str | None] = mapped_column(String)
    list_price: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    active: Mapped[bool | None] = mapped_column(Boolean)
    sale_ok: Mapped[bool | None] = mapped_column(Boolean)
    type: Mapped[str | None] = mapped_column(String)


class ProductProduct(Base):
    __tablename__ = "product_product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_tmpl_id: Mapped[int | None] = mapped_column(ForeignKey("product_template.id"))
    default_code: Mapped[str | None] = mapped_column(String)
    active: Mapped[bool | None] = mapped_column(Boolean)
    template = relationship("ProductTemplate", lazy="joined")


class ResUsers(Base):
    __tablename__ = "res_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool | None] = mapped_column(Boolean)


class HREmployee(Base):
    __tablename__ = "hr_employee"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    user_id: Mapped[int | None] = mapped_column(Integer)
    work_email: Mapped[str | None] = mapped_column(String)
    active: Mapped[bool | None] = mapped_column(Boolean)
