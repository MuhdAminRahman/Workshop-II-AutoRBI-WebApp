"""
Users Routes - CRUD Operations
GET /api/users - List all users (admin only)
GET /api/users/{userId} - Get user details
PUT /api/users/{userId} - Update user
DELETE /api/users/{userId} - Delete user
GET /api/users/me - Get current user profile
PUT /api/users/me - Update current user profile
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserRole
from app.dependencies import get_current_user
from app.schemas.user import (
    UserResponse,
    UserUpdateRequest,
    UserStatusRequest,
    UsersListResponse,
)
from app.services.user_service import (
    get_user_by_id,
    list_all_users,
    update_user,
    delete_user,
    deactivate_user,
    reactivate_user,
)

logger = logging.getLogger(__name__)

# Create router for user endpoints
router = APIRouter()

# ============================================================================
# GET CURRENT USER PROFILE - GET /api/users/me
# ============================================================================


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get authenticated user's profile information",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user's profile.
    
    Args:
        current_user: Current authenticated user (auto-injected)
    
    Returns:
        UserResponse with user details
    
    Example:
        GET /api/users/me
        
        Response:
        {
            "id": 1,
            "username": "engineer1",
            "email": "engineer@company.com",
            "full_name": "John Engineer",
            "role": "Engineer",
            "created_at": "2024-01-15T10:30:00"
        }
    """
    logger.info(f"Getting profile for user {current_user.username}")
    
    return UserResponse.model_validate(current_user)


# ============================================================================
# UPDATE CURRENT USER PROFILE - PUT /api/users/me
# ============================================================================


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update authenticated user's profile information",
)
async def update_current_user_profile(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Update current user's profile.
    
    Can update: full_name
    Cannot update: username, email, role (use admin endpoints)
    
    Args:
        request: Update data (full_name)
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Updated UserResponse
    
    Raises:
        HTTPException 400: If update fails
    
    Example:
        PUT /api/users/me
        {
            "full_name": "John Updated"
        }
    """
    logger.info(f"Updating profile for user {current_user.username}")
    
    # Only allow updating full_name for self
    user, error = update_user(
        db=db,
        user_id=current_user.id,
        full_name=request.full_name,
    )
    
    if error:
        logger.warning(f"Failed to update user profile: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    logger.info(f"✅ User profile updated: {user.username}")
    
    return UserResponse.model_validate(user)


# ============================================================================
# LIST ALL USERS - GET /api/users (Admin only)
# ============================================================================


@router.get(
    "",
    response_model=UsersListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users",
    description="Get all users in the system (admin only)",
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    role: str = Query(None, description="Filter by role (Engineer, Admin)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UsersListResponse:
    """
    List all users in the system.
    
    Only admins can access this endpoint.
    
    Args:
        skip: Pagination - number of records to skip (default 0)
        limit: Pagination - max records to return (default 100, max 1000)
        role: Optional filter by role
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        List of users with total count
    
    Raises:
        HTTPException 403: If user is not an admin
    
    Example:
        GET /api/users?skip=0&limit=10
        GET /api/users?role=Engineer
        
        Response:
        {
            "users": [
                {
                    "id": 1,
                    "username": "engineer1",
                    "email": "engineer@company.com",
                    ...
                }
            ],
            "total": 5
        }
    """
    logger.info(f"User {current_user.username} listing all users")
    
    # Check admin permission
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to list users")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list all users",
        )
    
    users, total = list_all_users(
        db=db,
        skip=skip,
        limit=limit,
        role=role,
    )
    
    return UsersListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
    )


# ============================================================================
# GET USER DETAILS - GET /api/users/{userId} (Admin or self)
# ============================================================================


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user details",
    description="Get user details (admin or self only)",
)
async def get_user_details(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Get user details.
    
    Users can view their own profile, admins can view any user.
    
    Args:
        user_id: User ID
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        UserResponse with user details
    
    Raises:
        HTTPException 403: If user is not admin and not requesting own profile
        HTTPException 404: If user not found
    
    Example:
        GET /api/users/1
        
        Response:
        {
            "id": 1,
            "username": "engineer1",
            "email": "engineer@company.com",
            ...
        }
    """
    logger.info(f"User {current_user.username} requesting user {user_id} details")
    
    # Check permission: admin or self
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        logger.warning(f"User {current_user.username} tried to view unauthorized user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile or be an admin",
        )
    
    user = get_user_by_id(db=db, user_id=user_id)
    
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse.model_validate(user)


# ============================================================================
# UPDATE USER - PUT /api/users/{userId} (Admin only)
# ============================================================================


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
    description="Update user details (admin only)",
)
async def update_user_details(
    user_id: int,
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Update user details.
    
    Only admins can update other users.
    
    Args:
        user_id: User ID
        request: Update data (full_name, role)
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Updated UserResponse
    
    Raises:
        HTTPException 403: If user is not admin
        HTTPException 404: If user not found
        HTTPException 400: If update fails
    
    Example:
        PUT /api/users/1
        {
            "full_name": "John Updated",
            "role": "Admin"
        }
    """
    logger.info(f"User {current_user.username} updating user {user_id}")
    
    # Check admin permission
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to update user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update users",
        )
    
    # Verify user exists
    user = get_user_by_id(db=db, user_id=user_id)
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update user
    user, error = update_user(
        db=db,
        user_id=user_id,
        full_name=request.full_name,
        role=request.role,
    )
    
    if error:
        logger.warning(f"Failed to update user {user_id}: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    logger.info(f"✅ User updated: {user.username}")
    
    return UserResponse.model_validate(user)


# ============================================================================
# DELETE USER - DELETE /api/users/{userId} (Admin only)
# ============================================================================


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete user and all related data (admin only)",
)
async def delete_user_account(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a user account.
    
    Only admins can delete users.
    Cascade deletes all user's related data (works, files, etc.)
    
    Args:
        user_id: User ID
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        None (204 No Content)
    
    Raises:
        HTTPException 403: If user is not admin
        HTTPException 404: If user not found
        HTTPException 400: If deletion fails
    
    Example:
        DELETE /api/users/1
    """
    logger.info(f"User {current_user.username} deleting user {user_id}")
    
    # Check admin permission
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to delete user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete users",
        )
    
    # Verify user exists
    user = get_user_by_id(db=db, user_id=user_id)
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent self-deletion
    if current_user.id == user_id:
        logger.warning(f"Admin {current_user.username} attempted to delete themselves")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    # Delete user
    success, error = delete_user(db=db, user_id=user_id)
    
    if not success:
        logger.warning(f"Failed to delete user {user_id}: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    logger.info(f"✅ User deleted: {user.username}")


# ============================================================================
# DEACTIVATE USER - PUT /api/users/{userId}/deactivate (Admin only)
# ============================================================================


@router.put(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate user",
    description="Deactivate a user account (admin only)",
)
async def deactivate_user_account(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Deactivate a user account.
    
    Soft delete - user data is preserved but account cannot be used for login.
    Only admins can deactivate users.
    
    Args:
        user_id: User ID
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Updated UserResponse with is_active=False
    
    Raises:
        HTTPException 403: If user is not admin
        HTTPException 404: If user not found
        HTTPException 400: If user already deactivated
    
    Example:
        PUT /api/users/1/deactivate
        
        Response:
        {
            "id": 1,
            "username": "engineer1",
            "email": "engineer@company.com",
            "full_name": "John Engineer",
            "role": "Engineer",
            "is_active": false,
            "created_at": "2024-01-15T10:30:00"
        }
    """
    logger.info(f"User {current_user.username} deactivating user {user_id}")
    
    # Check admin permission
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to deactivate user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can deactivate users",
        )
    
    # Prevent self-deactivation
    if current_user.id == user_id:
        logger.warning(f"Admin {current_user.username} attempted to deactivate themselves")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    # Deactivate user
    user, error = deactivate_user(db=db, user_id=user_id)
    
    if error:
        logger.warning(f"Failed to deactivate user {user_id}: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    logger.info(f"✅ User deactivated: {user.username}")
    
    return UserResponse.model_validate(user)


# ============================================================================
# REACTIVATE USER - PUT /api/users/{userId}/reactivate (Admin only)
# ============================================================================


@router.put(
    "/{user_id}/reactivate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Reactivate user",
    description="Reactivate a deactivated user account (admin only)",
)
async def reactivate_user_account(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Reactivate a deactivated user account.
    
    Only admins can reactivate users.
    
    Args:
        user_id: User ID
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Updated UserResponse with is_active=True
    
    Raises:
        HTTPException 403: If user is not admin
        HTTPException 404: If user not found
        HTTPException 400: If user already active
    
    Example:
        PUT /api/users/1/reactivate
        
        Response:
        {
            "id": 1,
            "username": "engineer1",
            "email": "engineer@company.com",
            "full_name": "John Engineer",
            "role": "Engineer",
            "is_active": true,
            "created_at": "2024-01-15T10:30:00"
        }
    """
    logger.info(f"User {current_user.username} reactivating user {user_id}")
    
    # Check admin permission
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to reactivate user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reactivate users",
        )
    
    # Reactivate user
    user, error = reactivate_user(db=db, user_id=user_id)
    
    if error:
        logger.warning(f"Failed to reactivate user {user_id}: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    logger.info(f"✅ User reactivated: {user.username}")
    
    return UserResponse.model_validate(user)


# ============================================================================
# ROUTE SUMMARY
# ============================================================================

"""
Users Routes:

1. GET /api/users/me
   - Get current authenticated user's profile
   - Response: UserResponse
   - Status: 200 OK

2. PUT /api/users/me
   - Update current user's profile (full_name only)
   - Body: full_name
   - Response: UserResponse
   - Status: 200 OK

3. GET /api/users
   - List all users (admin only)
   - Query params: skip, limit, role (optional filter)
   - Response: UsersListResponse (users array + total count)
   - Status: 200 OK or 403 Forbidden

4. GET /api/users/{userId}
   - Get user details (admin or self)
   - Params: userId
   - Response: UserResponse
   - Status: 200 OK, 403 Forbidden, or 404 Not Found

5. PUT /api/users/{userId}
   - Update user (admin only)
   - Params: userId
   - Body: full_name, role
   - Response: UserResponse
   - Status: 200 OK, 403 Forbidden, or 404 Not Found

6. DELETE /api/users/{userId}
   - Delete user (admin only, cascade deletes related data)
   - Params: userId
   - Response: None
   - Status: 204 No Content, 403 Forbidden, or 404 Not Found

7. PUT /api/users/{userId}/deactivate
   - Deactivate user account (admin only, soft delete)
   - Params: userId
   - Response: UserResponse with is_active=false
   - Status: 200 OK, 403 Forbidden, or 404 Not Found

8. PUT /api/users/{userId}/reactivate
   - Reactivate user account (admin only)
   - Params: userId
   - Response: UserResponse with is_active=true
   - Status: 200 OK, 403 Forbidden, or 404 Not Found

All endpoints except /users/me and PUT /users/me require admin permission for other users
Authorization: Bearer token in Authorization header
"""