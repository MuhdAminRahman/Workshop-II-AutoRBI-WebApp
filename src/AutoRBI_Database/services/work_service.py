# services/work_service.py

"""
This service handles creating a Work and inserting all related Equipment
and Components in one safe transaction.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from AutoRBI_Database.database.models import Work, Equipment, Component
from AutoRBI_Database.database.crud import (
    create_history,
    get_works_for_user,
    get_work_by_id,
)


def create_work_with_items(
    db: Session, work_name: str, description: str, parsed_equipment: list, user_id: int
):

    try:
        # --------------------------------------------------------------
        # 1. Create the Work (NOT committed yet)
        # --------------------------------------------------------------
        work = Work(
            work_name=work_name,
            description=description,
            status="In progress",
            created_at=datetime.utcnow(),
        )

        db.add(work)
        db.flush()
        # flush gives the work a work_id WITHOUT committing the transaction

        # --------------------------------------------------------------
        # 2. Insert Equipment + Components
        # --------------------------------------------------------------
        for eq in parsed_equipment:

            # Insert Equipment
            equipment = Equipment(
                work_id=work.work_id,
                equipment_no=eq["equipment_no"],
                pmt_no=eq["pmt_no"],
                description=eq["description"],
            )
            db.add(equipment)
            db.flush()  # assigns equipment_id

            # Insert Components for this Equipment
            for comp in eq.get("components", []):
                component = Component(
                    equipment_id=equipment.equipment_id,
                    part_name=comp["part_name"],
                    phase=comp.get("phase"),
                )
                db.add(component)

        # --------------------------------------------------------------
        # 3. Insert Work History
        # --------------------------------------------------------------
        create_history(
            db,
            work_id=work.work_id,
            user_id=user_id,
            action_type="create_work",
            description=f"Work '{work_name}' created",
        )

        # --------------------------------------------------------------
        # 4. Commit ALL changes together
        # --------------------------------------------------------------
        db.commit()
        db.refresh(work)
        return work

    except Exception as e:
        # --------------------------------------------------------------
        # 5. If ANYTHING fails → rollback ALL changes
        # --------------------------------------------------------------
        db.rollback()
        raise e


def get_assigned_works(db: Session, user_id: int):
    """Get all works assigned to a specific user"""
    works = get_works_for_user(db, user_id)
    return works


def get_work_details(db: Session, work_id: int):
    """Get detailed information about a specific work, including equipment and components"""
    workdetails = get_work_by_id(db, work_id)
    return workdetails
