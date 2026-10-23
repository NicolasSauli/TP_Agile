"""
Pydantic models for authentication system
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user model"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation model with password"""
    password: str = Field(..., min_length=8, max_length=100)


class UserInDBBase(UserBase):
    """User model with ID"""
    id: int
    is_active: bool = True
    is_superuser: bool = False


class UserInDB(UserInDBBase):
    """User model with hashed password"""
    hashed_password: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserPublic(UserInDBBase):
    """Public user model (no password)"""
    created_at: datetime


class Token(BaseModel):
    """JWT Token model"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    email: Optional[str] = None


class TokenBlacklist(BaseModel):
    """Model for blacklisted tokens"""
    token: str
    expired_at: datetime


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    user: UserPublic
    token: Token


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str
    detail: Optional[str] = None


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8)
