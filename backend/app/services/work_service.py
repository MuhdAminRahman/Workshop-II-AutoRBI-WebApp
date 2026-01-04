"""
Work Service
Business logic for work project management
"""

import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.work import Work, WorkStatus
from app.models.equipment import Equipment
from app.models.file import File

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
    
    Args:
        db: Database session
        user_id: Owner user ID
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
        if error:
            print(f"Failed: {error}")
    """
    try:
        new_work = Work(
            user_id=user_id,
            name=name,
            description=description,
            status=WorkStatus.ACTIVE,
        )
        
        db.add(new_work)
        db.commit()
        db.refresh(new_work)
        
        logger.info(f"✅ Work created: {name} (ID: {new_work.id})")
        
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
    user_id: Optional[int] = None,
) -> Optional[Work]:
    """
    Get work by ID.
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: Optional - if provided, ensure work belongs to this user
    
    Returns:
        Work object or None if not found
    
    Example:
        work = get_work_by_id(db=db, work_id=1)
        work = get_work_by_id(db=db, work_id=1, user_id=1)  # Verify ownership
    """
    query = db.query(Work).filter(Work.id == work_id)
    
    if user_id is not None:
        query = query.filter(Work.user_id == user_id)
    
    work = query.first()
    
    if not work:
        logger.warning(f"Work not found: ID {work_id}")
        return None
    
    logger.debug(f"Retrieved work: {work.name} (ID: {work.id})")
    
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
    List all works for a user.
    
    Args:
        db: Database session
        user_id: User ID
        skip: Number of records to skip (pagination)
        limit: Maximum records to return (pagination)
    
    Returns:
        (List of Work objects, total count)
    
    Example:
        works, total = list_works_for_user(db=db, user_id=1, skip=0, limit=10)
        print(f"Found {total} works, returning {len(works)}")
    """
    query = db.query(Work).filter(Work.user_id == user_id)
    
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
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID (verify ownership)
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
    work = get_work_by_id(db=db, work_id=work_id, user_id=user_id)
    
    if not work:
        return None, "Work not found or you don't have permission"
    
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
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID (verify ownership)
    
    Returns:
        (success: bool, error_message)
        If successful: (True, None)
        If failed: (False, error_message)
    
    Example:
        success, error = delete_work(db=db, work_id=1, user_id=1)
        if success:
            print("Work deleted")
    """
    work = get_work_by_id(db=db, work_id=work_id, user_id=user_id)
    
    if not work:
        return False, "Work not found or you don't have permission"
    
    try:
        # Cascade delete handles related records:
        # - equipment → components
        # - extractions
        # - files
        db.delete(work)
        db.commit()
        
        logger.info(f"✅ Work deleted: {work.name} (ID: {work.id})")
        
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
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID (verify ownership)
        excel_url: Cloudinary URL to Excel file
        ppt_url: Cloudinary URL to PPT file
    
    Returns:
        (Updated Work object, error_message)
    
    Example:
        work, error = update_work_file_urls(
            db=db,
            work_id=1,
            user_id=1,
            excel_url="https://res.cloudinary.com/.../masterfile.xlsx",
            ppt_url="https://res.cloudinary.com/.../template.pptx"
        )
    """
    work = get_work_by_id(db=db, work_id=work_id, user_id=user_id)
    
    if not work:
        return None, "Work not found"
    
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
    user_id: Optional[int] = None,
) -> Tuple[List[Equipment], List[File]]:
    """
    Get all equipment and files for a work.
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: Optional - verify ownership
    
    Returns:
        (List of Equipment, List of Files)
    
    Example:
        equipment, files = get_work_equipment_and_files(
            db=db,
            work_id=1,
            user_id=1
        )
    """
    # Verify work exists and belongs to user (if user_id provided)
    work = get_work_by_id(db=db, work_id=work_id, user_id=user_id)
    
    if not work:
        return [], []
    
    # Get equipment with components
    equipment = db.query(Equipment).filter(Equipment.work_id == work_id).all()
    
    # Get files
    files = db.query(File).filter(File.work_id == work_id).all()
    
    logger.debug(f"Retrieved {len(equipment)} equipment and {len(files)} files for work {work_id}")
    
    return equipment, files


# ============================================================================
# HELPER: Check work ownership
# ============================================================================


def verify_work_ownership(
    db: Session,
    work_id: int,
    user_id: int,
) -> bool:
    """
    Verify that a work belongs to a user.
    
    Args:
        db: Database session
        work_id: Work ID
        user_id: User ID
    
    Returns:
        True if user owns the work, False otherwise
    
    Example:
        if verify_work_ownership(db=db, work_id=1, user_id=1):
            print("User owns this work")
    """
    work = db.query(Work).filter(
        Work.id == work_id,
        Work.user_id == user_id
    ).first()
    
    return work is not None