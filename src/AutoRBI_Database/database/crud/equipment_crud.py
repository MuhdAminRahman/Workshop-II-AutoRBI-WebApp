
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from AutoRBI_Database.database.models import Equipment
from datetime import datetime


# 1. Create equipment (Excel upload or manual creation)
def create_equipment(db: Session, work_id: int, equipment_no: str, pmt_no: str, description: str):
    equipment = Equipment(
        work_id=work_id,
        equipment_no=equipment_no,
        pmt_no=pmt_no,
        description=description
    )

    try:
        db.add(equipment)
        db.flush()
        return equipment


    except IntegrityError:
        db.rollback()
        raise ValueError(
            f"Equipment number '{equipment_no}' already exists in Work {work_id}. "
            "Equipment numbers must be unique within a single work."
        )


# 2. Get equipment by ID
def get_equipment_by_id(db: Session, equipment_id: int):
    return db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()


# 3. Get equipment by equipment number (global)
def get_equipment_by_no(db: Session, equipment_no: str):
    return db.query(Equipment).filter(Equipment.equipment_no == equipment_no).first()


# 4. Get all equipment in a Work
def get_equipment_by_work(db: Session, work_id: int):
    return db.query(Equipment).filter(Equipment.work_id == work_id).all()


# 5. Get all equipment (optional for admin/dashboard)
def get_all_equipment(db: Session):
    return db.query(Equipment).all()


# 6. Update drawing path (PDF upload)
def update_drawing_path(db: Session, equipment_id: int, path: str):
    equipment = get_equipment_by_id(db, equipment_id)
    if not equipment:
        return None

    equipment.drawing_path = path
    db.flush()
    return equipment



# 7. Mark equipment as extracted
def mark_extracted(db: Session, equipment_id: int, user_id: int):
    equipment = get_equipment_by_id(db, equipment_id)
    if not equipment:
        return None

    equipment.user_id = user_id
    equipment.extracted_date = datetime.utcnow()
    db.flush()
    return equipment


# 8. Update equipment info (admin/manual updates)
def update_equipment_info(db: Session, equipment_id: int, updates: dict):
    equipment = get_equipment_by_id(db, equipment_id)
    if not equipment:
        return None

    if "pmt_no" in updates:
        equipment.pmt_no = updates["pmt_no"]
    if "description" in updates:
        equipment.description = updates["description"]

    db.commit()
    return equipment
