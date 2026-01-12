"""
User Schemas
Pydantic models for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ============================================================================
# REQUESTS (What client sends to API)
# ============================================================================


class UserRegisterRequest(BaseModel):
    """User registration request"""
    
    username: str = Field(..., min_length=3, max_length=50)
    """Username (3-50 characters)"""
    
    email: EmailStr
    """Email address (must be valid format)"""
    
    password: str = Field(..., min_length=8)
    """Password (minimum 8 characters)"""
    
    full_name: str = Field(..., min_length=2, max_length=100)
    """Full name (2-100 characters)"""

    role: str = Field(..., min_length=2, max_length=100)
    """User Role (Engineer, Admin)"""
    
    class Config:
        example = {
            "username": "engineer1",
            "email": "engineer@company.com",
            "password": "SecurePassword123",
            "full_name": "John Engineer",
            "role": "Engineer"
        }


class UserLoginRequest(BaseModel):
    """User login request"""
    
    username: str = Field(..., min_length=3)
    """Username"""
    
    password: str = Field(..., min_length=8)
    """Password"""
    
    class Config:
        example = {
            "username": "engineer1",
            "password": "SecurePassword123"
        }


class UserUpdateRequest(BaseModel):
    """User update request"""
    
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    """Full name (optional, 2-100 characters)"""
    
    role: Optional[str] = Field(None, min_length=2, max_length=100)
    """User role (optional, 'Engineer' or 'Admin')"""
    
    class Config:
        example = {
            "full_name": "John Updated",
            "role": "Admin"
        }


class UserStatusRequest(BaseModel):
    """Request to change user active status"""
    
    is_active: bool
    """Whether user should be active or deactivated"""
    
    class Config:
        example = {
            "is_active": False
        }


# ============================================================================
# RESPONSES (What API sends back to client)
# ============================================================================


class UserResponse(BaseModel):
    """User data response (never include password)"""
    
    id: int
    """User ID"""
    
    username: str
    """Username"""
    
    email: str
    """Email address"""
    
    full_name: str
    """Full name"""
    
    role: str
    """User role: 'Engineer' or 'Admin'"""
    
    is_active: bool
    """Whether user account is active"""
    
    created_at: datetime
    """When user was created"""
    
    class Config:
        from_attributes = True  # Allow creation from ORM models
        example = {
            "id": 1,
            "username": "engineer1",
            "email": "engineer@company.com",
            "full_name": "John Engineer",
            "role": "Engineer",
            "is_active": True,
            "created_at": "2024-01-15T10:30:00"
        }


class UsersListResponse(BaseModel):
    """Response for listing users"""
    
    users: list[UserResponse]
    """List of users"""
    
    total: int
    """Total count of users"""
    
    class Config:
        example = {
            "users": [
                {
                    "id": 1,
                    "username": "engineer1",
                    "email": "engineer@company.com",
                    "full_name": "John Engineer",
                    "role": "Engineer",
                    "created_at": "2024-01-15T10:30:00"
                },
                {
                    "id": 2,
                    "username": "admin1",
                    "email": "admin@company.com",
                    "full_name": "Admin User",
                    "role": "Admin",
                    "created_at": "2024-01-14T10:30:00"
                }
            ],
            "total": 2
        }


class AuthResponse(BaseModel):
    """Authentication response with token"""
    
    user: UserResponse
    """User data"""
    
    access_token: str
    """JWT access token"""
    
    token_type: str = "bearer"
    """Token type (always 'bearer')"""
    
    class Config:
        example = {
            "user": {
                "id": 1,
                "username": "engineer1",
                "email": "engineer@company.com",
                "full_name": "John Engineer",
                "role": "Engineer",
                "created_at": "2024-01-15T10:30:00"
            },
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }


class TokenData(BaseModel):
    """JWT token payload data"""
    
    sub: int
    """Subject (user_id)"""
    
    exp: int
    """Expiration timestamp"""


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Returns: (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and digits"
    
    return True, "Password is strong"


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format.
    
    Returns: (is_valid, message)
    """
    if not username.isalnum() and '_' not in username:
        return False, "Username can only contain letters, numbers, and underscores"
    
    if username[0].isdigit():
        return False, "Username cannot start with a number"
    
    return True, "Username is valid"