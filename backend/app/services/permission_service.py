"""
Permission Service - Centralized access control for work collaboration
WITH ADMIN OVERRIDE
"""

import logging
from enum import Enum
from sqlalchemy.orm import Session

from app.models.work_collaborator import WorkCollaborator, CollaboratorRole
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for work access"""
    NONE = 0
    VIEWER = 1
    EDITOR = 2
    OWNER = 3


def get_user_permission(db: Session, work_id: int, user_id: int) -> PermissionLevel:
    """
    Get user's permission level for a work.
    
    ✓ FIXED: Admins get OWNER level automatically
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID
    
    Returns:
        PermissionLevel (NONE, VIEWER, EDITOR, or OWNER)
    
    Example:
        perm = get_user_permission(db=db, work_id=1, user_id=5)
        if perm == PermissionLevel.OWNER:
            print("User is owner")
    """
    # ✓ FIXED: Check if user is admin first (admin override)
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.role == UserRole.ADMIN:
        logger.debug(f"Admin user {user_id} has OWNER permission on all works")
        return PermissionLevel.OWNER
    
    collaborator = db.query(WorkCollaborator).filter(
        WorkCollaborator.work_id == work_id,
        WorkCollaborator.user_id == user_id
    ).first()
    
    if not collaborator:
        return PermissionLevel.NONE
    
    role_map = {
        CollaboratorRole.OWNER: PermissionLevel.OWNER,
        CollaboratorRole.EDITOR: PermissionLevel.EDITOR,
        CollaboratorRole.VIEWER: PermissionLevel.VIEWER,
    }
    
    return role_map.get(collaborator.role, PermissionLevel.NONE)


def require_permission(
    db: Session,
    work_id: int,
    user_id: int,
    min_level: PermissionLevel
) -> bool:
    """
    Check if user has minimum required permission.
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID
        min_level: Minimum permission level required
    
    Returns:
        True if user has sufficient permission, False otherwise
    
    Example:
        if require_permission(db, work_id=1, user_id=5, min_level=PermissionLevel.EDITOR):
            print("User can edit")
    """
    user_level = get_user_permission(db, work_id, user_id)
    return user_level.value >= min_level.value


def can_view(db: Session, work_id: int, user_id: int) -> bool:
    """
    Check if user can view a work.
    Required for: GET endpoints
    
    ✓ Admins can always view
    """
    return require_permission(db, work_id, user_id, PermissionLevel.VIEWER)


def can_edit(db: Session, work_id: int, user_id: int) -> bool:
    """
    Check if user can edit a work (create/update equipment, files, extractions).
    Required for: POST/PUT endpoints for content
    
    ✓ Admins can always edit
    """
    return require_permission(db, work_id, user_id, PermissionLevel.EDITOR)


def can_own(db: Session, work_id: int, user_id: int) -> bool:
    """
    Check if user is owner (can delete, manage collaborators).
    Required for: DELETE endpoints, collaboration management
    
    ✓ Admins are considered owners of all works
    """
    return require_permission(db, work_id, user_id, PermissionLevel.OWNER)


def get_work_owner_id(db: Session, work_id: int) -> int:
    """
    Get the owner ID of a work.
    
    Args:
        db: Database session
        work_id: Work ID
    
    Returns:
        Owner user ID, or None if no owner found
    
    Example:
        owner_id = get_work_owner_id(db=db, work_id=1)
    """
    collaborator = db.query(WorkCollaborator).filter(
        WorkCollaborator.work_id == work_id,
        WorkCollaborator.role == CollaboratorRole.OWNER
    ).first()
    
    return collaborator.user_id if collaborator else None


def get_owner_count(db: Session, work_id: int) -> int:
    """
    Get count of owners for a work.
    
    Args:
        db: Database session
        work_id: Work ID
    
    Returns:
        Number of owners
    
    Example:
        if get_owner_count(db=db, work_id=1) == 1:
            print("Single owner - cannot be removed")
    """
    return db.query(WorkCollaborator).filter(
        WorkCollaborator.work_id == work_id,
        WorkCollaborator.role == CollaboratorRole.OWNER
    ).count()


def get_work_collaborators(db: Session, work_id: int) -> list:
    """
    Get all collaborators for a work.
    
    Args:
        db: Database session
        work_id: Work ID
    
    Returns:
        List of WorkCollaborator objects
    """
    return db.query(WorkCollaborator).filter(
        WorkCollaborator.work_id == work_id
    ).all()


def is_admin(db: Session, user_id: int) -> bool:
    """
    Check if user is an admin.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        True if user is admin, False otherwise
    """
    user = db.query(User).filter(User.id == user_id).first()
    return user and user.role == UserRole.ADMIN