"""
Work Service - Updated for multi-user collaboration
Business logic for work project management
"""

import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.work import Work, WorkStatus
from app.models.work_collaborator import WorkCollaborator, CollaboratorRole
from app.models.equipment import Equipment
from app.models.file import File
from app.services.permission_service import (
    can_edit,
    can_own,
    get_owner_count,
    PermissionLevel,
)

logger = logging.getLogger(__name__)

# ============================================================================
# CREATE WORK
# ============================================================================


def create_work(
    db: Session,
    user_id: int,
    name: str,
    description: Optional[str] = None,
) -> Tuple[Optional[Work], Optional[str]]:
    """
    Create a new work project.
    Creator automatically becomes owner.
    
    Args:
        db: Database session
        user_id: Creator/owner user ID
        name: Project name
        description: Optional description
    
    Returns:
        (Work object, error_message)
        If successful: (work, None)
        If failed: (None, error_message)
    
    Example:
        work, error = create_work(
            db=db,
            user_id=1,
            name="Refinery Unit A",
            description="Extract equipment data"
        )
    """
    try:
        new_work = Work(
            name=name,
            description=description,
            status=WorkStatus.ACTIVE,
        )
        
        db.add(new_work)
        db.flush()
        
        # Creator becomes owner automatically
        owner_collaborator = WorkCollaborator(
            work_id=new_work.id,
            user_id=user_id,
            role=CollaboratorRole.OWNER
        )
        db.add(owner_collaborator)
        db.commit()
        db.refresh(new_work)
        
        logger.info(f"✅ Work created: {name} (ID: {new_work.id}) by user {user_id}")
        
        return new_work, None
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create work: {str(e)}")
        return None, f"Failed to create work: {str(e)}"


# ============================================================================
# GET WORK
# ============================================================================


def get_work_by_id(
    db: Session,
    work_id: int,
) -> Optional[Work]:
    """
    Get work by ID (no permission check - permission checked by caller).
    
    Args:
        db: Database session
        work_id: Work ID
    
    Returns:
        Work object or None if not found
    
    Example:
        work = get_work_by_id(db=db, work_id=1)
    """
    work = db.query(Work).filter(Work.id == work_id).first()
    
    if not work:
        logger.debug(f"Work not found: ID {work_id}")
        return None
    
    return work


# ============================================================================
# LIST WORKS
# ============================================================================


def list_works_for_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[Work], int]:
    """
    List all works for a user (works they collaborate on).
    
    Args:
        db: Database session
        user_id: User ID
        skip: Number of records to skip (pagination)
        limit: Maximum records to return (pagination)
    
    Returns:
        (List of Work objects, total count)
    
    Example:
        works, total = list_works_for_user(db=db, user_id=1, skip=0, limit=10)
    """
    query = db.query(Work).join(WorkCollaborator).filter(
        WorkCollaborator.user_id == user_id
    ).distinct()
    
    total = query.count()
    
    works = query.offset(skip).limit(limit).all()
    
    logger.debug(f"Listed {len(works)} works for user {user_id}")
    
    return works, total


# ============================================================================
# UPDATE WORK
# ============================================================================


def update_work(
    db: Session,
    work_id: int,
    user_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[Optional[Work], Optional[str]]:
    """
    Update a work project.
    Requires edit permission.
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID (permission check)
        name: New name (optional)
        description: New description (optional)
        status: New status (optional)
    
    Returns:
        (Updated Work object, error_message)
        If successful: (work, None)
        If failed: (None, error_message)
    
    Example:
        work, error = update_work(
            db=db,
            work_id=1,
            user_id=1,
            status="completed"
        )
    """
    work = get_work_by_id(db=db, work_id=work_id)
    
    if not work:
        return None, "Work not found"
    
    # ✅ NEW: Permission check
    if not can_edit(db, work_id, user_id):
        logger.warning(f"User {user_id} tried to update unauthorized work {work_id}")
        return None, "You don't have permission to edit this work"
    
    try:
        if name is not None:
            work.name = name
        if description is not None:
            work.description = description
        if status is not None:
            work.status = status
        
        db.commit()
        db.refresh(work)
        
        logger.info(f"✅ Work updated: {work.name} (ID: {work.id})")
        
        return work, None
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update work: {str(e)}")
        return None, f"Failed to update work: {str(e)}"


# ============================================================================
# DELETE WORK
# ============================================================================


def delete_work(
    db: Session,
    work_id: int,
    user_id: int,
) -> Tuple[bool, Optional[str]]:
    """
    Delete a work project and all related data.
    Requires owner permission.
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID (permission check)
    
    Returns:
        (success: bool, error_message)
        If successful: (True, None)
        If failed: (False, error_message)
    
    Example:
        success, error = delete_work(db=db, work_id=1, user_id=1)
    """
    work = get_work_by_id(db=db, work_id=work_id)
    
    if not work:
        return False, "Work not found"
    
    # ✅ NEW: Permission check
    if not can_own(db, work_id, user_id):
        logger.warning(f"User {user_id} tried to delete unauthorized work {work_id}")
        return False, "Only owner can delete this work"
    
    try:
        db.delete(work)
        db.commit()
        
        logger.info(f"✅ Work deleted: ID {work_id}")
        
        return True, None
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete work: {str(e)}")
        return False, f"Failed to delete work: {str(e)}"


# ============================================================================
# UPDATE FILE URLS
# ============================================================================


def update_work_file_urls(
    db: Session,
    work_id: int,
    user_id: int,
    excel_url: Optional[str] = None,
    ppt_url: Optional[str] = None,
) -> Tuple[Optional[Work], Optional[str]]:
    """
    Update Excel masterfile and PPT template URLs.
    Requires edit permission.
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID (permission check)
        excel_url: Cloudinary URL to Excel file
        ppt_url: Cloudinary URL to PPT file
    
    Returns:
        (Updated Work object, error_message)
    
    Example:
        work, error = update_work_file_urls(
            db=db,
            work_id=1,
            user_id=1,
            excel_url="https://..."
        )
    """
    work = get_work_by_id(db=db, work_id=work_id)
    
    if not work:
        return None, "Work not found"
    
    # ✅ NEW: Permission check
    if not can_edit(db, work_id, user_id):
        return None, "You don't have permission to edit this work"
    
    try:
        if excel_url:
            work.excel_masterfile_url = excel_url
        if ppt_url:
            work.ppt_template_url = ppt_url
        
        db.commit()
        db.refresh(work)
        
        logger.info(f"✅ Work files updated: {work.name}")
        
        return work, None
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update work files: {str(e)}")
        return None, str(e)


# ============================================================================
# GET EQUIPMENT AND FILES
# ============================================================================


def get_work_equipment_and_files(
    db: Session,
    work_id: int,
    user_id: int,
) -> Tuple[List[Equipment], List[File]]:
    """
    Get all equipment and files for a work.
    Requires view permission.
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID (permission check)
    
    Returns:
        (List of Equipment, List of Files) or ([], []) if no permission
    
    Example:
        equipment, files = get_work_equipment_and_files(
            db=db,
            work_id=1,
            user_id=1
        )
    """
    work = get_work_by_id(db=db, work_id=work_id)
    
    if not work:
        return [], []
    
    # ✅ NEW: Permission check (view level)
    from app.services.permission_service import can_view
    if not can_view(db, work_id, user_id):
        logger.warning(f"User {user_id} tried to access unauthorized work {work_id}")
        return [], []
    
    # Get equipment with components
    equipment = db.query(Equipment).filter(Equipment.work_id == work_id).all()
    
    # Get files
    files = db.query(File).filter(File.work_id == work_id).all()
    
    logger.debug(f"Retrieved {len(equipment)} equipment and {len(files)} files for work {work_id}")
    
    return equipment, files


# ============================================================================
# HELPER: Check if user can access work
# ============================================================================


def verify_work_ownership(
    db: Session,
    work_id: int,
    user_id: int,
) -> bool:
    """
    ⚠️ DEPRECATED: Use permission_service.can_view/can_edit/can_own instead.
    
    This function is kept for backward compatibility.
    It checks if user has ANY permission on the work (view level).
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID
    
    Returns:
        True if user is collaborator, False otherwise
    """
    from app.services.permission_service import can_view
    return can_view(db, work_id, user_id)