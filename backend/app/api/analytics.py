from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
from pydantic import BaseModel
from app.models.activity import Activity, EntityType, ActivityAction
from app.models.work import Work
from app.models.extraction import Extraction
from app.models.file import File
from app.models.equipment import Equipment
from app.models.component import Component
from app.db.database import get_db


router = APIRouter()


# ============================================================================
# ENUMS & SCHEMAS
# ============================================================================

class TimePeriod(str, Enum):
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    ALL_TIME = "all_time"


class MetricResponse(BaseModel):
    metric: str
    period: TimePeriod
    group_by: Optional[str] = None
    data: list
    total: int
    timestamp: datetime


# ============================================================================
# EXTRACTION METRICS
# ============================================================================

@router.get("/extractions/status", response_model=MetricResponse)
async def extraction_status(
    period: TimePeriod = Query(TimePeriod.LAST_30_DAYS),
    group_by: Optional[str] = Query(None),  # "user_id", "work_id", None
    db: Session = Depends(get_db)
):
    """
    Extraction success/failure rates.
    
    group_by options:
    - None: overall stats
    - "user_id": breakdown by user
    - "work_id": breakdown by work
    """
    cutoff_date = _get_cutoff_date(period)
    
    if group_by == "user_id":
        result = db.query(
            Work.user_id,
            Extraction.status,
            func.count(Extraction.id).label("count")
        ).join(Work).filter(
            Extraction.created_at >= cutoff_date
        ).group_by(Work.user_id, Extraction.status).all()
        
        data = [
            {"user_id": r.user_id, "status": r.status, "count": r.count}
            for r in result
        ]
    
    elif group_by == "work_id":
        result = db.query(
            Extraction.work_id,
            Extraction.status,
            func.count(Extraction.id).label("count")
        ).filter(
            Extraction.created_at >= cutoff_date
        ).group_by(Extraction.work_id, Extraction.status).all()
        
        data = [
            {"work_id": r.work_id, "status": r.status, "count": r.count}
            for r in result
        ]
    
    else:
        result = db.query(
            Extraction.status,
            func.count(Extraction.id).label("count")
        ).filter(
            Extraction.created_at >= cutoff_date
        ).group_by(Extraction.status).all()
        
        data = [{"status": r.status, "count": r.count} for r in result]
    
    return MetricResponse(
        metric="extraction_status",
        period=period,
        group_by=group_by,
        data=data,
        total=sum([d.get("count", 0) for d in data]),
        timestamp=datetime.utcnow()
    )


# ============================================================================
# WORK METRICS
# ============================================================================

@router.get("/works/status", response_model=MetricResponse)
async def work_status(
    period: TimePeriod = Query(TimePeriod.LAST_30_DAYS),
    group_by: Optional[str] = Query(None),  # "user_id", None
    db: Session = Depends(get_db)
):
    """
    Work completion tracking.
    
    group_by options:
    - None: overall stats
    - "user_id": breakdown by user
    """
    cutoff_date = _get_cutoff_date(period)
    
    if group_by == "user_id":
        result = db.query(
            Work.user_id,
            Work.status,
            func.count(Work.id).label("count")
        ).filter(
            Work.created_at >= cutoff_date
        ).group_by(Work.user_id, Work.status).all()
        
        data = [
            {"user_id": r.user_id, "status": r.status, "count": r.count}
            for r in result
        ]
    
    else:
        result = db.query(
            Work.status,
            func.count(Work.id).label("count")
        ).filter(
            Work.created_at >= cutoff_date
        ).group_by(Work.status).all()
        
        data = [{"status": r.status, "count": r.count} for r in result]
    
    return MetricResponse(
        metric="work_status",
        period=period,
        group_by=group_by,
        data=data,
        total=sum([d.get("count", 0) for d in data]),
        timestamp=datetime.utcnow()
    )


# ============================================================================
# FILE METRICS
# ============================================================================

@router.get("/files/versions", response_model=MetricResponse)
async def file_versions(
    period: TimePeriod = Query(TimePeriod.LAST_30_DAYS),
    group_by: Optional[str] = Query(None),  # "file_type", "work_id", None
    db: Session = Depends(get_db)
):
    """
    File version histories and distribution.
    
    group_by options:
    - None: overall file count and average version
    - "file_type": breakdown by file type (excel, powerpoint)
    - "work_id": breakdown by work
    """
    cutoff_date = _get_cutoff_date(period)
    
    if group_by == "file_type":
        result = db.query(
            File.file_type,
            func.count(File.id).label("count"),
            func.avg(File.version_number).label("avg_version")
        ).filter(
            File.created_at >= cutoff_date
        ).group_by(File.file_type).all()
        
        data = [
            {
                "file_type": r.file_type,
                "count": r.count,
                "avg_version": round(r.avg_version or 0, 2)
            }
            for r in result
        ]
    
    elif group_by == "work_id":
        result = db.query(
            File.work_id,
            func.count(File.id).label("count"),
            func.max(File.version_number).label("max_version")
        ).filter(
            File.created_at >= cutoff_date
        ).group_by(File.work_id).all()
        
        data = [
            {
                "work_id": r.work_id,
                "count": r.count,
                "max_version": r.max_version
            }
            for r in result
        ]
    
    else:
        result = db.query(
            func.count(File.id).label("count"),
            func.avg(File.version_number).label("avg_version")
        ).filter(
            File.created_at >= cutoff_date
        ).all()
        
        data = [
            {
                "count": result[0].count or 0,
                "avg_version": round(result[0].avg_version or 0, 2)
            }
        ]
    
    return MetricResponse(
        metric="file_versions",
        period=period,
        group_by=group_by,
        data=data,
        total=len(data),
        timestamp=datetime.utcnow()
    )


# ============================================================================
# USER METRICS
# ============================================================================

@router.get("/users/activity", response_model=MetricResponse)
async def user_activity(
    period: TimePeriod = Query(TimePeriod.LAST_30_DAYS),
    db: Session = Depends(get_db)
):
    """
    User activity: works created, files created, extractions run.
    """
    cutoff_date = _get_cutoff_date(period)
    
    result = db.query(
        Work.user_id,
        func.count(func.distinct(Work.id)).label("works_created"),
        func.count(func.distinct(File.id)).label("files_created"),
        func.count(func.distinct(Extraction.id)).label("extractions_run")
    ).outerjoin(File, Work.id == File.work_id).outerjoin(
        Extraction, Work.id == Extraction.work_id
    ).filter(
        Work.created_at >= cutoff_date
    ).group_by(Work.user_id).all()
    
    data = [
        {
            "user_id": r.user_id,
            "works_created": r.works_created,
            "files_created": r.files_created or 0,
            "extractions_run": r.extractions_run or 0
        }
        for r in result
    ]
    
    return MetricResponse(
        metric="user_activity",
        period=period,
        group_by=None,
        data=data,
        total=len(data),
        timestamp=datetime.utcnow()
    )


# ============================================================================
# COMPONENT METRICS
# ============================================================================

@router.get("/components/count", response_model=MetricResponse)
async def component_count(
    period: TimePeriod = Query(TimePeriod.LAST_30_DAYS),
    group_by: Optional[str] = Query(None),  # "phase", "fluid", None
    db: Session = Depends(get_db)
):
    """
    Component data trends: count by phase, fluid type.
    
    group_by options:
    - None: total component count
    - "phase": breakdown by phase (Vapor, Liquid, Two-phase)
    - "fluid": breakdown by fluid type
    """
    cutoff_date = _get_cutoff_date(period)
    
    if group_by == "phase":
        result = db.query(
            Component.phase,
            func.count(Component.id).label("count")
        ).join(Equipment).filter(
            Equipment.created_at >= cutoff_date
        ).group_by(Component.phase).all()
        
        data = [
            {"phase": r.phase or "unknown", "count": r.count}
            for r in result
        ]
    
    elif group_by == "fluid":
        result = db.query(
            Component.fluid,
            func.count(Component.id).label("count")
        ).join(Equipment).filter(
            Equipment.created_at >= cutoff_date
        ).group_by(Component.fluid).all()
        
        data = [
            {"fluid": r.fluid or "unknown", "count": r.count}
            for r in result
        ]
    
    else:
        result = db.query(
            func.count(Component.id).label("count")
        ).join(Equipment).filter(
            Equipment.created_at >= cutoff_date
        ).all()
        
        data = [{"count": result[0].count or 0}]
    
    return MetricResponse(
        metric="component_count",
        period=period,
        group_by=group_by,
        data=data,
        total=sum([d.get("count", 0) for d in data]),
        timestamp=datetime.utcnow()
    )


# ============================================================================
# EQUIPMENT METRICS
# ============================================================================

@router.get("/equipment/count", response_model=MetricResponse)
async def equipment_count(
    period: TimePeriod = Query(TimePeriod.LAST_30_DAYS),
    db: Session = Depends(get_db)
):
    """
    Total equipment count by work.
    """
    cutoff_date = _get_cutoff_date(period)
    
    result = db.query(
        Equipment.work_id,
        func.count(Equipment.id).label("count")
    ).filter(
        Equipment.created_at >= cutoff_date
    ).group_by(Equipment.work_id).all()
    
    data = [
        {"work_id": r.work_id, "count": r.count}
        for r in result
    ]
    
    return MetricResponse(
        metric="equipment_count",
        period=period,
        group_by="work_id",
        data=data,
        total=sum([d.get("count", 0) for d in data]),
        timestamp=datetime.utcnow()
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_cutoff_date(period: TimePeriod) -> datetime:
    """Convert TimePeriod to cutoff datetime."""
    now = datetime.utcnow()
    if period == TimePeriod.LAST_7_DAYS:
        return now - timedelta(days=7)
    elif period == TimePeriod.LAST_30_DAYS:
        return now - timedelta(days=30)
    else:  # ALL_TIME
        return datetime.min