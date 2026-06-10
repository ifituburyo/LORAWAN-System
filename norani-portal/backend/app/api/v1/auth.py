"""Authentication endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.core.security import create_access_token, verify_password
from app.db.models.user import User
from app.db.models.audit import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse, UserOut

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate with email + password, return a JWT."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.customer_account))
        .where(User.email == payload.email.lower())
    )
    user = result.scalar_one_or_none()

    # Same error message whether email or password is wrong (prevent enumeration)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    if not user.customer_account.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account suspended",
        )

    # Update last_login_at
    user.last_login_at = datetime.now(timezone.utc)

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        customer_account_id=user.customer_account_id,
        action="user.login",
        target_type="user",
        target_id=str(user.id),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    db.add(audit)
    await db.commit()

    # Generate JWT
    token = create_access_token(
        user_id=str(user.id),
        customer_account_id=str(user.customer_account_id),
        role=user.role,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_hours * 3600,
        user=UserOut(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            customer_account_id=str(user.customer_account_id),
            customer_account_name=user.customer_account.name,
        ),
    )


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    """Return the current authenticated user."""
    return UserOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        customer_account_id=str(user.customer_account_id),
        customer_account_name=user.customer_account.name,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Log out the user. Since JWTs are stateless, this is mostly for audit logging.
    The frontend should discard the token on its side.

    (Future: maintain a Redis blocklist of revoked tokens.)
    """
    audit = AuditLog(
        user_id=user.id,
        customer_account_id=user.customer_account_id,
        action="user.logout",
        target_type="user",
        target_id=str(user.id),
        ip=request.client.host if request.client else None,
    )
    db.add(audit)
    await db.commit()
