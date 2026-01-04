"""
Dependency Injection
Reusable dependencies for routes
"""

import logging
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.services.auth_service import get_user_from_token

logger = logging.getLogger(__name__)

# ============================================================================
# GET CURRENT USER (For protected routes)
# ============================================================================


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Use this dependency in any route that requires authentication.
    
    Args:
        request: HTTP request (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        User object if token is valid
    
    Raises:
        HTTPException 401: If token is missing, invalid, or expired
    
    Example Usage in Routes:
        @app.get("/api/works")
        async def list_works(current_user: User = Depends(get_current_user)):
            # current_user is automatically extracted and validated
            return {"user_id": current_user.id, "works": [...]}
    
    Flow:
        1. Client sends: Authorization: Bearer <token>
        2. Extract token from header
        3. get_user_from_token() validates and decodes JWT
        4. Query database for user
        5. Return user object (or raise 401)
    """
    # Get Authorization header
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token (remove "Bearer " prefix)
    token = auth_header.replace("Bearer ", "")
    
    logger.debug(f"Validating token: {token[:20]}...")
    
    # Get user from token
    user = get_user_from_token(db=db, token=token)
    
    if user is None:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Token validated for user: {user.username}")
    
    return user


# ============================================================================
# GET CURRENT ADMIN (For admin-only routes)
# ============================================================================


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current user and verify they are an admin.
    
    Use this dependency for admin-only routes.
    
    Args:
        current_user: Current authenticated user (auto-injected)
    
    Returns:
        User object if user is admin
    
    Raises:
        HTTPException 403: If user is not admin
    
    Example Usage:
        @app.delete("/api/users/{user_id}")
        async def delete_user(user_id: int, admin: User = Depends(get_current_admin)):
            # Only admins can call this route
            db.query(User).filter(User.id == user_id).delete()
            return {"message": "User deleted"}
    """
    if current_user.role != "Admin":
        logger.warning(f"Unauthorized admin access attempt by {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return current_user


# ============================================================================
# OPTIONAL CURRENT USER (For public routes that can be authenticated)
# ============================================================================


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    """
    Get the current user if authenticated, otherwise return None.
    
    Use this for routes that work both with and without authentication.
    
    Args:
        request: HTTP request (auto-injected)
        db: Database session
    
    Returns:
        User object if token is valid, None otherwise
    
    Example Usage:
        @app.get("/api/public-data")
        async def get_public_data(user: User | None = Depends(get_optional_user)):
            if user:
                return {"data": "personalized", "user_id": user.id}
            else:
                return {"data": "public"}
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    user = get_user_from_token(db=db, token=token)
    
    return user


# ============================================================================
# DEPENDENCY SUMMARY
# ============================================================================

# ============================================================================
# DEPENDENCY SUMMARY
# ============================================================================

"""
Use these dependencies in your routes:

1. get_current_user - Required authentication
   @app.get("/api/works")
   async def my_route(current_user: User = Depends(get_current_user)):
       return {"user": current_user.username}

2. get_current_admin - Admin-only
   @app.post("/api/admin/users")
   async def admin_route(admin: User = Depends(get_current_admin)):
       return {"admin": admin.username}

3. get_optional_user - Optional authentication
   @app.get("/api/public")
   async def public_route(user: User | None = Depends(get_optional_user)):
       if user:
           return {"authenticated": True}
       return {"authenticated": False}

Authorization Header Format:
Authorization: Bearer <jwt_token>

Flow when using get_current_user:
1. Client requests: GET /api/works
   Headers: Authorization: Bearer eyJhbGci...

2. FastAPI calls get_current_user dependency

3. Dependency extracts token from Authorization header

4. If valid:
   - Return User object
   - Route handler receives User

5. If invalid:
   - Raise HTTPException 401
   - Request fails before route handler runs

This prevents unauthorized access at the dependency level!
"""