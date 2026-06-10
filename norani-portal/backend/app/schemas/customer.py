"""Pydantic schemas for customer account & admin endpoints."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class CustomerAccountOut(BaseModel):
    id: str
    name: str
    contact_email: str
    phone: str | None
    address: str | None
    plan_tier: str
    price_per_device_rwf: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerAccountCreate(BaseModel):
    """For admin: provision a new customer."""
    name: str = Field(min_length=1, max_length=255)
    contact_email: EmailStr
    phone: str | None = None
    address: str | None = None
    plan_tier: str = "standard"
    price_per_device_rwf: float = 1500
    # First user details
    first_user_email: EmailStr
    first_user_name: str
    first_user_password: str = Field(min_length=8)


class CustomerAccountCreateResponse(BaseModel):
    account: CustomerAccountOut
    first_user_id: str
    chirpstack_tenant_id: str
    chirpstack_application_id: str


class UserCreate(BaseModel):
    """For admin: add a user to an existing customer account."""
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)
    role: str = Field(default="viewer", pattern="^(admin|operator|viewer)$")


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    customer_account_id: str
    customer_account_name: str

    class Config:
        from_attributes = True
