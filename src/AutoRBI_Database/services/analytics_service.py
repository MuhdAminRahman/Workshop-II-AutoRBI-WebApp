# services/analytics_service.py
""""
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from database.models import Work, Equipment, WorkHistory, CorrectionLog


# -----------------------------
# 1. Total Works
# -----------------------------
def get_total_works(db: Session):
    return db.query(func.count(Work.work_id)).scalar()


# -----------------------------
# 2. Success Rate
# Success = equipment that have extracted_date NOT NULL
# -----------------------------
def get_extraction_success_rate(db: Session):
    total = db.query(func.count(Equipment.equipment_id)).scalar()
    if total == 0:
        return 0

    extracted = db.query(func.count(Equipment.equipment_id)).filter(
        Equipment.extracted_date.isnot(None)
    ).scalar()

    return (extracted / total) * 100


# -----------------------------
# 3. Total Files Generated (Excel + PPT)
# Counts works that have paths
# -----------------------------
def get_total_generated_files(db: Session):
    excel_count = db.query(func.count(Work.work_id)).filter(Work.excel_path.isnot(None)).scalar()
    ppt_count = db.query(func.count(Work.work_id)).filter(Work.ppt_path.isnot(None)).scalar()
    return excel_count + ppt_count


# -----------------------------
# 4. Recent Activity Summary (from work_history)
# -----------------------------
def get_recent_activity(db: Session, limit: int = 5):
    return (
        db.query(WorkHistory)
        .order_by(WorkHistory.timestamp.desc())
        .limit(limit)
        .all()
    )


# -----------------------------
# 5. Work Over Time (aggregate by date)
# -----------------------------
def get_work_over_time(db: Session):
    return (
        db.query(
            func.date(Work.created_at).label("date"),
            func.count(Work.work_id).label("total_works")
        )
        .group_by(func.date(Work.created_at))
        .order_by(func.date(Work.created_at))
        .all()
    )


# -----------------------------
# 6. Status Distribution
# Example: how many works are "In progress" vs "Completed"
# -----------------------------
def get_status_distribution(db: Session):
    return (
        db.query(
            Work.status,
            func.count(Work.work_id).label("count")
        )
        .group_by(Work.status)
        .all()
    )


# -----------------------------
# 7. Average Extraction Time
# Requires comparing history timestamps: upload_pdf → extract
# -----------------------------
def get_average_extraction_time(db: Session):
    # This query depends on consistent history logging
    uploads = db.query(WorkHistory).filter(WorkHistory.action_type == "upload_pdf").all()
    extracts = db.query(WorkHistory).filter(WorkHistory.action_type == "extract").all()

    # Map equipment_id → upload time
    upload_map = {h.equipment_id: h.timestamp for h in uploads}

    durations = []
    for ext in extracts:
        if ext.equipment_id in upload_map:
            delta = ext.timestamp - upload_map[ext.equipment_id]
            durations.append(delta.total_seconds())

    if not durations:
        return 0

    return sum(durations) / len(durations)
"""