"""Invoice — monthly bill per customer account."""

import uuid
from datetime import datetime, date
from sqlalchemy import String, Numeric, Integer, Date, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')",
            name="invoices_status_check",
        ),
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

    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    device_count: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_rwf: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    amount_usd: Mapped[float | None] = mapped_column(Numeric(12, 2))

    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer_account: Mapped["CustomerAccount"] = relationship(back_populates="invoices")
