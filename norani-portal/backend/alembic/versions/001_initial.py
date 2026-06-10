"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-06-10 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # customer_accounts
    op.create_table(
        "customer_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact_email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50)),
        sa.Column("address", sa.String(500)),
        sa.Column("chirpstack_tenant_id", sa.String(36), nullable=False, unique=True),
        sa.Column("chirpstack_application_id", sa.String(36)),
        sa.Column("plan_tier", sa.String(50), nullable=False, server_default="standard"),
        sa.Column("price_per_device_rwf", sa.Numeric(10, 2), nullable=False, server_default="1500"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("customer_account_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("customer_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "role IN ('admin', 'operator', 'viewer')",
            name="users_role_check",
        ),
    )
    op.create_index("ix_users_customer_account_id", "users", ["customer_account_id"])
    op.create_index("ix_users_email", "users", ["email"])

    # device_types
    op.create_table(
        "device_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("manufacturer", sa.String(255)),
        sa.Column("model", sa.String(255)),
        sa.Column("chirpstack_profile_id", sa.String(36), nullable=False),
        sa.Column("region", sa.String(20), nullable=False),
        sa.Column("description", sa.String(1000)),
        sa.Column("icon", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    # devices
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("customer_account_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("customer_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_type_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("device_types.id"), nullable=False),
        sa.Column("dev_eui", sa.String(16), nullable=False, unique=True),
        sa.Column("join_eui", sa.String(16), nullable=False, server_default="0000000000000000"),
        sa.Column("app_key_encrypted", sa.String(500), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location_name", sa.String(500)),
        sa.Column("location_lat", sa.Numeric(10, 7)),
        sa.Column("location_lon", sa.Numeric(10, 7)),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "status IN ('pending', 'active', 'offline', 'disabled')",
            name="devices_status_check",
        ),
    )
    op.create_index("ix_devices_customer_account_id", "devices", ["customer_account_id"])
    op.create_index("ix_devices_dev_eui", "devices", ["dev_eui"])
    op.create_index("idx_devices_account_status", "devices",
                    ["customer_account_id", "status"])

    # invoices
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("customer_account_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("customer_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_number", sa.String(50), nullable=False, unique=True),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("device_count", sa.Integer, nullable=False),
        sa.Column("amount_rwf", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_usd", sa.Numeric(12, 2)),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("generated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')",
            name="invoices_status_check",
        ),
    )
    op.create_index("ix_invoices_customer_account_id", "invoices", ["customer_account_id"])

    # audit_log
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("customer_account_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("customer_accounts.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50)),
        sa.Column("target_id", sa.String(255)),
        sa.Column("ip", postgresql.INET),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("details", postgresql.JSONB),
        sa.Column("timestamp", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_audit_timestamp", "audit_log", ["timestamp"])
    op.create_index("idx_audit_account_time", "audit_log",
                    ["customer_account_id", "timestamp"])


def downgrade() -> None:
    op.drop_index("idx_audit_account_time", "audit_log")
    op.drop_index("idx_audit_timestamp", "audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_invoices_customer_account_id", "invoices")
    op.drop_table("invoices")
    op.drop_index("idx_devices_account_status", "devices")
    op.drop_index("ix_devices_dev_eui", "devices")
    op.drop_index("ix_devices_customer_account_id", "devices")
    op.drop_table("devices")
    op.drop_table("device_types")
    op.drop_index("ix_users_email", "users")
    op.drop_index("ix_users_customer_account_id", "users")
    op.drop_table("users")
    op.drop_table("customer_accounts")
