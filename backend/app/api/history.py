from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from app.models.activity import Activity, EntityType, ActivityAction
from app.models.work import Work
from app.models.equipment import Equipment
from app.db.database import get_db


router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class ActivityResponse(BaseModel):
    id: int
    user_id: int
    entity_type: str
    entity_id: int
    action: str
    data: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserHistoryResponse(BaseModel):
    user_id: int
    total_activities: int
    activities: list[ActivityResponse]


class WorkHistoryResponse(BaseModel):
    work_id: int
    total_activities: int
    activities: list[ActivityResponse]


class EntityHistoryResponse(BaseModel):
    entity_type: str
    entity_id: int
    total_activities: int
    activities: list[ActivityResponse]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/user/{user_id}", response_model=UserHistoryResponse)
async def get_user_history(
    user_id: int,
    entity_type: Optional[EntityType] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get all activities for a specific user.
    
    Query Parameters:
    - entity_type: Optional filter by entity type (work, equipment, component, file, extraction)
    - limit: Number of records (1-500, default 50)
    - offset: Pagination offset (default 0)
    """
    query = db.query(Activity).filter(Activity.user_id == user_id).order_by(desc(Activity.created_at))
    
    if entity_type:
        query = query.filter(Activity.entity_type == entity_type.value)
    
    total = query.count()
    activities = query.limit(limit).offset(offset).all()
    
    return UserHistoryResponse(
        user_id=user_id,
        total_activities=total,
        activities=[ActivityResponse.from_orm(a) for a in activities]
    )


@router.get("/work/{work_id}", response_model=WorkHistoryResponse)
async def get_work_history(
    work_id: int,
    db: Session = Depends(get_db)
):
    """
    Get complete history of a work and all related entities.
    
    Includes:
    - Work status changes
    - Equipment added/modified/deleted
    - Files uploaded
    - Extractions run
    - All other work-related activities
    """
    # Verify work exists
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    # Get all activities related to this work directly
    work_activities = db.query(Activity).filter(
        (Activity.entity_type == EntityType.WORK.value) & (Activity.entity_id == work_id)
    ).all()
    
    # Get equipment IDs for this work
    equipment = db.query(Equipment).filter(Equipment.work_id == work_id).all()
    equipment_ids = [e.id for e in equipment]
    
    # Get all activities for related equipment and files
    related_activities = []
    if equipment_ids:
        related_activities = db.query(Activity).filter(
            Activity.entity_id.in_(equipment_ids) |
            ((Activity.entity_type == EntityType.FILE.value) & (Activity.data.contains({'work_id': work_id}))) |
            ((Activity.entity_type == EntityType.EXTRACTION.value) & (Activity.data.contains({'work_id': work_id})))
        ).all()
    
    # Combine and sort by created_at descending
    all_activities = work_activities + related_activities
    all_activities.sort(key=lambda x: x.created_at, reverse=True)
    
    return WorkHistoryResponse(
        work_id=work_id,
        total_activities=len(all_activities),
        activities=[ActivityResponse.from_orm(a) for a in all_activities]
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=EntityHistoryResponse)
async def get_entity_history(
    entity_type: EntityType,
    entity_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get complete history of a specific entity.
    
    Supported entity types: work, equipment, component, file, extraction
    """
    activities = db.query(Activity).filter(
        (Activity.entity_type == entity_type.value) & 
        (Activity.entity_id == entity_id)
    ).order_by(desc(Activity.created_at)).limit(limit).all()
    
    return EntityHistoryResponse(
        entity_type=entity_type.value,
        entity_id=entity_id,
        total_activities=len(activities),
        activities=[ActivityResponse.from_orm(a) for a in activities]
    )


@router.get("/action/{action}", response_model=list[ActivityResponse])
async def get_activities_by_action(
    action: ActivityAction,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get all activities of a specific action type.
    
    Useful for finding: all deletions, all extractions, all status changes, etc.
    Action types: created, updated, deleted, status_changed
    """
    activities = db.query(Activity).filter(
        Activity.action == action.value
    ).order_by(desc(Activity.created_at)).limit(limit).offset(offset).all()
    
    return [ActivityResponse.from_orm(a) for a in activities]


@router.get("/period", response_model=list[ActivityResponse])
async def get_activities_by_period(
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get all activities from the last N days.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    activities = db.query(Activity).filter(
        Activity.created_at >= cutoff
    ).order_by(desc(Activity.created_at)).limit(limit).all()
    
    return [ActivityResponse.from_orm(a) for a in activities]


# ============================================================================
# LOG ACTIVITY ENDPOINT (for frontend)
# ============================================================================

class LogActivityRequest(BaseModel):
    user_id: int
    entity_type: EntityType
    entity_id: int
    action: ActivityAction
    data: Optional[dict] = None


@router.post("/log", response_model=ActivityResponse)
async def log_activity(
    request: LogActivityRequest,
    db: Session = Depends(get_db)
):
    """
    Log an activity from the frontend.
    
    Call this after successful CRUD operations to record what happened.
    
    Example:
        POST /history/log
        {
            "user_id": 5,
            "entity_type": "work",
            "entity_id": 10,
            "action": "created",
            "data": {"name": "Q4 Report"}
        }
    """
    activity = Activity(
        user_id=request.user_id,
        entity_type=request.entity_type.value,
        entity_id=request.entity_id,
        action=request.action.value,
        data=request.data
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    
    return ActivityResponse.from_orm(activity)


# ============================================================================
# ACTIVITY LOGGER SERVICE
# ============================================================================

class ActivityLogger:
    """Utility to log user activities. Use this in your CRUD endpoints."""
    
    @staticmethod
    def log(
        db: Session,
        user_id: int,
        entity_type: EntityType,
        entity_id: int,
        action: ActivityAction,
        data: Optional[dict] = None
    ) -> Activity:
        """
        Log a single activity.
        
        Example:
            ActivityLogger.log(
                db=db,
                user_id=current_user.id,
                entity_type=EntityType.WORK,
                entity_id=work.id,
                action=ActivityAction.CREATED,
                data={"name": work.name}
            )
        """
        activity = Activity(
            user_id=user_id,
            entity_type=entity_type.value,
            entity_id=entity_id,
            action=action.value,
            data=data
        )
        db.add(activity)
        db.commit()
        return activity