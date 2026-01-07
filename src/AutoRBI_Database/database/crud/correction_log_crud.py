from datetime import datetime
from sqlalchemy.orm import Session
from AutoRBI_Database.database.models import CorrectionLog


# 1. Create a correction log record
def create_correction_log(
    db: Session,
    equipment_id: int,
    user_id: int,
    fields_to_fill: int,
    fields_corrected: int
):

    log = CorrectionLog(
        equipment_id=equipment_id,
        user_id=user_id,
        fields_to_fill=fields_to_fill,
        fields_corrected=fields_corrected,
        timestamp=datetime.utcnow()
    )

    db.add(log)
    db.flush()  # Assign correction_id safely

    return log


# 2. Get correction logs for an equipment
def get_logs_for_equipment(db: Session, equipment_id: int):
    return (
        db.query(CorrectionLog)
        .filter(CorrectionLog.equipment_id == equipment_id)
        .order_by(CorrectionLog.timestamp.desc())
        .all()
    )


# 3. Get correction logs for a user
def get_logs_for_user(db: Session, user_id: int):
    return (
        db.query(CorrectionLog)
        .filter(CorrectionLog.user_id == user_id)
        .order_by(CorrectionLog.timestamp.desc())
        .all()
    )
