from sqlalchemy.orm import Session
from AutoRBI_Database.database.models import Component


# Normalize insulation to lowercase ("yes" or "no")
def normalize_insulation(value):
    if value is None:
        return None
    v = str(value).strip().lower()

    if v in ["yes", "y", "true", "1", "t"]:
        return "yes"
    if v in ["no", "n", "false", "0", "f"]:
        return "no"

    return None


# 1. Create component (Excel upload)
def create_component(
    db: Session,
    equipment_id: int,
    part_name: str,
    phase: str = None,
    fluid: str = None,
    material_spec: str = None,
    material_grade: str = None,
    insulation: str = None,
    design_temp: str = None,
    design_pressure: str = None,
    operating_temp: str = None,
    operating_pressure: str = None
):
    insulation = normalize_insulation(insulation)

    comp = Component(
        equipment_id=equipment_id,
        part_name=part_name,
        phase=phase,
        fluid=fluid,
        material_spec=material_spec,
        material_grade=material_grade,
        insulation=insulation,
        design_temp=design_temp,
        design_pressure=design_pressure,
        operating_temp=operating_temp,
        operating_pressure=operating_pressure
    )

    db.add(comp)

    db.flush()   # Assign component_id safely

    return comp


# 2. Get component by ID
def get_component_by_id(db: Session, component_id: int):
    return db.query(Component).filter(Component.component_id == component_id).first()


# 3. Get all components under an equipment
def get_components_by_equipment(db: Session, equipment_id: int):
    return db.query(Component).filter(Component.equipment_id == equipment_id).all()


# 4. Update component (extraction or correction)
def update_component(db: Session, component_id: int, updates: dict):
    comp = get_component_by_id(db, component_id)
    if not comp:
        return None

    for field, value in updates.items():
        if field == "insulation":
            value = normalize_insulation(value)
        if hasattr(comp, field):
            setattr(comp, field, value)

   
    db.flush()  # Save pending changes to transaction buffer

    return comp


# 5. Bulk update for ExcelManager (still no commits here)
def bulk_update_components(db: Session, component_updates: list):
    for upd in component_updates:
        comp = get_component_by_id(db, upd["component_id"])
        if comp:
            for field, value in upd.items():
                if field == "component_id":
                    continue
                if field == "insulation":
                    value = normalize_insulation(value)
                if hasattr(comp, field):
                    setattr(comp, field, value)

  
    db.flush()

    return True
