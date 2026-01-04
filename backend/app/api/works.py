"""
Works Routes
CRUD operations for work projects
GET /api/works - List works
POST /api/works - Create work
GET /api/works/{workId} - Get work details
PUT /api/works/{workId} - Update work
DELETE /api/works/{workId} - Delete work
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
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
    verify_work_ownership,
)

logger = logging.getLogger(__name__)

# Create router for work endpoints
router = APIRouter()

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
    
    Args:
        skip: Pagination - number of records to skip (default 0)
        limit: Pagination - max records to return (default 100, max 1000)
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        List of works with total count
    
    Example:
        GET /api/works?skip=0&limit=10
        
        Response:
        {
            "works": [
                {
                    "id": 1,
                    "name": "Refinery Unit A",
                    "status": "active",
                    ...
                }
            ],
            "total": 5
        }
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
    description="Create a new work project",
)
async def create_new_work(
    request: WorkCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkResponse:
    """
    Create a new work project.
    
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
    
    Args:
        work_id: Work ID
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Work with equipment and files
    
    Raises:
        HTTPException 404: If work not found or not owned by user
    
    Example:
        GET /api/works/1
        
        Response:
        {
            "work": {...},
            "equipment": [...],
            "files": [...]
        }
    """
    logger.info(f"Getting work details: {work_id}")
    
    work = get_work_by_id(
        db=db,
        work_id=work_id,
        user_id=current_user.id,
    )
    
    if not work:
        logger.warning(f"Work not found: {work_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
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
    description="Update work project details",
)
async def update_work_details(
    work_id: int,
    request: WorkUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkResponse:
    """
    Update a work project.
    
    Args:
        work_id: Work ID
        request: Update data (any fields to update)
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        Updated work object
    
    Raises:
        HTTPException 404: If work not found
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
    description="Delete work project and all related data",
)
async def delete_work_project(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a work project.
    
    Cascade deletes all related data:
    - Equipment
    - Components
    - Extractions
    - Files
    
    Args:
        work_id: Work ID
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        None (204 No Content)
    
    Raises:
        HTTPException 404: If work not found
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
# ROUTE SUMMARY
# ============================================================================

"""
Works Routes:

1. GET /api/works
   - List all works for current user
   - Query params: skip, limit (pagination)
   - Response: WorksListResponse (works array + total count)
   - Status: 200 OK

2. POST /api/works
   - Create new work
   - Body: name, description
   - Response: WorkResponse
   - Status: 201 Created

3. GET /api/works/{workId}
   - Get work with equipment and files
   - Params: workId
   - Response: WorkDetailResponse (work + equipment + files)
   - Status: 200 OK or 404 Not Found

4. PUT /api/works/{workId}
   - Update work
   - Params: workId
   - Body: name, description, status (all optional)
   - Response: WorkResponse
   - Status: 200 OK or 404 Not Found

5. DELETE /api/works/{workId}
   - Delete work and all related data
   - Params: workId
   - Response: None
   - Status: 204 No Content or 404 Not Found

All routes require authentication (Bearer token in Authorization header)
"""