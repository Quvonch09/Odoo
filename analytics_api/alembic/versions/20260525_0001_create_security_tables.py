"""create analytics security tables"""

from alembic import op
import sqlalchemy as sa


revision = "20260525_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")

    op.create_table(
        "analytics_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="analytics",
    )

    op.create_table(
        "analytics_api_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("analytics.analytics_users.id"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("key_prefix", sa.String(length=16), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="analytics",
    )

    op.create_table(
        "analytics_audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("auth_type", sa.String(length=16), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="analytics",
    )


def downgrade() -> None:
    op.drop_table("analytics_audit_logs", schema="analytics")
    op.drop_table("analytics_api_keys", schema="analytics")
    op.drop_table("analytics_users", schema="analytics")
    op.execute("DROP SCHEMA IF EXISTS analytics")
