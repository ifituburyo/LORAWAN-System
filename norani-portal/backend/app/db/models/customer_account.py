"""CustomerAccount model — one per customer organisation."""

import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CustomerAccount(Base):
    __tablename__ = "customer_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(500))

    # ChirpStack mapping
    chirpstack_tenant_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
    )
    chirpstack_application_id: Mapped[str | None] = mapped_column(String(36))

    # Billing
    plan_tier: Mapped[str] = mapped_column(String(50), default="standard", nullable=False)
    price_per_device_rwf: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=1500,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        back_populates="customer_account",
        cascade="all, delete-orphan",
    )
    devices: Mapped[list["Device"]] = relationship(
        back_populates="customer_account",
        cascade="all, delete-orphan",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="customer_account",
        cascade="all, delete-orphan",
    )
