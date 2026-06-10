"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    customer_account_id: str
    customer_account_name: str

    class Config:
        from_attributes = True


# Forward reference resolution
TokenResponse.model_rebuild()
