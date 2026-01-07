from datetime import datetime
from sqlalchemy.orm import Session
from AutoRBI_Database.database.models import AssignWork


# 1. Assign a user to a work
def assign_user_to_work(db: Session, user_id: int, work_id: int):
    # Prevent duplicate assignments
    existing = (
        db.query(AssignWork)
        .filter(AssignWork.user_id == user_id, AssignWork.work_id == work_id)
        .first()
    )

    if existing:
        return existing  # Already assigned

    assignment = AssignWork(
        user_id=user_id,
        work_id=work_id,
        assigned_at=datetime.utcnow()
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


# 2. Remove an assignment
def unassign_user_from_work(db: Session, user_id: int, work_id: int):
    assignment = (
        db.query(AssignWork)
        .filter(AssignWork.user_id == user_id, AssignWork.work_id == work_id)
        .first()
    )

    if not assignment:
        return None

    db.delete(assignment)
    db.commit()
    return True


# 3. Get all engineers assigned to a work
def get_engineers_for_work(db: Session, work_id: int):
    return (
        db.query(AssignWork)
        .filter(AssignWork.work_id == work_id)
        .all()
    )


# 4. Get all works assigned to a user
def get_works_for_user(db: Session, user_id: int):
    return (
        db.query(AssignWork)
        .filter(AssignWork.user_id == user_id)
        .all()
    )
