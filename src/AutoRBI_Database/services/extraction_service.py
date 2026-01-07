# services/extraction_service.py
"""
Used after uploading a PDF/JPG drawing when the engineer clicks "Extract".

What it does:
1. Updates component fields with extracted values.
2. Marks the equipment as extracted.
3. Saves a history log.

"""

from datetime import datetime
from sqlalchemy.orm import Session
from AutoRBI_Database.database.models import Equipment, Component
from AutoRBI_Database.database.crud import (
    get_equipment_by_id,
    get_component_by_id,
    create_history,
)


def extract_equipment_data(db: Session, equipment_id: int, user_id: int, extracted_values: dict):
    """
    Apply extracted OCR/AI values to component fields for an equipment.

    Parameters:
    -----------
    equipment_id : int
        ID of the equipment being extracted.

    user_id : int
        Engineer performing the extraction.

    extracted_values : dict
        Example:
        {
            12: {"fluid": "Air", "design_temp": "200"},
            13: {"material_spec": "SA-516", "insulation": "yes"}
        }

        Keys = component_id
        Values = dictionary of field updates
    """

    try:
        # -----------------------------------------------------
        # STEP 1 — Validate equipment exists
        # -----------------------------------------------------
        eq = get_equipment_by_id(db, equipment_id)
        if not eq:
            raise ValueError(f"Equipment {equipment_id} not found.")


        # -----------------------------------------------------
        # STEP 2 — Update all component extraction fields
        # -----------------------------------------------------
        for comp_id, updates in extracted_values.items():

            comp = get_component_by_id(db, comp_id)
            if not comp:
                raise ValueError(f"Component {comp_id} not found.")

            # Apply field updates
            for field, value in updates.items():
                if hasattr(comp, field):
                    setattr(comp, field, value)


        # -----------------------------------------------------
        # STEP 3 — Mark equipment as extracted
        # -----------------------------------------------------
        eq.user_id = user_id
        eq.extracted_date = datetime.utcnow()


        # -----------------------------------------------------
        # STEP 4 — Record extraction in work_history
        # -----------------------------------------------------
        create_history(
            db,
            work_id=eq.work_id,
            user_id=user_id,
            action_type="extract",
            equipment_id=equipment_id,
            description="Automated extraction completed."
        )


        # -----------------------------------------------------
        # STEP 5 — Commit ALL updates together
        # -----------------------------------------------------
        db.commit()
        return {"status": "success", "equipment_id": equipment_id}


    except Exception as e:
        # -----------------------------------------------------
        # STEP 6 — Rollback if ANYTHING fails
        # -----------------------------------------------------
        db.rollback()
        raise e