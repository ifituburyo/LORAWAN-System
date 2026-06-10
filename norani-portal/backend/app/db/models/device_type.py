"""DeviceType — catalog of supported sensor/device models."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DeviceType(Base):
    __tablename__ = "device_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(255))
    model: Mapped[str | None] = mapped_column(String(255))

    # ChirpStack device profile ID this type maps to
    chirpstack_profile_id: Mapped[str] = mapped_column(String(36), nullable=False)

    region: Mapped[str] = mapped_column(String(20), nullable=False)  # eu868, us915_0, etc.
    description: Mapped[str | None] = mapped_column(String(1000))
    icon: Mapped[str | None] = mapped_column(String(100))  # icon identifier for UI

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
