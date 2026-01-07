from sqlalchemy.orm import Session
from AutoRBI_Database.database.models import Work
from datetime import datetime

# Normalizer for Work status
def normalize_work_status(value):
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in ["in progress", "progress", "inprogress", "ongoing", "running"]:
        return "In progress"
    if v in ["completed", "done", "finish", "finished"]:
        return "Completed"
    return None


# 1. Create a new work
def create_work(db: Session, work_name: str, description: str = None):
    new_work = Work(
        work_name=work_name,
        description=description,
        status="In progress",
        created_at=datetime.utcnow()
    )
    
    db.add(new_work)
    db.commit()
    db.refresh(new_work)
    return new_work


# 2. Get work by ID
def get_work_by_id(db: Session, work_id: int):
    return db.query(Work).filter(Work.work_id == work_id).first()


# 3. Get work by name
def get_work_by_name(db: Session, work_name: str):
    return db.query(Work).filter(Work.work_name == work_name).first()


# 4. Get all works
def get_all_works(db: Session):
    return db.query(Work).all()


# 5. Update work details (name, description)
def update_work_info(db: Session, work_id: int, updates: dict):
    work = get_work_by_id(db, work_id)
    if not work:
        return None
    
    if "work_name" in updates:
        work.work_name = updates["work_name"]
    if "description" in updates:
        work.description = updates["description"]

    db.commit()
    return work


# 6. Update work status
def update_work_status(db: Session, work_id: int, status: str):
    work = get_work_by_id(db, work_id)
    if not work:
        return None

    normalized = normalize_work_status(status)
    if normalized is None:
        raise ValueError(f"Invalid work status: {status}")

    work.status = normalized
    db.commit()
    return work



# 7. Update Excel path
def update_excel_path(db: Session, work_id: int, path: str):
    work = get_work_by_id(db, work_id)
    if not work:
        return None
    
    work.excel_path = path
    db.commit()
    return work


# 8. Update Inspection Plan (PPT) path
def update_ppt_path(db: Session, work_id: int, path: str):
    work = get_work_by_id(db, work_id)
    if not work:
        return None
    
    work.ppt_path = path
    db.commit()
    return work