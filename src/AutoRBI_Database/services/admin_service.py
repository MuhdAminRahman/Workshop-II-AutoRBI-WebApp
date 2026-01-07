"""
Admin Service - Business logic for admin operations.

This layer handles:
- Permission checking (is user an admin?)
- Safety validations (can't deactivate last admin)
- Converting exceptions to structured responses
- Logging for audit trail
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List

from AutoRBI_Database.logging_config import get_logger
from AutoRBI_Database.database.crud.user_crud import (
    get_all_users,
    get_user_by_id,
    update_user_details,
    update_user_status,
    reset_user_password,
    create_user_by_admin,
    count_users,
    count_active_admins,
)
from AutoRBI_Database.exceptions import (
    UserNotFoundError,
    ValidationError,
    AccountAlreadyExistsError,
    DatabaseError,
    UnauthorizedAccessError,
    CannotModifySelfError,
    LastAdminError,
)


# Initialize logger for this module
logger = get_logger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def check_admin_permission(current_user: dict) -> None:
    """
    Verify that the current user is an admin.

    Args:
        current_user: The logged-in user's session data

    Raises:
        UnauthorizedAccessError: If user is not an admin
    """
    if current_user.get("role") != "Admin":
        logger.warning(
            f"Unauthorized admin access attempt by: {current_user.get('username')}"
        )
        raise UnauthorizedAccessError("Only administrators can perform this action")


def user_to_dict(user) -> dict:
    """
    Convert User object to dictionary for UI.

    Args:
        user: User model object

    Returns:
        Dictionary with user data
    """
    return {
        "id": user.user_id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "status": user.status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ============================================================================
# SERVICE FUNCTIONS
# ============================================================================


def get_users(
    db: Session,
    current_user: dict,
    status_filter: str = None,
    role_filter: str = None,
    search_query: str = None,
    page: int = 1,
    per_page: int = 20,
) -> Dict[str, Any]:
    """
    Get paginated list of users.

    Args:
        db: Database session
        current_user: The logged-in user's session data
        status_filter: "Active" or "Inactive" (None = all)
        role_filter: "Admin" or "Engineer" (None = all)
        search_query: Search term for username/full_name
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        {
            "success": True,
            "users": [...],
            "total": 50,
            "page": 1,
            "per_page": 20,
            "total_pages": 3
        }
    """
    try:
        # Check permission
        check_admin_permission(current_user)

        # Calculate pagination offset
        skip = (page - 1) * per_page

        # Get users from database
        users = get_all_users(
            db,
            status_filter=status_filter,
            role_filter=role_filter,
            search_query=search_query,
            skip=skip,
            limit=per_page,
        )

        # Get total count for pagination
        total = count_users(db, status_filter, role_filter, search_query)
        total_pages = (total + per_page - 1) // per_page  # Ceiling division

        # Convert User objects to dictionaries
        user_list = [user_to_dict(u) for u in users]

        logger.info(
            f"Admin {current_user.get('username')} fetched users list (page {page})"
        )

        return {
            "success": True,
            "users": user_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }

    except UnauthorizedAccessError as e:
        return {
            "success": False,
            "message": str(e),
            "error_type": "unauthorized",
        }
    except ValidationError as e:
        return {
            "success": False,
            "message": str(e),
            "error_type": "validation",
        }
    except DatabaseError as e:
        logger.error(f"Database error in get_users: {e}")
        return {
            "success": False,
            "message": "Unable to retrieve users. Please try again.",
            "error_type": "system",
        }


def toggle_user_status(
    db: Session, current_user: dict, target_user_id: int
) -> Dict[str, Any]:
    """
    Toggle user between Active and Inactive.

    Safety checks:
    - Current user must be admin
    - Cannot deactivate yourself
    - Cannot deactivate the last active admin

    Args:
        db: Database session
        current_user: The logged-in admin's session data
        target_user_id: ID of user to toggle

    Returns:
        Success/failure response dict
    """
    try:
        # Check permission
        check_admin_permission(current_user)

        # Get target user
        target_user = get_user_by_id(db, target_user_id)

        # Safety: Can't modify yourself
        if target_user.user_id == current_user.get("id"):
            raise CannotModifySelfError("You cannot change your own account status")

        # Determine new status (toggle)
        new_status = "Inactive" if target_user.status == "Active" else "Active"

        # Safety: Can't deactivate last admin
        if new_status == "Inactive" and target_user.role == "Admin":
            active_admins = count_active_admins(db)
            if active_admins <= 1:
                raise LastAdminError("Cannot deactivate the last active administrator")

        # Perform the update
        updated_user = update_user_status(db, target_user_id, new_status)

        action = "activated" if new_status == "Active" else "deactivated"
        logger.info(
            f"Admin {current_user.get('username')} {action} user {target_user.username}"
        )

        return {
            "success": True,
            "message": f"User '{updated_user.username}' has been {action}.",
            "user": user_to_dict(updated_user),
        }

    except UnauthorizedAccessError as e:
        return {"success": False, "message": str(e), "error_type": "unauthorized"}
    except CannotModifySelfError as e:
        return {"success": False, "message": str(e), "error_type": "validation"}
    except LastAdminError as e:
        return {"success": False, "message": str(e), "error_type": "validation"}
    except UserNotFoundError as e:
        return {"success": False, "message": str(e), "error_type": "not_found"}
    except DatabaseError as e:
        logger.error(f"Database error in toggle_user_status: {e}")
        return {
            "success": False,
            "message": "Operation failed. Please try again.",
            "error_type": "system",
        }


def modify_user(
    db: Session,
    current_user: dict,
    target_user_id: int,
    full_name: str = None,
    role: str = None,
    new_password: str = None,
) -> Dict[str, Any]:
    """
    Modify user details (admin action).

    Safety checks:
    - Cannot demote yourself from Admin
    - Cannot demote the last admin

    Args:
        db: Database session
        current_user: The logged-in admin's session data
        target_user_id: ID of user to modify
        full_name: New full name (None = don't change)
        role: New role (None = don't change)
        new_password: New password (None = don't change)

    Returns:
        Success/failure response dict
    """
    try:
        # Check permission
        check_admin_permission(current_user)

        # Get target user
        target_user = get_user_by_id(db, target_user_id)

        # Safety: Can't demote yourself
        if target_user.user_id == current_user.get("id"):
            if role is not None and role != "Admin":
                raise CannotModifySelfError("You cannot demote your own account")

        # Safety: Can't demote last admin
        if target_user.role == "Admin" and role == "Engineer":
            active_admins = count_active_admins(db)
            if active_admins <= 1:
                raise LastAdminError("Cannot demote the last administrator")

        # Update user details if provided
        if full_name is not None or role is not None:
            update_user_details(db, target_user_id, full_name=full_name, role=role)

        # Reset password if provided
        if new_password is not None:
            reset_user_password(db, target_user_id, new_password)

        # Get fresh user data
        updated_user = get_user_by_id(db, target_user_id)

        logger.info(
            f"Admin {current_user.get('username')} modified user {updated_user.username}"
        )

        return {
            "success": True,
            "message": f"User '{updated_user.username}' has been updated.",
            "user": user_to_dict(updated_user),
        }

    except UnauthorizedAccessError as e:
        return {"success": False, "message": str(e), "error_type": "unauthorized"}
    except (CannotModifySelfError, LastAdminError) as e:
        return {"success": False, "message": str(e), "error_type": "validation"}
    except ValidationError as e:
        return {"success": False, "message": str(e), "error_type": "validation"}
    except UserNotFoundError as e:
        return {"success": False, "message": str(e), "error_type": "not_found"}
    except DatabaseError as e:
        logger.error(f"Database error in modify_user: {e}")
        return {
            "success": False,
            "message": "Operation failed. Please try again.",
            "error_type": "system",
        }


def add_user(
    db: Session,
    current_user: dict,
    username: str,
    full_name: str,
    password: str,
    role: str = "Engineer",
) -> Dict[str, Any]:
    """
    Create a new user (admin action).

    Args:
        db: Database session
        current_user: The logged-in admin's session data
        username: New user's username
        full_name: New user's full name
        password: New user's password
        role: "Admin" or "Engineer"

    Returns:
        Success/failure response dict
    """
    try:
        # Check permission
        check_admin_permission(current_user)

        # Create the user
        new_user = create_user_by_admin(
            db, username=username, full_name=full_name, password=password, role=role
        )

        logger.info(
            f"Admin {current_user.get('username')} created user {new_user.username}"
        )

        return {
            "success": True,
            "message": f"User '{new_user.username}' has been created successfully.",
            "user": user_to_dict(new_user),
        }

    except UnauthorizedAccessError as e:
        return {"success": False, "message": str(e), "error_type": "unauthorized"}
    except AccountAlreadyExistsError as e:
        return {"success": False, "message": str(e), "error_type": "account_exists"}
    except ValidationError as e:
        return {"success": False, "message": str(e), "error_type": "validation"}
    except DatabaseError as e:
        logger.error(f"Database error in add_user: {e}")
        return {
            "success": False,
            "message": "Operation failed. Please try again.",
            "error_type": "system",
        }
