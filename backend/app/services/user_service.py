"""
User Service
Business logic for user management and CRUD operations
"""

import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

# ============================================================================
# GET USER
# ============================================================================


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get user by ID.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        User object or None if not found
    
    Example:
        user = get_user_by_id(db=db, user_id=1)
        if user:
            print(f"Found: {user.full_name}")
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning(f"User not found: ID {user_id}")
            return None
        
        logger.debug(f"Retrieved user: {user.username} (ID: {user.id})")
        
        return user
    
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}")
        return None


# ============================================================================
# LIST USERS
# ============================================================================


def list_all_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
) -> Tuple[List[User], int]:
    """
    List all users with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum records to return (pagination)
        role: Optional filter by role (Engineer, Admin)
    
    Returns:
        (List of User objects, total count)
    
    Example:
        users, total = list_all_users(db=db, skip=0, limit=10)
        users, total = list_all_users(db=db, role="Engineer")
    """
    try:
        query = db.query(User)
        
        # Apply role filter if provided
        if role:
            try:
                role_enum = UserRole[role.upper()]
                query = query.filter(User.role == role_enum)
            except KeyError:
                logger.warning(f"Invalid role filter: {role}")
        
        total = query.count()
        
        users = query.offset(skip).limit(limit).all()
        
        logger.debug(f"Listed {len(users)} users (total: {total})")
        
        return users, total
    
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return [], 0


# ============================================================================
# UPDATE USER
# ============================================================================


def update_user(
    db: Session,
    user_id: int,
    full_name: Optional[str] = None,
    role: Optional[str] = None,
) -> Tuple[Optional[User], Optional[str]]:
    """
    Update user details.
    
    Args:
        db: Database session
        user_id: User ID
        full_name: New full name (optional)
        role: New role (Engineer, Admin) (optional)
    
    Returns:
        (Updated User object, error_message)
        If successful: (user, None)
        If failed: (None, error_message)
    
    Example:
        user, error = update_user(
            db=db,
            user_id=1,
            full_name="John Updated",
            role="Admin"
        )
        if error:
            print(f"Update failed: {error}")
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None, f"User not found: {user_id}"
        
        # Update full_name if provided
        if full_name is not None:
            user.full_name = full_name
        
        # Update role if provided
        if role is not None:
            try:
                role_enum = UserRole[role.upper()]
                user.role = role_enum
            except KeyError:
                return None, f"Invalid role: {role}. Must be 'Engineer' or 'Admin'"
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ User updated: {user.username} (ID: {user.id})")
        
        return user, None
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user {user_id}: {str(e)}")
        return None, f"Failed to update user: {str(e)}"


# ============================================================================
# DELETE USER
# ============================================================================


def delete_user(db: Session, user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Delete a user and all related data.
    
    Cascade deletes:
    - Works (owned by user)
    - Equipment (related to works)
    - Components (related to equipment)
    - Extractions (related to works)
    - Files (created by user)
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        (success: bool, error_message)
        If successful: (True, None)
        If failed: (False, error_message)
    
    Example:
        success, error = delete_user(db=db, user_id=1)
        if success:
            print("User deleted")
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False, f"User not found: {user_id}"
        
        username = user.username
        
        # Cascade delete is handled by SQLAlchemy relationships
        # User.works has cascade="all, delete-orphan"
        # Work.equipment has cascade="all, delete-orphan"
        # Equipment.components has cascade="all, delete-orphan"
        # etc.
        db.delete(user)
        db.commit()
        
        logger.info(f"✅ User deleted: {username} (ID: {user_id})")
        
        return True, None
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return False, f"Failed to delete user: {str(e)}"


# ============================================================================
# DEACTIVATE USER
# ============================================================================


def deactivate_user(db: Session, user_id: int) -> Tuple[Optional[User], Optional[str]]:
    """
    Deactivate a user account (soft delete).
    
    User data is preserved, but account cannot be used for login.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        (Updated User object, error_message)
        If successful: (user, None)
        If failed: (None, error_message)
    
    Example:
        user, error = deactivate_user(db=db, user_id=1)
        if error:
            print(f"Deactivation failed: {error}")
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None, f"User not found: {user_id}"
        
        if not user.is_active:
            return None, f"User is already deactivated"
        
        user.is_active = False
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ User deactivated: {user.username} (ID: {user_id})")
        
        return user, None
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating user {user_id}: {str(e)}")
        return None, f"Failed to deactivate user: {str(e)}"


# ============================================================================
# REACTIVATE USER
# ============================================================================


def reactivate_user(db: Session, user_id: int) -> Tuple[Optional[User], Optional[str]]:
    """
    Reactivate a deactivated user account.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        (Updated User object, error_message)
        If successful: (user, None)
        If failed: (None, error_message)
    
    Example:
        user, error = reactivate_user(db=db, user_id=1)
        if error:
            print(f"Reactivation failed: {error}")
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None, f"User not found: {user_id}"
        
        if user.is_active:
            return None, f"User is already active"
        
        user.is_active = True
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ User reactivated: {user.username} (ID: {user_id})")
        
        return user, None
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error reactivating user {user_id}: {str(e)}")
        return None, f"Failed to reactivate user: {str(e)}"


# ============================================================================
# VERIFY USER OWNERSHIP (utility for other services)
# ============================================================================


def verify_user_exists(db: Session, user_id: int) -> bool:
    """
    Check if a user exists.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        True if user exists, False otherwise
    
    Example:
        if verify_user_exists(db=db, user_id=1):
            print("User exists")
    """
    user = db.query(User).filter(User.id == user_id).first()
    return user is not None


# ============================================================================
# GET USER BY USERNAME
# ============================================================================


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get user by username.
    
    Used by auth service.
    
    Args:
        db: Database session
        username: Username
    
    Returns:
        User object or None if not found
    
    Example:
        user = get_user_by_username(db=db, username="engineer1")
    """
    try:
        user = db.query(User).filter(User.username == username).first()
        return user
    except Exception as e:
        logger.error(f"Error fetching user by username {username}: {str(e)}")
        return None


# ============================================================================
# GET USER BY EMAIL
# ============================================================================


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get user by email.
    
    Used by auth service.
    
    Args:
        db: Database session
        email: User email
    
    Returns:
        User object or None if not found
    
    Example:
        user = get_user_by_email(db=db, email="engineer@company.com")
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        return user
    except Exception as e:
        logger.error(f"Error fetching user by email {email}: {str(e)}")
        return None