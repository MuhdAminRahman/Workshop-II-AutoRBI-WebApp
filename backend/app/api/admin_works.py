"""
Admin Works Management Routes
Admin-only endpoints for managing user works

GET /api/admin/works - List all works across all users (paginated)
GET /api/admin/users/{user_id}/works - List works for specific user
POST /api/admin/works/assign - Assign work to user
PUT /api/admin/works/{work_id} - Update work (admin can change owner)
DELETE /api/admin/works/{work_id} - Delete work
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.work import Work
from app.dependencies import get_current_user
from app.schemas.work import (
    WorkResponse,
    WorkDetailResponse,
)
from app.services.work_service import (
    get_work_by_id,
    get_work_equipment_and_files,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# MIDDLEWARE: VERIFY ADMIN ROLE
# ============================================================================

async def verify_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Verify that current user is an admin.
    
    Raises:
        HTTPException 403: If user is not admin
    """
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted admin action")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )
    return current_user


# ============================================================================
# SCHEMAS
# ============================================================================

from pydantic import BaseModel
from typing import Optional, List


class AdminWorksListResponse(BaseModel):
    """Response for listing all works"""
    works: List[dict]
    total: int
    page: int
    page_size: int
    
    class Config:
        from_attributes = True


class AdminWorkDetailResponse(BaseModel):
    """Response for work details with user info"""
    work: WorkResponse
    user: dict
    equipment_count: int
    file_count: int
    extraction_count: int
    
    class Config:
        from_attributes = True


class AssignWorkRequest(BaseModel):
    """Request to assign work to user"""
    work_id: int
    user_id: int


class AssignWorkResponse(BaseModel):
    """Response after assigning work"""
    work_id: int
    user_id: int
    message: str
    
    class Config:
        from_attributes = True


class AdminWorkUpdateRequest(BaseModel):
    """Request to update work (admin can change owner)"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None  # Admin can change owner


# ============================================================================
# LIST ALL WORKS (Admin Only)
# ============================================================================

@router.get(
    "/works",
    response_model=AdminWorksListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all works",
    description="Admin: Get all works across all users with pagination",
)
async def list_all_works(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    status: Optional[str] = Query(None, description="Filter by status (active, completed, archived)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    sort_by: str = Query("created_at", description="Sort by: created_at, name, status"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    current_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
) -> AdminWorksListResponse:
    """
    List all works in the system (admin only).
    
    Query Parameters:
    - skip: Pagination offset (default 0)
    - limit: Records per page (1-500, default 50)
    - status: Filter by status (optional)
    - user_id: Filter by user ID (optional)
    - sort_by: Sort column (created_at, name, status)
    - sort_order: asc or desc (default desc)
    
    Returns:
        AdminWorksListResponse with works list and pagination info
    
    Example:
        GET /api/admin/works?skip=0&limit=10&status=active&sort_by=created_at
    """
    logger.info(f"Admin {current_user.username} listing all works")
    
    query = db.query(Work)
    
    # Apply filters
    if status:
        query = query.filter(Work.status == status)
    
    if user_id is not None:
        query = query.filter(Work.user_id == user_id)
    
    # Apply sorting
    sort_column = {
        "created_at": Work.created_at,
        "name": Work.name,
        "status": Work.status,
    }.get(sort_by, Work.created_at)
    
    if sort_order.lower() == "asc":
        query = query.order_by(sort_column)
    else:
        query = query.order_by(desc(sort_column))
    
    # Get total count
    total = query.count()
    
    # Paginate
    works = query.offset(skip).limit(limit).all()
    
    # Format response
    works_data = [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "status": w.status,
            "user_id": w.user_id,
            "user_username": w.user.username if w.user else None,
            "created_at": w.created_at,
            "updated_at": w.updated_at,
        }
        for w in works
    ]
    
    logger.info(f"Listed {len(works)} works (total: {total})")
    
    return AdminWorksListResponse(
        works=works_data,
        total=total,
        page=skip // limit,
        page_size=limit,
    )


# ============================================================================
# LIST WORKS FOR SPECIFIC USER (Admin Only)
# ============================================================================

@router.get(
    "/users/{user_id}/works",
    response_model=AdminWorksListResponse,
    status_code=status.HTTP_200_OK,
    summary="List works for user",
    description="Admin: Get all works for a specific user",
)
async def list_user_works(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[str] = Query(None),
    current_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
) -> AdminWorksListResponse:
    """
    List all works for a specific user (admin only).
    
    Args:
        user_id: Target user ID
        skip: Pagination offset
        limit: Records per page
        status: Optional filter by status
        current_user: Current admin user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        AdminWorksListResponse with user's works
    
    Raises:
        HTTPException 404: If user not found
    
    Example:
        GET /api/admin/users/5/works?skip=0&limit=10
    """
    logger.info(f"Admin {current_user.username} listing works for user {user_id}")
    
    # Verify user exists
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        logger.warning(f"Admin tried to list works for non-existent user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    query = db.query(Work).filter(Work.user_id == user_id)
    
    if status:
        query = query.filter(Work.status == status)
    
    total = query.count()
    works = query.order_by(desc(Work.created_at)).offset(skip).limit(limit).all()
    
    works_data = [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "status": w.status,
            "user_id": w.user_id,
            "user_username": w.user.username,
            "created_at": w.created_at,
            "updated_at": w.updated_at,
        }
        for w in works
    ]
    
    logger.info(f"Listed {len(works)} works for user {target_user.username}")
    
    return AdminWorksListResponse(
        works=works_data,
        total=total,
        page=skip // limit,
        page_size=limit,
    )


# ============================================================================
# GET WORK DETAILS (Admin Only)
# ============================================================================

@router.get(
    "/works/{work_id}",
    response_model=AdminWorkDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get work details",
    description="Admin: Get detailed information about a work",
)
async def get_work_admin(
    work_id: int,
    current_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
) -> AdminWorkDetailResponse:
    """
    Get detailed work information (admin only).
    
    Includes:
    - Work details
    - Owner user information
    - Equipment count
    - File count
    - Extraction count
    
    Args:
        work_id: Work ID
        current_user: Current admin user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        AdminWorkDetailResponse with full work details
    
    Raises:
        HTTPException 404: If work not found
    
    Example:
        GET /api/admin/works/1
    """
    logger.info(f"Admin {current_user.username} viewing work {work_id}")
    
    work = db.query(Work).filter(Work.id == work_id).first()
    
    if not work:
        logger.warning(f"Admin tried to view non-existent work {work_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    
    # Get counts
    from app.models.equipment import Equipment
    from app.models.file import File
    from app.models.extraction import Extraction
    
    equipment_count = db.query(Equipment).filter(Equipment.work_id == work_id).count()
    file_count = db.query(File).filter(File.work_id == work_id).count()
    extraction_count = db.query(Extraction).filter(Extraction.work_id == work_id).count()
    
    logger.info(f"Work {work_id}: {equipment_count} equipment, {file_count} files, {extraction_count} extractions")
    
    return AdminWorkDetailResponse(
        work=WorkResponse.model_validate(work),
        user={
            "id": work.user.id,
            "username": work.user.username,
            "email": work.user.email,
            "full_name": work.user.full_name,
            "role": work.user.role,
        },
        equipment_count=equipment_count,
        file_count=file_count,
        extraction_count=extraction_count,
    )


# ============================================================================
# ASSIGN WORK TO USER (Admin Only)
# ============================================================================

@router.post(
    "/works/assign",
    response_model=AssignWorkResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign work to user",
    description="Admin: Change the owner of a work",
)
async def assign_work_to_user(
    request: AssignWorkRequest,
    current_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
) -> AssignWorkResponse:
    """
    Assign a work to a user (change owner).
    
    Args:
        request: AssignWorkRequest with work_id and user_id
        current_user: Current admin user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        AssignWorkResponse with confirmation
    
    Raises:
        HTTPException 404: If work or user not found
        HTTPException 400: If assignment fails
    
    Example:
        POST /api/admin/works/assign
        {
            "work_id": 1,
            "user_id": 5
        }
    """
    logger.info(f"Admin {current_user.username} assigning work {request.work_id} to user {request.user_id}")
    
    # Verify work exists
    work = db.query(Work).filter(Work.id == request.work_id).first()
    if not work:
        logger.warning(f"Admin tried to assign non-existent work {request.work_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    
    # Verify target user exists
    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        logger.warning(f"Admin tried to assign work to non-existent user {request.user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )
    
    try:
        old_owner = work.user.username
        work.user_id = request.user_id
        db.commit()
        db.refresh(work)
        
        logger.info(f"âœ… Work {request.work_id} transferred from {old_owner} to {target_user.username}")
        
        return AssignWorkResponse(
            work_id=work.id,
            user_id=work.user_id,
            message=f"Work reassigned from {old_owner} to {target_user.username}",
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to assign work: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assign work: {str(e)}",
        )


# ============================================================================
# UPDATE WORK (Admin Only)
# ============================================================================

@router.put(
    "/works/{work_id}",
    response_model=WorkResponse,
    status_code=status.HTTP_200_OK,
    summary="Update work",
    description="Admin: Update work details or change owner",
)
async def update_work_admin(
    work_id: int,
    request: AdminWorkUpdateRequest,
    current_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
) -> WorkResponse:
    """
    Update a work (admin can change owner).
    
    Args:
        work_id: Work ID
        request: AdminWorkUpdateRequest with fields to update
        current_user: Current admin user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Updated WorkResponse
    
    Raises:
        HTTPException 404: If work or new owner not found
        HTTPException 400: If update fails
    
    Example:
        PUT /api/admin/works/1
        {
            "status": "completed",
            "user_id": 5
        }
    """
    logger.info(f"Admin {current_user.username} updating work {work_id}")
    
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    
    try:
        # Update basic fields
        if request.name is not None:
            work.name = request.name
            logger.debug(f"Updated work name to: {request.name}")
        
        if request.description is not None:
            work.description = request.description
            logger.debug(f"Updated work description")
        
        if request.status is not None:
            work.status = request.status
            logger.debug(f"Updated work status to: {request.status}")
        
        # Update owner (admin-only feature)
        if request.user_id is not None:
            new_owner = db.query(User).filter(User.id == request.user_id).first()
            if not new_owner:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="New owner user not found",
                )
            
            old_owner = work.user.username
            work.user_id = request.user_id
            logger.info(f"Changed work owner from {old_owner} to {new_owner.username}")
        
        db.commit()
        db.refresh(work)
        
        logger.info(f"âœ… Work {work_id} updated successfully")
        
        return WorkResponse.model_validate(work)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update work: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update work: {str(e)}",
        )


# ============================================================================
# DELETE WORK (Admin Only)
# ============================================================================

@router.delete(
    "/works/{work_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete work",
    description="Admin: Delete work and all related data",
)
async def delete_work_admin(
    work_id: int,
    current_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a work (admin only).
    
    Cascade deletes:
    - Equipment and components
    - Extractions
    - Files
    
    Args:
        work_id: Work ID
        current_user: Current admin user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        None (204 No Content)
    
    Raises:
        HTTPException 404: If work not found
        HTTPException 400: If deletion fails
    
    Example:
        DELETE /api/admin/works/1
    """
    logger.info(f"Admin {current_user.username} deleting work {work_id}")
    
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    
    try:
        work_name = work.name
        db.delete(work)
        db.commit()
        
        logger.info(f"âœ… Work deleted: {work_name} (ID: {work_id})")
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete work: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete work: {str(e)}",
        )


# ============================================================================
# ROUTE SUMMARY
# ============================================================================

"""
Admin Works Routes (All require ADMIN role):

1. GET /api/admin/works
   - List all works (paginated, filterable, sortable)
   - Query: skip, limit, status, user_id, sort_by, sort_order
   - Response: AdminWorksListResponse
   - Status: 200 OK

2. GET /api/admin/users/{user_id}/works
   - List works for specific user
   - Query: skip, limit, status
   - Response: AdminWorksListResponse
   - Status: 200 OK or 404 Not Found

3. GET /api/admin/works/{work_id}
   - Get detailed work information
   - Includes: equipment count, file count, extraction count
   - Response: AdminWorkDetailResponse
   - Status: 200 OK or 404 Not Found

4. POST /api/admin/works/assign
   - Assign work to user (change owner)
   - Body: work_id, user_id
   - Response: AssignWorkResponse
   - Status: 200 OK or 404/400

5. PUT /api/admin/works/{work_id}
   - Update work (including owner)
   - Body: name, description, status, user_id (all optional)
   - Response: WorkResponse
   - Status: 200 OK or 404/400

6. DELETE /api/admin/works/{work_id}
   - Delete work and all related data
   - Response: None (204 No Content)
   - Status: 204 No Content or 404/400

All routes require authentication with ADMIN role
"""