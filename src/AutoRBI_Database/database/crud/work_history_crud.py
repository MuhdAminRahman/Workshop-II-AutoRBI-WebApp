from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Tuple, Optional

from AutoRBI_Database.database.models.work_history import WorkHistory
from AutoRBI_Database.database.models.work import Work
from AutoRBI_Database.database.models.users import User
from AutoRBI_Database.database.models.equipment import Equipment


# ============================================================================
# EXISTING FUNCTIONS (Keep these)
# ============================================================================


def create_history(
    db: Session,
    work_id: int,
    user_id: int,
    action_type: str,
    description: str = None,
    equipment_id: int = None,
 ):
    """Record a new history entry"""

    history = WorkHistory(
        work_id=work_id,
        user_id=user_id,
        equipment_id=equipment_id,
        action_type=action_type,
        description=description,
        timestamp=datetime.utcnow(),
    )

    db.add(history)
    db.flush()  # Assign history_id without committing

    return history


def get_history_for_work(db: Session, work_id: int):
    """Get all history for a work"""
    return (
        db.query(WorkHistory)
        .filter(WorkHistory.work_id == work_id)
        .order_by(WorkHistory.timestamp.desc())
        .all()
    )


def get_history_for_equipment(db: Session, equipment_id: int):
    """Get history for a specific equipment"""
    return (
        db.query(WorkHistory)
        .filter(WorkHistory.equipment_id == equipment_id)
        .order_by(WorkHistory.timestamp.desc())
        .all()
    )


def get_history_for_user(db: Session, user_id: int):
    """Get all actions performed by a specific user"""
    return (
        db.query(WorkHistory)
        .filter(WorkHistory.user_id == user_id)
        .order_by(WorkHistory.timestamp.desc())
        .all()
    )


# ============================================================================
# NEW FUNCTIONS (Add these)
# ============================================================================


def get_paginated_history(
    db: Session,
    user_id: int = None,
    work_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    action_types: List[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[WorkHistory], int]:
    """
    Get paginated work history with filters.

    Args:
        db: Database session
        user_id: Filter by user (for Engineers to see only their work)
        work_id: Filter by specific work
        start_date: Filter entries after this date
        end_date: Filter entries before this date
        action_types: Filter by action types
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (history_entries, total_count)
    """

    # Build base query
    query = db.query(WorkHistory)

    # Apply filters
    filters = []

    if user_id is not None:
        filters.append(WorkHistory.user_id == user_id)

    if work_id is not None:
        filters.append(WorkHistory.work_id == work_id)

    if start_date is not None:
        filters.append(WorkHistory.timestamp >= start_date)

    if end_date is not None:
        filters.append(WorkHistory.timestamp <= end_date)

    if action_types:
        filters.append(WorkHistory.action_type.in_(action_types))

    if filters:
        query = query.filter(and_(*filters))

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    history_entries = (
        query.order_by(WorkHistory.timestamp.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return history_entries, total


def count_history_entries(
    db: Session,
    user_id: int = None,
    work_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    action_types: List[str] = None,
) -> int:
    """Count total history entries matching filters"""

    query = db.query(func.count(WorkHistory.history_id))

    filters = []

    if user_id is not None:
        filters.append(WorkHistory.user_id == user_id)

    if work_id is not None:
        filters.append(WorkHistory.work_id == work_id)

    if start_date is not None:
        filters.append(WorkHistory.timestamp >= start_date)

    if end_date is not None:
        filters.append(WorkHistory.timestamp <= end_date)

    if action_types:
        filters.append(WorkHistory.action_type.in_(action_types))

    if filters:
        query = query.filter(and_(*filters))

    return query.scalar()


def get_history_by_id(db: Session, history_id: int) -> Optional[WorkHistory]:
    """Get single history entry by ID"""

    return db.query(WorkHistory).filter(WorkHistory.history_id == history_id).first()


def get_history_with_details(db: Session, history_id: int) -> Optional[dict]:
    """
    Get history entry with related work, user, equipment details via joins.
    Returns enriched dictionary suitable for details view.
    """

    result = (
        db.query(
            WorkHistory,
            Work.work_name,
            Work.status.label("work_status"),
            Users.username,
            Users.full_name.label("user_full_name"),
            Users.role.label("user_role"),
            Equipment.equipment_no,
            Equipment.pmt_no,
            Equipment.description.label("equipment_description"),
        )
        .join(Work, WorkHistory.work_id == Work.work_id)
        .join(Users, WorkHistory.user_id == Users.user_id)
        .outerjoin(Equipment, WorkHistory.equipment_id == Equipment.equipment_id)
        .filter(WorkHistory.history_id == history_id)
        .first()
    )

    if not result:
        return None

    (
        history,
        work_name,
        work_status,
        username,
        user_full_name,
        user_role,
        equipment_no,
        pmt_no,
        equipment_desc,
    ) = result

    return {
        "id": history.history_id,
        "action_type": history.action_type,
        "description": history.description,
        "timestamp": history.timestamp.isoformat() if history.timestamp else None,
        "work_id": history.work_id,
        "work_name": work_name,
        "work_status": work_status,
        "user_id": history.user_id,
        "username": username,
        "user_full_name": user_full_name,
        "user_role": user_role,
        "equipment_id": history.equipment_id,
        "equipment_no": equipment_no,
        "pmt_no": pmt_no,
        "equipment_description": equipment_desc,
    }


def delete_history(db: Session, history_id: int) -> bool:
    """
    Delete a history entry.

    Returns:
        True if deleted, False if not found
    """

    history = get_history_by_id(db, history_id)

    if not history:
        return False

    db.delete(history)
    db.flush()

    return True


def get_work_statistics(db: Session, work_id: int) -> dict:
    """
    Get statistics for a work (total actions, action breakdown, etc.)
    """

    # Total actions
    total_actions = (
        db.query(func.count(WorkHistory.history_id))
        .filter(WorkHistory.work_id == work_id)
        .scalar()
    )

    # Actions by type
    action_breakdown = (
        db.query(
            WorkHistory.action_type, func.count(WorkHistory.history_id).label("count")
        )
        .filter(WorkHistory.work_id == work_id)
        .group_by(WorkHistory.action_type)
        .all()
    )

    # First and last action timestamps
    timestamps = (
        db.query(
            func.min(WorkHistory.timestamp).label("first_action"),
            func.max(WorkHistory.timestamp).label("last_action"),
        )
        .filter(WorkHistory.work_id == work_id)
        .first()
    )

    return {
        "total_actions": total_actions,
        "action_breakdown": {action: count for action, count in action_breakdown},
        "first_action": (
            timestamps.first_action.isoformat() if timestamps.first_action else None
        ),
        "last_action": (
            timestamps.last_action.isoformat() if timestamps.last_action else None
        ),
    }
