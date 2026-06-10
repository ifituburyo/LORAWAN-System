"""Device — represents a registered LoRaWAN sensor."""

import uuid
from datetime import datetime
from sqlalchemy import (
    String, Numeric, DateTime, ForeignKey, CheckConstraint, Index, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'offline', 'disabled')",
            name="devices_status_check",
        ),
        Index("idx_devices_account_status", "customer_account_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    customer_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("device_types.id"),
        nullable=False,
    )

    # LoRaWAN identifiers
    dev_eui: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    join_eui: Mapped[str] = mapped_column(
        String(16),
        default="0000000000000000",
        nullable=False,
    )

    # AppKey stored encrypted (Fernet-wrapped); never exposed in plaintext after creation
    app_key_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)

    # Customer-facing metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_name: Mapped[str | None] = mapped_column(String(500))
    location_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    location_lon: Mapped[float | None] = mapped_column(Numeric(10, 7))

    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )

    # Relationships
    customer_account: Mapped["CustomerAccount"] = relationship(back_populates="devices")
    device_type: Mapped["DeviceType"] = relationship()
