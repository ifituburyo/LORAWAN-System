"""Billing service — compute monthly invoices from device counts."""

from datetime import date, datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.customer_account import CustomerAccount
from app.db.models.device import Device


async def compute_active_device_count(
    db: AsyncSession,
    customer_account_id: str,
) -> int:
    """Count devices that are not disabled for a customer."""
    result = await db.execute(
        select(func.count(Device.id))
        .where(Device.customer_account_id == customer_account_id)
        .where(Device.status != "disabled")
    )
    return result.scalar() or 0


async def compute_current_period_invoice(
    db: AsyncSession,
    account: CustomerAccount,
) -> dict:
    """
    Compute the projected invoice for the current month.

    Returns:
        dict with device_count, amount_rwf, amount_usd, period_start, period_end
    """
    today = date.today()
    period_start = today.replace(day=1)
    # Next month minus a day = last day of current month
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)

    device_count = await compute_active_device_count(db, account.id)
    amount_rwf = float(account.price_per_device_rwf) * device_count
    # Rough USD conversion (1 USD ≈ 1300 RWF as of 2026; replace with live rate later)
    amount_usd = round(amount_rwf / 1300, 2)

    return {
        "device_count": device_count,
        "period_start": period_start.isoformat(),
        "period_end": (next_month.toordinal() - 1 and date.fromordinal(next_month.toordinal() - 1)).isoformat(),
        "amount_rwf": amount_rwf,
        "amount_usd": amount_usd,
        "price_per_device_rwf": float(account.price_per_device_rwf),
    }
