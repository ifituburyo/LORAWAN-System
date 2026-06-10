"""Customer account self-service endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.customer import CustomerAccountOut

router = APIRouter()


@router.get("", response_model=CustomerAccountOut)
async def get_my_account(
    user: Annotated[User, Depends(get_current_user)],
) -> CustomerAccountOut:
    """Return the authenticated user's customer account."""
    account = user.customer_account
    return CustomerAccountOut(
        id=str(account.id),
        name=account.name,
        contact_email=account.contact_email,
        phone=account.phone,
        address=account.address,
        plan_tier=account.plan_tier,
        price_per_device_rwf=float(account.price_per_device_rwf),
        is_active=account.is_active,
        created_at=account.created_at,
    )
