"""Billing endpoints — view current bill, invoice history."""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.invoice import Invoice
from app.db.models.user import User
from app.services.billing_service import compute_current_period_invoice

router = APIRouter()


@router.get("/current")
async def get_current_period(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Compute the projected invoice for the current month."""
    return await compute_current_period_invoice(db, user.customer_account)


@router.get("/invoices")
async def list_invoices(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """List past invoices for the customer."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.customer_account_id == user.customer_account_id)
        .order_by(Invoice.period_start.desc())
    )
    invoices = result.scalars().all()
    return [
        {
            "id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "period_start": inv.period_start.isoformat(),
            "period_end": inv.period_end.isoformat(),
            "device_count": inv.device_count,
            "amount_rwf": float(inv.amount_rwf),
            "amount_usd": float(inv.amount_usd) if inv.amount_usd else None,
            "status": inv.status,
            "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
        }
        for inv in invoices
    ]
