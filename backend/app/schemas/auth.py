from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.security import Role


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    organization: str | None = None
    role: Role = Role.AUDITOR


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Role
    organization: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
