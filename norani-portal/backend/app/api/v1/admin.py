"""Admin endpoints — Norani staff manage customer accounts.

Access restricted to users with role='admin' AND belonging to the internal
Norani account (identified by env var or a flag).
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.core.security import hash_password
from app.db.models.audit import AuditLog
from app.db.models.customer_account import CustomerAccount
from app.db.models.user import User
from app.schemas.customer import (
    CustomerAccountCreate,
    CustomerAccountCreateResponse,
    CustomerAccountOut,
    UserCreate,
    UserOut,
)
from app.services.chirpstack_client import cs_client, ChirpStackError

router = APIRouter()


@router.get("/customers", response_model=list[CustomerAccountOut])
async def list_customers(
    user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CustomerAccountOut]:
    """List all customer accounts (admin only)."""
    result = await db.execute(
        select(CustomerAccount).order_by(CustomerAccount.created_at.desc())
    )
    accounts = result.scalars().all()
    return [
        CustomerAccountOut(
            id=str(a.id),
            name=a.name,
            contact_email=a.contact_email,
            phone=a.phone,
            address=a.address,
            plan_tier=a.plan_tier,
            price_per_device_rwf=float(a.price_per_device_rwf),
            is_active=a.is_active,
            created_at=a.created_at,
        )
        for a in accounts
    ]


@router.post(
    "/customers",
    response_model=CustomerAccountCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer(
    payload: CustomerAccountCreate,
    request: Request,
    user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CustomerAccountCreateResponse:
    """
    Provision a new customer account.

    Flow:
        1. Create ChirpStack tenant
        2. Create default Application in that tenant
        3. Save CustomerAccount record
        4. Create the first user (admin role)
        5. Roll back ChirpStack if anything fails
    """
    # Check email uniqueness
    existing = await db.execute(
        select(User).where(User.email == payload.first_user_email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # 1+2. Create ChirpStack tenant + default application
    tenant_id = None
    try:
        tenant_id = cs_client.create_tenant(name=payload.name)
        application_id = cs_client.create_application(
            tenant_id=tenant_id,
            name="Default",
            description=f"Default application for {payload.name}",
        )
    except ChirpStackError as e:
        if tenant_id:
            cs_client.delete_tenant(tenant_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"ChirpStack provisioning failed: {e}",
        )

    # 3+4. Save in portal DB
    try:
        account = CustomerAccount(
            name=payload.name,
            contact_email=payload.contact_email,
            phone=payload.phone,
            address=payload.address,
            chirpstack_tenant_id=tenant_id,
            chirpstack_application_id=application_id,
            plan_tier=payload.plan_tier,
            price_per_device_rwf=payload.price_per_device_rwf,
        )
        db.add(account)
        await db.flush()  # get account.id without committing

        first_user = User(
            customer_account_id=account.id,
            email=payload.first_user_email.lower(),
            password_hash=hash_password(payload.first_user_password),
            full_name=payload.first_user_name,
            role="admin",
            is_active=True,
        )
        db.add(first_user)

        audit = AuditLog(
            user_id=user.id,
            customer_account_id=account.id,
            action="admin.customer.create",
            target_type="customer_account",
            target_id=str(account.id),
            ip=request.client.host if request.client else None,
            details={"name": payload.name, "tenant_id": tenant_id},
        )
        db.add(audit)

        await db.commit()
        await db.refresh(account)
        await db.refresh(first_user)

    except Exception as e:
        cs_client.delete_tenant(tenant_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )

    return CustomerAccountCreateResponse(
        account=CustomerAccountOut(
            id=str(account.id),
            name=account.name,
            contact_email=account.contact_email,
            phone=account.phone,
            address=account.address,
            plan_tier=account.plan_tier,
            price_per_device_rwf=float(account.price_per_device_rwf),
            is_active=account.is_active,
            created_at=account.created_at,
        ),
        first_user_id=str(first_user.id),
        chirpstack_tenant_id=tenant_id,
        chirpstack_application_id=application_id,
    )


# ─── User management within an account ──────────────────────────────────────

@router.get("/customers/{account_id}/users", response_model=list[UserOut])
async def list_account_users(
    account_id: str,
    user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[UserOut]:
    """List all users belonging to a customer account."""
    account = await db.get(CustomerAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    result = await db.execute(
        select(User).where(User.customer_account_id == account_id).order_by(User.created_at)
    )
    users = result.scalars().all()
    return [
        UserOut(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            customer_account_id=str(u.customer_account_id),
            customer_account_name=account.name,
        )
        for u in users
    ]


@router.post(
    "/customers/{account_id}/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_account_user(
    account_id: str,
    payload: UserCreate,
    request: Request,
    user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    """Add a new user to an existing customer account."""
    account = await db.get(CustomerAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    existing = await db.execute(select(User).where(User.email == payload.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    new_user = User(
        customer_account_id=account_id,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )
    db.add(new_user)

    audit = AuditLog(
        user_id=user.id,
        customer_account_id=account_id,
        action="admin.user.create",
        target_type="user",
        target_id=payload.email,
        ip=request.client.host if request.client else None,
        details={"email": payload.email, "role": payload.role, "account": account.name},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(new_user)

    return UserOut(
        id=str(new_user.id),
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
        customer_account_id=str(new_user.customer_account_id),
        customer_account_name=account.name,
    )


@router.delete("/customers/{account_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_account_user(
    account_id: str,
    user_id: str,
    request: Request,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Remove a user from a customer account. Cannot remove yourself."""
    if str(admin.id) == user_id:
        raise HTTPException(status_code=400, detail="You cannot remove your own account")

    result = await db.execute(
        select(User).where(User.id == user_id, User.customer_account_id == account_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found in this account")

    audit = AuditLog(
        user_id=admin.id,
        customer_account_id=account_id,
        action="admin.user.delete",
        target_type="user",
        target_id=user_id,
        ip=request.client.host if request.client else None,
        details={"email": target.email},
    )
    db.add(audit)
    await db.delete(target)
    await db.commit()
