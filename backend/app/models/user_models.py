from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    """Model for user registration."""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Model for JWT token response."""
    access_token: str
    token_type: str


class User(BaseModel):
    """Model for user data (without password)."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    disabled: bool = False
