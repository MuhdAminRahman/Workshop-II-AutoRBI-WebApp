"""
Work History Service - Business logic for work history operations.

This layer handles:
- Permission checking (can user view this history?)
- Data transformation (DB models → UI dictionaries)
- Business logic (filtering, pagination, statistics)
- Exception handling and logging
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text 

from AutoRBI_Database.logging_config import get_logger
from AutoRBI_Database.database.crud.work_history_crud import (
    get_paginated_history,
    count_history_entries,
    get_history_by_id,
    get_history_with_details,
    delete_history,
    get_work_statistics,
)
from AutoRBI_Database.exceptions import (
    UserNotFoundError,
    ValidationError,
    DatabaseError,
    UnauthorizedAccessError,
)

logger = get_logger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def history_to_dict(history) -> dict:
    """
    Convert WorkHistory object to dictionary for UI.

    Args:
        history: WorkHistory model object

    Returns:
        Dictionary with history data formatted for UI
    """
    return {
        "id": history.history_id,
        "work_id": history.work_id,
        "user_id": history.user_id,
        "equipment_id": history.equipment_id,
        "equipment_name": "-",  # Default value, will be populated if available
        "action_type": history.action_type,
        "description": history.description or "-",
        "timestamp": (
            history.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if history.timestamp
            else "-"
        ),
        "date": history.timestamp.strftime("%Y-%m-%d") if history.timestamp else "-",
        "time": history.timestamp.strftime("%H:%M:%S") if history.timestamp else "-",
    }


def calculate_date_range(period: str) -> tuple:
    """
    Convert period string to date range (start_date, end_date).

    Args:
        period: One of "all", "today", "last_7_days", "last_month"

    Returns:
        Tuple of (start_date, end_date) as datetime objects
        Returns (None, None) for "all"
    """

    now = datetime.utcnow()

    if period == "all":
        return None, None

    elif period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    elif period == "last_7_days":
        start = now - timedelta(days=7)
        return start, now

    elif period == "last_month":
        start = now - timedelta(days=30)
        return start, now

    else:
        # Default to all if unknown period
        logger.warning(f"Unknown period filter: {period}, defaulting to 'all'")
        return None, None


def check_view_permission(current_user: dict, work_id: int, db: Session) -> None:
    """
    Check if user has permission to view work history.

    Args:
        current_user: The logged-in user's session data
        work_id: The work ID to check permission for
        db: Database session

    Raises:
        UnauthorizedAccessError: If user doesn't have permission
    """
    from AutoRBI_Database.database.crud.work_crud import get_work_by_id

    # Admin can view all
    if current_user.get("role") == "Admin":
        return

    # Engineers can only view their assigned work
    work = get_work_by_id(db, work_id)

    if not work:
        raise ValidationError(f"Work with ID {work_id} not found")

    # TODO: Add logic to check if work is assigned to user's group
    # For now, allow all Engineers to view all work
    # This should be updated based on your work assignment logic

    logger.info(
        f"Permission check passed for user {current_user.get('username')} on work {work_id}"
    )


# ============================================================================
# SERVICE FUNCTIONS
# ============================================================================


def get_work_history(
    db: Session,
    current_user: dict,
    period: str = "all",
    work_id: int = None,
    page: int = 1,
    per_page: int = 20,
) -> Dict[str, Any]:
    """
    Get paginated work history with filters.

    Args:
        db: Database session
        current_user: Current user session data
        period: Time period filter ("all", "today", "last_7_days", "last_month")
        work_id: Optional work ID to filter by
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        {
            "success": bool,
            "data": List[dict],  # List of history entries
            "pagination": {
                "page": int,
                "per_page": int,
                "total": int,
                "total_pages": int
            }
        }
    """

    try:
        # 1. Permission check
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")

        if not user_id:
            raise ValidationError("User ID not found in session")

        # Engineers can only see their assigned work (filter by user_id)
        # Admins can see all work (no user_id filter)
        filter_user_id = None if user_role == "Admin" else user_id

        logger.info(
            f"Loading work history for user {current_user.get('username')} "
            f"(role: {user_role}, period: {period}, page: {page})"
        )

        # 2. Calculate date range from period
        start_date, end_date = calculate_date_range(period)

        # 3. Get paginated data from CRUD
        history_entries, total = get_paginated_history(
            db=db,
            user_id=filter_user_id,
            work_id=work_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            per_page=per_page,
        )

        # 4. Transform to UI format
        history_data = []
        for entry in history_entries:
            item = history_to_dict(entry)

            # Try to extract equipment name from description
            equipment_name = "-"

            # First, try to get from equipment_id if it exists
            if entry.equipment_id:
                try:
                    result = db.execute(
                        text("SELECT equipment_no FROM equipment WHERE equipment_id = :eq_id"),
                        {"eq_id": entry.equipment_id},
                    ).fetchone()

                    if result:
                        equipment_name = result[0]
                except Exception as e:
                    logger.warning(
                        f"Could not fetch equipment name for equipment_id {entry.equipment_id}: {e}"
                    )

            # If still not found, try to extract from description
            if equipment_name == "-" and entry.description:
                import re

                # Pattern to match equipment codes like H-001, V-006, etc.
                match = re.search(r"([A-Z]-\d{3})", entry.description)
                if match:
                    equipment_name = match.group(1)

            item["equipment_name"] = equipment_name
            history_data.append(item)

        # 5. Calculate pagination info
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1

        # 6. Log success
        logger.info(
            f"Retrieved {len(history_data)} work history entries "
            f"for user {current_user.get('username')} (page {page}/{total_pages})"
        )

        # 7. Return structured response
        return {
            "success": True,
            "data": history_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }

    except UnauthorizedAccessError as e:
        logger.warning(f"Unauthorized access attempt: {e}")
        return {"success": False, "message": str(e), "error_type": "UNAUTHORIZED"}

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return {"success": False, "message": str(e), "error_type": "VALIDATION_ERROR"}

    except Exception as e:
        logger.error(f"Error retrieving work history: {e}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to retrieve work history. Please try again.",
            "error_type": "DATABASE_ERROR",
        }


def get_history_details(
    db: Session, current_user: dict, history_id: int
) -> Dict[str, Any]:
    """
    Get detailed information about a single history entry.

    Args:
        db: Database session
        current_user: Current user session data
        history_id: ID of the history entry

    Returns:
        {
            "success": bool,
            "data": dict,  # Detailed history information
            "message": str (optional error message)
        }
    """

    try:
        logger.info(
            f"Loading history details for ID {history_id} "
            f"by user {current_user.get('username')}"
        )

        # Get detailed history with joins
        details = get_history_with_details(db, history_id)

        if not details:
            logger.warning(f"History entry {history_id} not found")
            return {
                "success": False,
                "message": f"History entry with ID {history_id} not found",
            }

        # Permission check: Engineers can only view their own work history
        if current_user.get("role") != "Admin":
            if details["user_id"] != current_user.get("user_id"):
                logger.warning(
                    f"User {current_user.get('username')} attempted to view "
                    f"history entry {history_id} belonging to another user"
                )
                return {
                    "success": False,
                    "message": "You don't have permission to view this history entry",
                }

        logger.info(f"Successfully retrieved details for history {history_id}")

        return {"success": True, "data": details}

    except Exception as e:
        logger.error(f"Error retrieving history details: {e}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to retrieve history details. Please try again.",
        }


def delete_work_history(
    db: Session, current_user: dict, history_id: int
) -> Dict[str, Any]:
    """
    Delete or archive a work history entry.

    Args:
        db: Database session
        current_user: Current user session data
        history_id: ID of the history entry to delete

    Returns:
        {
            "success": bool,
            "message": str
        }
    """

    try:
        logger.info(
            f"Deleting history entry {history_id} "
            f"by user {current_user.get('username')}"
        )

        # Get the history entry first
        history = get_history_by_id(db, history_id)

        if not history:
            logger.warning(f"History entry {history_id} not found")
            return {
                "success": False,
                "message": f"History entry with ID {history_id} not found",
            }

        # Permission check: Only Admin can delete, or user can delete their own entries
        user_role = current_user.get("role")
        user_id = current_user.get("user_id")

        if user_role != "Admin" and history.user_id != user_id:
            logger.warning(
                f"User {current_user.get('username')} attempted to delete "
                f"history entry {history_id} belonging to another user"
            )
            return {
                "success": False,
                "message": "You don't have permission to delete this history entry",
            }

        # Perform deletion
        deleted = delete_history(db, history_id)

        if deleted:
            db.commit()
            logger.info(f"Successfully deleted history entry {history_id}")
            return {"success": True, "message": "History entry deleted successfully"}
        else:
            logger.error(f"Failed to delete history entry {history_id}")
            return {"success": False, "message": "Failed to delete history entry"}

    except Exception as e:
        logger.error(f"Error deleting history entry: {e}", exc_info=True)
        db.rollback()
        return {
            "success": False,
            "message": "Failed to delete history entry. Please try again.",
        }


def get_work_summary(db: Session, current_user: dict, work_id: int) -> Dict[str, Any]:
    """
    Get summary statistics for a work.

    Args:
        db: Database session
        current_user: Current user session data
        work_id: ID of the work

    Returns:
        {
            "success": bool,
            "data": dict,  # Statistics about the work
            "message": str (optional error message)
        }
    """

    try:
        logger.info(
            f"Loading work summary for work {work_id} "
            f"by user {current_user.get('username')}"
        )

        # Get statistics
        stats = get_work_statistics(db, work_id)

        logger.info(f"Successfully retrieved summary for work {work_id}")

        return {"success": True, "data": stats}

    except Exception as e:
        logger.error(f"Error retrieving work summary: {e}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to retrieve work summary. Please try again.",
        }
