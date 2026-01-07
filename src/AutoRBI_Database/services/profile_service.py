"""
Profile Service - Business logic for user profile operations.

This service handles:
- Profile information updates (full name, email)
- Password changes with current password verification
- Converting exceptions to structured responses
"""

from sqlalchemy.orm import Session
from typing import Dict, Any

from AutoRBI_Database.logging_config import get_logger
from AutoRBI_Database.database.crud.user_crud import (
    get_user_by_id,
    update_user_profile_data,
    change_user_password,
    verify_current_password,
)
from AutoRBI_Database.exceptions import (
    UserNotFoundError,
    ValidationError,
    DatabaseError,
    CurrentPasswordIncorrectError,
    EmailAlreadyInUseError,
)


# Initialize logger for this module
logger = get_logger(__name__)


def update_profile(
    db: Session, user_id: int, full_name: str = None, email: str = None
) -> Dict[str, Any]:
    """
    Update user's profile information.

    Args:
        db: Database session
        user_id: ID of the user updating their profile
        full_name: New full name (None = don't change)
        email: New email (None = don't change)

    Returns:
        {
            "success": True/False,
            "message": "...",
            "user": {...}  # Updated user data
        }
    """
    try:
        # Update profile
        updated_user = update_user_profile_data(
            db, user_id=user_id, full_name=full_name, email=email
        )

        logger.info(f"Profile updated for user: {updated_user.username}")

        return {
            "success": True,
            "message": "Profile updated successfully.",
            "user": {
                "id": updated_user.user_id,
                "username": updated_user.username,
                "full_name": updated_user.full_name,
                "email": updated_user.email,
                "role": updated_user.role,
            },
        }

    except UserNotFoundError as e:
        logger.error(f"User not found during profile update: {e}")
        return {
            "success": False,
            "message": str(e),
            "error_type": "not_found",
        }
    except ValidationError as e:
        logger.warning(f"Validation error during profile update: {e}")
        return {
            "success": False,
            "message": str(e),
            "error_type": "validation",
        }
    except EmailAlreadyInUseError as e:
        logger.warning(f"Email already in use: {e}")
        return {
            "success": False,
            "message": str(e),
            "error_type": "email_taken",
        }
    except DatabaseError as e:
        logger.error(f"Database error during profile update: {e}")
        return {
            "success": False,
            "message": "Unable to update profile. Please try again.",
            "error_type": "system",
        }


def change_password(
    db: Session, user_id: int, current_password: str, new_password: str
) -> Dict[str, Any]:
    """
    Change user's password.

    Args:
        db: Database session
        user_id: ID of the user changing their password
        current_password: Current password for verification
        new_password: New password to set

    Returns:
        {
            "success": True/False,
            "message": "...",
        }
    """
    try:
        # Change password (includes verification of current password)
        change_user_password(
            db,
            user_id=user_id,
            current_password=current_password,
            new_password=new_password,
        )

        logger.info(f"Password changed for user ID: {user_id}")

        return {
            "success": True,
            "message": "Password changed successfully.",
        }

    except UserNotFoundError as e:
        logger.error(f"User not found during password change: {e}")
        return {
            "success": False,
            "message": str(e),
            "error_type": "not_found",
        }
    except CurrentPasswordIncorrectError as e:
        logger.warning(f"Incorrect current password: {e}")
        return {
            "success": False,
            "message": "Current password is incorrect.",
            "error_type": "wrong_password",
        }
    except ValidationError as e:
        logger.warning(f"Validation error during password change: {e}")
        return {
            "success": False,
            "message": str(e),
            "error_type": "validation",
        }
    except DatabaseError as e:
        logger.error(f"Database error during password change: {e}")
        return {
            "success": False,
            "message": "Unable to change password. Please try again.",
            "error_type": "system",
        }


def get_profile(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Get user's profile information.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        {
            "success": True/False,
            "user": {...}
        }
    """
    try:
        user = get_user_by_id(db, user_id)

        return {
            "success": True,
            "user": {
                "id": user.user_id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        }

    except UserNotFoundError as e:
        return {
            "success": False,
            "message": str(e),
            "error_type": "not_found",
        }
    except DatabaseError as e:
        logger.error(f"Database error fetching profile: {e}")
        return {
            "success": False,
            "message": "Unable to load profile.",
            "error_type": "system",
        }
