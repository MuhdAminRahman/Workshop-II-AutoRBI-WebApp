"""
Works Routes - Updated for multi-user collaboration
CRUD operations for work projects
GET /api/works - List works for current user
POST /api/works - Create work
GET /api/works/{workId} - Get work details
PUT /api/works/{workId} - Update work
DELETE /api/works/{workId} - Delete work
POST /api/works/{workId}/collaborators - Add collaborator
DELETE /api/works/{workId}/collaborators/{userId} - Remove collaborator
GET /api/works/{workId}/collaborators - List collaborators
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.user import User
from app.models.work_collaborator import CollaboratorRole
from app.dependencies import get_current_user
from app.schemas.work import (
    WorkCreateRequest,
    WorkUpdateRequest,
    WorkResponse,
    WorkDetailResponse,
    WorksListResponse,
    EquipmentResponse,
    FileVersionResponse,
)
from app.services.work_service import (
    create_work,
    get_work_by_id,
    list_works_for_user,
    update_work,
    delete_work,
    get_work_equipment_and_files,
)
from app.services.permission_service import (
    can_view,
    can_edit,
    can_own,
    get_owner_count,
)
from app.models.work_collaborator import WorkCollaborator
from app.models.user import User as UserModel

logger = logging.getLogger(__name__)

# Create router for work endpoints
router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class CollaboratorResponse(BaseModel):
    user_id: int
    email: str
    full_name: str
    role: str
    
    class Config:
        from_attributes = True


class CollaboratorsListResponse(BaseModel):
    work_id: int
    collaborators: list[CollaboratorResponse]


# ============================================================================
# LIST WORKS - GET /api/works
# ============================================================================


@router.get(
    "",
    response_model=WorksListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all works",
    description="Get all work projects for current user with pagination",
)
async def list_works(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorksListResponse:
    """
    List all work projects for current user.
    
    Returns works where user is a collaborator (any role).
    
    Args:
        skip: Pagination - number of records to skip (default 0)
        limit: Pagination - max records to return (default 100, max 1000)
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        List of works with total count
    
    Example:
        GET /api/works?skip=0&limit=10
    """
    logger.info(f"Listing works for user {current_user.username}")
    
    works, total = list_works_for_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    
    return WorksListResponse(
        works=[WorkResponse.model_validate(work) for work in works],
        total=total,
    )


# ============================================================================
# CREATE WORK - POST /api/works
# ============================================================================


@router.post(
    "",
    response_model=WorkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new work",
    description="Create a new work project (creator becomes owner)",
)
async def create_new_work(
    request: WorkCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkResponse:
    """
    Create a new work project.
    Creator automatically becomes owner.
    
    Args:
        request: Work creation data (name, description)
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Created work object
    
    Raises:
        HTTPException 400: If creation fails
    
    Example:
        POST /api/works
        {
            "name": "Refinery Unit A",
            "description": "Extract equipment data from GA drawings"
        }
    """
    logger.info(f"Creating work: {request.name} for user {current_user.username}")
    
    work, error = create_work(
        db=db,
        user_id=current_user.id,
        name=request.name,
        description=request.description,
    )
    
    if error:
        logger.warning(f"Failed to create work: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    return WorkResponse.model_validate(work)


# ============================================================================
# GET WORK DETAILS - GET /api/works/{workId}
# ============================================================================


@router.get(
    "/{work_id}",
    response_model=WorkDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get work details",
    description="Get work with equipment and files",
)
async def get_work_details(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkDetailResponse:
    """
    Get work project with all related equipment and files.
    Requires view permission.
    
    Args:
        work_id: Work ID
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Work with equipment and files
    
    Raises:
        HTTPException 404: If work not found
        HTTPException 403: If user doesn't have access
    
    Example:
        GET /api/works/1
    """
    logger.info(f"Getting work details: {work_id}")
    
    work = get_work_by_id(db=db, work_id=work_id)
    
    if not work:
        logger.warning(f"Work not found: {work_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    
    # ✅ NEW: Permission check
    if not can_view(db, work_id, current_user.id):
        logger.warning(f"User {current_user.username} tried to access unauthorized work {work_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this work",
        )
    
    equipment, files = get_work_equipment_and_files(
        db=db,
        work_id=work_id,
        user_id=current_user.id,
    )
    
    return WorkDetailResponse(
        work=WorkResponse.model_validate(work),
        equipment=[EquipmentResponse.model_validate(eq) for eq in equipment],
        files=[FileVersionResponse.model_validate(f) for f in files],
    )


# ============================================================================
# UPDATE WORK - PUT /api/works/{workId}
# ============================================================================


@router.put(
    "/{work_id}",
    response_model=WorkResponse,
    status_code=status.HTTP_200_OK,
    summary="Update work",
    description="Update work project details (requires edit permission)",
)
async def update_work_details(
    work_id: int,
    request: WorkUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkResponse:
    """
    Update a work project.
    Requires edit permission.
    
    Args:
        work_id: Work ID
        request: Update data (any fields to update)
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Updated work object
    
    Raises:
        HTTPException 404: If work not found
        HTTPException 403: If no edit permission
        HTTPException 400: If update fails
    
    Example:
        PUT /api/works/1
        {
            "name": "Updated Name",
            "status": "completed"
        }
    """
    logger.info(f"Updating work: {work_id}")
    
    work, error = update_work(
        db=db,
        work_id=work_id,
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        status=request.status,
    )
    
    if error:
        if "permission" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error,
            )
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    return WorkResponse.model_validate(work)


# ============================================================================
# DELETE WORK - DELETE /api/works/{workId}
# ============================================================================


@router.delete(
    "/{work_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete work",
    description="Delete work project and all related data (owner only)",
)
async def delete_work_project(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a work project.
    Cascade deletes all related data (equipment, components, extractions, files).
    Requires owner permission.
    
    Args:
        work_id: Work ID
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        None (204 No Content)
    
    Raises:
        HTTPException 404: If work not found
        HTTPException 403: If not owner
        HTTPException 400: If deletion fails
    
    Example:
        DELETE /api/works/1
    """
    logger.info(f"Deleting work: {work_id}")
    
    success, error = delete_work(
        db=db,
        work_id=work_id,
        user_id=current_user.id,
    )
    
    if not success:
        if "permission" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error,
            )
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )


# ============================================================================
# ADD COLLABORATOR - POST /api/works/{workId}/collaborators
# ============================================================================


@router.post(
    "/{work_id}/collaborators",
    status_code=status.HTTP_201_CREATED,
    summary="Add collaborator",
    description="Add collaborator to work (owner only)",
)
async def add_collaborator(
    work_id: int,
    email: str = Query(..., description="Email of user to add"),
    role: CollaboratorRole = Query(CollaboratorRole.EDITOR, description="Role (owner, editor, viewer)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add collaborator to work project.
    Requires owner permission.
    
    Args:
        work_id: Work ID
        email: Email of user to add
        role: Role (owner, editor, viewer) - default: editor
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Success message
    
    Raises:
        HTTPException 404: If work or user not found
        HTTPException 403: If not owner
        HTTPException 400: If user already collaborating
    
    Example:
        POST /api/works/1/collaborators?email=alice@example.com&role=editor
    """
    logger.info(f"Adding collaborator {email} to work {work_id}")
    
    # Verify owner
    if not can_own(db, work_id, current_user.id):
        logger.warning(f"User {current_user.username} tried to manage collaborators without owner permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can manage collaborators",
        )
    
    # Check if work exists
    work = get_work_by_id(db=db, work_id=work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    
    # Find user by email
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if already collaborator
    existing = db.query(WorkCollaborator).filter(
        WorkCollaborator.work_id == work_id,
        WorkCollaborator.user_id == user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already collaborating on this work",
        )
    
    # Add collaborator
    try:
        collaborator = WorkCollaborator(work_id=work_id, user_id=user.id, role=role)
        db.add(collaborator)
        db.commit()
        
        logger.info(f"✅ Added {user.email} as {role} to work {work_id}")
        
        return {"message": f"Added {user.email} as {role}"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add collaborator: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add collaborator",
        )


# ============================================================================
# REMOVE COLLABORATOR - DELETE /api/works/{workId}/collaborators/{userId}
# ============================================================================


@router.delete(
    "/{work_id}/collaborators/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove collaborator",
    description="Remove collaborator from work (owner only)",
)
async def remove_collaborator(
    work_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove collaborator from work project.
    Requires owner permission.
    Cannot remove last owner.
    
    Args:
        work_id: Work ID
        user_id: User ID to remove
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Success message
    
    Raises:
        HTTPException 403: If not owner
        HTTPException 404: If collaborator not found
        HTTPException 400: If trying to remove last owner
    
    Example:
        DELETE /api/works/1/collaborators/5
    """
    logger.info(f"Removing collaborator {user_id} from work {work_id}")
    
    # Verify owner
    if not can_own(db, work_id, current_user.id):
        logger.warning(f"User {current_user.username} tried to remove collaborator without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can manage collaborators",
        )
    
    # Prevent removing last owner
    owner_count = get_owner_count(db, work_id)
    target_is_owner = can_own(db, work_id, user_id)
    
    if target_is_owner and owner_count == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last owner of the work",
        )
    
    # Find collaborator
    collaborator = db.query(WorkCollaborator).filter(
        WorkCollaborator.work_id == work_id,
        WorkCollaborator.user_id == user_id
    ).first()
    
    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found",
        )
    
    try:
        db.delete(collaborator)
        db.commit()
        
        logger.info(f"✅ Removed user {user_id} from work {work_id}")
        
        return {"message": "Collaborator removed"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to remove collaborator: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove collaborator",
        )


# ============================================================================
# LIST COLLABORATORS - GET /api/works/{workId}/collaborators
# ============================================================================


@router.get(
    "/{work_id}/collaborators",
    response_model=CollaboratorsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List collaborators",
    description="List all collaborators on a work",
)
async def list_collaborators(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CollaboratorsListResponse:
    """
    List all collaborators on a work project.
    Any collaborator can view the list.
    
    Args:
        work_id: Work ID
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        List of collaborators with roles
    
    Raises:
        HTTPException 403: If user doesn't have access
        HTTPException 404: If work not found
    
    Example:
        GET /api/works/1/collaborators
    """
    logger.info(f"Listing collaborators for work {work_id}")
    
    # Check access
    if not can_view(db, work_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this work",
        )
    
    # Verify work exists
    work = get_work_by_id(db=db, work_id=work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    
    # Get collaborators
    collaborators = db.query(WorkCollaborator).join(UserModel).filter(
        WorkCollaborator.work_id == work_id
    ).all()
    
    return CollaboratorsListResponse(
        work_id=work_id,
        collaborators=[
            CollaboratorResponse(
                user_id=c.user_id,
                email=c.user.email,
                full_name=c.user.full_name or "",
                role=c.role,
            )
            for c in collaborators
        ]
    )