from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.equipment import Equipment
from app.models.component import Component
from app.models.work import Work
from app.models.user import User
from app.db.database import get_db
from app.dependencies import get_current_user
from app.services.permission_service import can_view, can_edit

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class ComponentCreate(BaseModel):
    component_name: str
    phase: Optional[str] = None
    fluid: Optional[str] = None
    material_spec: Optional[str] = None
    material_grade: Optional[str] = None
    insulation: Optional[str] = None
    design_temp: Optional[str] = None
    design_pressure: Optional[str] = None
    operating_temp: Optional[str] = None
    operating_pressure: Optional[str] = None


class ComponentUpdate(BaseModel):
    component_name: Optional[str] = None
    phase: Optional[str] = None
    fluid: Optional[str] = None
    material_spec: Optional[str] = None
    material_grade: Optional[str] = None
    insulation: Optional[str] = None
    design_temp: Optional[str] = None
    design_pressure: Optional[str] = None
    operating_temp: Optional[str] = None
    operating_pressure: Optional[str] = None


class ComponentResponse(BaseModel):
    id: int
    equipment_id: int
    component_name: str
    phase: Optional[str] = None
    fluid: Optional[str] = None
    material_spec: Optional[str] = None
    material_grade: Optional[str] = None
    insulation: Optional[str] = None
    design_temp: Optional[str] = None
    design_pressure: Optional[str] = None
    operating_temp: Optional[str] = None
    operating_pressure: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EquipmentCreate(BaseModel):
    work_id: int
    equipment_number: str
    pmt_number: Optional[str] = None
    description: Optional[str] = None
    components: Optional[List[ComponentCreate]] = None


class EquipmentUpdate(BaseModel):
    equipment_number: Optional[str] = None
    pmt_number: Optional[str] = None
    description: Optional[str] = None


class EquipmentResponse(BaseModel):
    id: int
    work_id: int
    equipment_number: str
    pmt_number: Optional[str] = None
    description: Optional[str] = None
    extracted_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    components: List[ComponentResponse] = []
    
    class Config:
        from_attributes = True


class BulkEquipmentImport(BaseModel):
    work_id: int
    equipment_list: List[EquipmentCreate]


# ============================================================================
# EQUIPMENT ENDPOINTS
# ============================================================================

@router.post("", response_model=EquipmentResponse)
async def create_equipment(
    payload: EquipmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create equipment with optional components in one call.
    Requires edit permission on work.
    
    Example:
        {
            "work_id": 1,
            "equipment_number": "E-001",
            "pmt_number": "PMT-123",
            "description": "Main pump",
            "components": [
                {
                    "component_name": "Impeller",
                    "phase": "Liquid",
                    "fluid": "Water"
                }
            ]
        }
    """
    # ✅ NEW: Permission check
    if not can_edit(db, payload.work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have permission to edit this work")
    
    # Verify work exists
    work = db.query(Work).filter(Work.id == payload.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    try:
        equipment = Equipment(
            work_id=payload.work_id,
            equipment_number=payload.equipment_number,
            pmt_number=payload.pmt_number,
            description=payload.description
        )
        db.add(equipment)
        db.flush()
        
        # Add components if provided
        if payload.components:
            for comp_data in payload.components:
                component = Component(
                    equipment_id=equipment.id,
                    **comp_data.dict()
                )
                db.add(component)
        
        db.commit()
        db.refresh(equipment)
        return EquipmentResponse.from_orm(equipment)
    
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Equipment number already exists for this work"
        )


@router.get("/work/{work_id}", response_model=List[EquipmentResponse])
async def list_equipment_by_work(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all equipment for a work.
    Requires view permission on work.
    """
    # ✅ NEW: Permission check
    if not can_view(db, work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have access to this work")
    
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    equipment = db.query(Equipment).filter(Equipment.work_id == work_id).all()
    return [EquipmentResponse.from_orm(e) for e in equipment]


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get equipment by ID with all components.
    Requires view permission on the equipment's work.
    """
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # ✅ NEW: Permission check
    if not can_view(db, equipment.work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have access to this work")
    
    return EquipmentResponse.from_orm(equipment)


@router.put("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update equipment.
    Requires edit permission on the equipment's work.
    """
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # ✅ NEW: Permission check
    if not can_edit(db, equipment.work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have permission to edit this work")
    
    try:
        update_data = payload.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(equipment, key, value)
        
        db.commit()
        db.refresh(equipment)
        return EquipmentResponse.from_orm(equipment)
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Equipment number already exists for this work"
        )


@router.delete("/{equipment_id}")
async def delete_equipment(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete equipment (cascade deletes all components).
    Requires edit permission on the equipment's work.
    """
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # ✅ NEW: Permission check
    if not can_edit(db, equipment.work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have permission to edit this work")
    
    db.delete(equipment)
    db.commit()
    
    return {"message": "Equipment deleted", "equipment_id": equipment_id}


@router.post("/bulk", response_model=List[EquipmentResponse])
async def bulk_import_equipment(
    payload: BulkEquipmentImport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk import equipment with components.
    Requires edit permission on work.
    
    Example:
        {
            "work_id": 1,
            "equipment_list": [
                {
                    "equipment_number": "E-001",
                    "pmt_number": "PMT-123",
                    "components": [...]
                },
                {
                    "equipment_number": "E-002",
                    "pmt_number": "PMT-124",
                    "components": [...]
                }
            ]
        }
    """
    # ✅ NEW: Permission check
    if not can_edit(db, payload.work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have permission to edit this work")
    
    # Verify work exists
    work = db.query(Work).filter(Work.id == payload.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    created_equipment = []
    
    try:
        for eq_data in payload.equipment_list:
            equipment = Equipment(
                work_id=payload.work_id,
                equipment_number=eq_data.equipment_number,
                pmt_number=eq_data.pmt_number,
                description=eq_data.description
            )
            db.add(equipment)
            db.flush()
            
            if eq_data.components:
                for comp_data in eq_data.components:
                    component = Component(
                        equipment_id=equipment.id,
                        **comp_data.dict()
                    )
                    db.add(component)
            
            created_equipment.append(equipment)
        
        db.commit()
        return [EquipmentResponse.from_orm(e) for e in created_equipment]
    
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="One or more equipment numbers already exist for this work"
        )


# ============================================================================
# COMPONENT ENDPOINTS
# ============================================================================

@router.post("/{equipment_id}/components", response_model=ComponentResponse)
async def create_component(
    equipment_id: int,
    payload: ComponentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a component for equipment.
    Requires edit permission on the equipment's work.
    """
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # ✅ NEW: Permission check
    if not can_edit(db, equipment.work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have permission to edit this work")
    
    component = Component(
        equipment_id=equipment_id,
        **payload.dict()
    )
    db.add(component)
    db.commit()
    db.refresh(component)
    
    return ComponentResponse.from_orm(component)


@router.get("/{equipment_id}/components", response_model=List[ComponentResponse])
async def list_components(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all components for equipment.
    Requires view permission on the equipment's work.
    """
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # ✅ NEW: Permission check
    if not can_view(db, equipment.work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have access to this work")
    
    components = db.query(Component).filter(Component.equipment_id == equipment_id).all()
    return [ComponentResponse.from_orm(c) for c in components]


@router.get("/components/{component_id}", response_model=ComponentResponse)
async def get_component(
    component_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get component by ID.
    Requires view permission on the equipment's work.
    """
    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    equipment = db.query(Equipment).filter(Equipment.id == component.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # ✅ NEW: Permission check
    if not can_view(db, equipment.work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have access to this work")
    
    return ComponentResponse.from_orm(component)


@router.put("/components/{component_id}", response_model=ComponentResponse)
async def update_component(
    component_id: int,
    payload: ComponentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a component.
    Requires edit permission on the equipment's work.
    """
    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    equipment = db.query(Equipment).filter(Equipment.id == component.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # ✅ NEW: Permission check
    if not can_edit(db, equipment.work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have permission to edit this work")
    
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(component, key, value)
    
    db.commit()
    db.refresh(component)
    
    return ComponentResponse.from_orm(component)


@router.delete("/components/{component_id}")
async def delete_component(
    component_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a component.
    Requires edit permission on the equipment's work.
    """
    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    equipment = db.query(Equipment).filter(Equipment.id == component.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # ✅ NEW: Permission check
    if not can_edit(db, equipment.work_id, current_user.id):
        raise HTTPException(status_code=403, detail="You don't have permission to edit this work")
    
    db.delete(component)
    db.commit()
    
    return {"message": "Component deleted", "component_id": component_id}


@router.put("/components/bulk", response_model=List[ComponentResponse])
async def bulk_update_components(
    payload: List[ComponentUpdate],
    component_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update multiple components at once.
    Requires edit permission on the equipment's work.
    
    Note: component_ids and payload must be same length.
    """
    if len(component_ids) != len(payload):
        raise HTTPException(
            status_code=400,
            detail="component_ids and payload must have same length"
        )
    
    updated_components = []
    
    for component_id, update_data in zip(component_ids, payload):
        component = db.query(Component).filter(Component.id == component_id).first()
        if not component:
            raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
        
        equipment = db.query(Equipment).filter(Equipment.id == component.equipment_id).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        # ✅ NEW: Permission check (only on first iteration to avoid redundant checks)
        if component_id == component_ids[0]:
            if not can_edit(db, equipment.work_id, current_user.id):
                raise HTTPException(status_code=403, detail="You don't have permission to edit this work")
        
        data = update_data.dict(exclude_unset=True)
        for key, value in data.items():
            setattr(component, key, value)
        
        updated_components.append(component)
    
    db.commit()
    return [ComponentResponse.from_orm(c) for c in updated_components]