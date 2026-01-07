from sqlalchemy.orm import Session
from AutoRBI_Database.database.models import TypeMaterial


# 1. Insert a material (Admin only)
def create_material(db: Session, material_spec: str, material_type: str):
    item = TypeMaterial(
        material_spec=material_spec,
        material_type=material_type
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# 2. Get all materials
def get_all_materials(db: Session):
    return db.query(TypeMaterial).all()


# 3. Get material by spec
def get_material_by_spec(db: Session, material_spec: str):
    return db.query(TypeMaterial).filter(
        TypeMaterial.material_spec == material_spec
    ).first()


# 4. Update material type (rare, admin only)
def update_material_type(db: Session, material_spec: str, new_type: str):
    item = get_material_by_spec(db, material_spec)
    if not item:
        return None

    item.material_type = new_type
    db.commit()
    return item


# 5. Soft Delete? → NOT Recommended
# Type materials should NOT be deleted in real systems,
# because components depend on them.
