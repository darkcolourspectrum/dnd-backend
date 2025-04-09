from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
import uuid

class UserBase(BaseModel):
    email: EmailStr
    nickname: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    fingerprint: str = Field(..., min_length=8, description="Device fingerprint")

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    fingerprint: str = Field(..., min_length=8)

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    fingerprint: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class MessageResponse(BaseModel):
    message: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True