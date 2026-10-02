from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    restaurant_name: str = Field(min_length=1, max_length=100)
    restaurant_address: str = Field(min_length=1, max_length=200)
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    # Never trimmed: a trailing space is part of the password, not noise.
    password: str = Field(min_length=10, max_length=128)

    @field_validator("restaurant_name", "restaurant_address", "full_name", mode="before")
    @classmethod
    def strip_text_fields(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


class LoginRequest(BaseModel):
    email: EmailStr
    # Capped so an absurdly long input can't be used to force extra work out
    # of Argon2, which is deliberately slow. Never trimmed, same reason as
    # RegisterRequest.password.
    password: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class RestaurantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    vat_number: str | None
    timezone: str
    created_at: datetime


class AccountResponse(BaseModel):
    user: UserRead
    restaurant: RestaurantRead
