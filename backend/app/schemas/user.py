"""
NEXORA User & Authentication Schemas.
Enforces strict input validation and guarantees passwords/hashes are never exposed in responses.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    email: str = Field(..., min_length=5, max_length=100)
    role: str = Field("operator", pattern=r"^(admin|operator|observer)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Strong operator password")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern=r"^(admin|operator|observer)$")
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse


class BootstrapRequest(BaseModel):
    username: str = Field("admin", min_length=3, max_length=50)
    email: EmailStr = Field("admin@nexora.local")
    password: str = Field(..., min_length=8, max_length=128)
