import re

from pydantic import BaseModel, EmailStr, field_validator


class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        return value

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if len(value.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return value.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthSessionResponse(BaseModel):
    token_type: str = "cookie"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    is_verified: bool

    class Config:
        from_attributes = True


class RefreshRequest(BaseModel):
    refresh_token: str | None = None
