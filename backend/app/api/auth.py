"""
Authentication Routes
POST /api/auth/register - Register new user
POST /api/auth/login - Login user
POST /api/auth/logout - Logout user (optional)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    AuthResponse,
    UserResponse,
)
from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_access_token,
)

logger = logging.getLogger(__name__)

# Create router for auth endpoints
router = APIRouter()

# ============================================================================
# REGISTER ENDPOINT
# ============================================================================


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account",
)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Register a new user account.
    
    Args:
        request: Registration data (username, email, password, full_name)
        db: Database session (auto-injected)
    
    Returns:
        AuthResponse with user data and access token
    
    Raises:
        HTTPException 400: If username/email exists or password is weak
        HTTPException 500: If registration fails
    
    Example:
        POST /api/auth/register
        {
            "username": "engineer1",
            "email": "engineer@company.com",
            "password": "SecurePassword123",
            "full_name": "John Engineer"
        }
    """
    logger.info(f"Registration attempt: {request.username}")
    
    # Call service to register user
    user, error = register_user(
        db=db,
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
    )
    
    # If registration failed, return error
    if error:
        logger.warning(f"Registration failed: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    # Generate JWT token
    access_token = create_access_token(user_id=user.id)
    
    logger.info(f"✅ User registered successfully: {user.username}")
    
    # Return user data + token
    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer",
    )


# ============================================================================
# LOGIN ENDPOINT
# ============================================================================


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user and get access token",
)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Login with username and password.
    
    Args:
        request: Login credentials (username, password)
        db: Database session (auto-injected)
    
    Returns:
        AuthResponse with user data and access token
    
    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 500: If login fails
    
    Example:
        POST /api/auth/login
        {
            "username": "engineer1",
            "password": "SecurePassword123"
        }
        
        Response:
        {
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
    """
    logger.info(f"Login attempt: {request.username}")
    
    # Call service to authenticate user
    user, error = authenticate_user(
        db=db,
        username=request.username,
        password=request.password,
    )
    
    # If authentication failed, return error
    if error:
        logger.warning(f"Login failed for {request.username}: {error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    access_token = create_access_token(user_id=user.id)
    
    logger.info(f"✅ User logged in: {user.username}")
    
    # Return user data + token
    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer",
    )


# ============================================================================
# LOGOUT ENDPOINT (Optional)
# ============================================================================


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Logout current user (frontend should delete token)",
)
async def logout() -> dict:
    """
    Logout endpoint.
    
    Note: With JWT tokens, logout is handled on the frontend by deleting the token.
    This endpoint is optional and mainly for frontend convenience.
    
    Returns:
        Success message
    
    Example:
        POST /api/auth/logout
        
        Response:
        {
            "message": "Successfully logged out",
            "status": "success"
        }
    """
    logger.info("User logged out")
    
    return {
        "message": "Successfully logged out",
        "status": "success",
    }


# ============================================================================
# ROUTE SUMMARY
# ============================================================================

"""
Routes defined in this file:

1. POST /api/auth/register
   - Register new user
   - Request: username, email, password, full_name
   - Response: user data + access_token
   - Status: 201 Created or 400 Bad Request

2. POST /api/auth/login
   - Login user
   - Request: username, password
   - Response: user data + access_token
   - Status: 200 OK or 401 Unauthorized

3. POST /api/auth/logout
   - Logout user (frontend deletes token)
   - Request: (bearer token in header)
   - Response: success message
   - Status: 200 OK

All endpoints are documented in Swagger UI at /docs
"""