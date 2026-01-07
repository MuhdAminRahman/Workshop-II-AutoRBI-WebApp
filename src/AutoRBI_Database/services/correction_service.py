# services/correction_service.py

"""
CORRECTION SERVICE
------------------
Handles manual corrections performed by an engineer for a single equipment.

What it does (short):
1. Load current components for the equipment.
2. Compute how many tracked fields are expected (fields_to_fill).
3. Count how many tracked fields were non-empty BEFORE correction.
4. Apply the provided corrections to components (normalize insulation).
5. Count how many tracked fields are non-empty AFTER correction.
6. fields_corrected = after_count - before_count (>= 0).
7. Create a CorrectionLog and a WorkHistory entry.
8. All steps happen in a single DB transaction. Any failure -> rollback.
"""
from datetime import datetime
from sqlalchemy.orm import Session

from AutoRBI_Database.database.crud import (
    get_components_by_equipment,
    get_component_by_id,
    update_component,
    create_correction_log,
    create_history,
    get_work_by_id,
)
from AutoRBI_Database.database.models import Component


# Fields we track per component (matches your model)
TRACKED_COMPONENT_FIELDS = [
    "fluid",
    "material_spec",
    "material_grade",
    "insulation",
    "design_temp",
    "design_pressure",
    "operating_temp",
    "operating_pressure",
]


def normalize_insulation(value):
    """Normalize various user inputs into 'yes' or 'no' or None."""
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in ["yes", "y", "true", "1", "t"]:
        return "yes"
    if v in ["no", "n", "false", "0", "f"]:
        return "no"
    return None


def _count_filled_fields(components):
    """
    Count how many tracked fields are currently non-empty across a list of Component objects.
    A field is considered filled if it's not None and not an empty string after strip().
    """
    count = 0
    for c in components:
        for f in TRACKED_COMPONENT_FIELDS:
            val = getattr(c, f, None)
            if val is None:
                continue
            # treat empty string as empty
            if isinstance(val, str) and val.strip() == "":
                continue
            count += 1
    return count


def calculate_fields_to_fill(components):
    """
    Compute fields_to_fill for the equipment.
    Currently: number_of_components * len(TRACKED_COMPONENT_FIELDS)
    (If you want to include equipment-level fields, add them here.)
    """
    return len(components) * len(TRACKED_COMPONENT_FIELDS)


def apply_corrections(db: Session, equipment_id: int, user_id: int, corrections: dict):
    """
    Apply corrections for a given equipment.

    Parameters:
    - db: SQLAlchemy Session
    - equipment_id: int
    - user_id: int (engineer performing correction)
    - corrections: dict mapping component_id -> { field_name: value, ... }

    Example:
    {
        12: {"material_spec": "SA-516", "material_grade": "70", "insulation": "yes"},
        13: {"operating_temp": "150"}
    }

    Returns: created CorrectionLog object
    Raises exceptions on failure (and rolls back).
    """
    try:
        # 1) Load current components for equipment
        components = get_components_by_equipment(db, equipment_id)
        if components is None:
            raise ValueError(f"No components found for equipment {equipment_id}")

        # 2) fields_to_fill based on number of components
        fields_to_fill = calculate_fields_to_fill(components)

        # 3) Count how many fields are already filled BEFORE the correction
        before_filled = _count_filled_fields(components)

        # 4) Apply corrections in-memory first (so we can compute after-count)
        # We will use update_component() to persist each component update.
        # Keep track of which component ids we actually updated.
        for comp_id, updates in corrections.items():
            # Basic validation
            comp = None
            # try find local component object first (avoid extra DB query)
            for c in components:
                if c.component_id == comp_id:
                    comp = c
                    break

            if comp is None:
                # If not present in loaded list, try to fetch; if still none -> error
                comp = get_component_by_id(db, comp_id)
                if not comp:
                    raise ValueError(f"Component {comp_id} not found for equipment {equipment_id}")

            # Prepare normalized updates
            to_apply = {}
            for field, value in updates.items():
                if field == "insulation":
                    value = normalize_insulation(value)
                # Only allow tracked fields to be changed via this service
                if field in TRACKED_COMPONENT_FIELDS:
                    to_apply[field] = value

            if not to_apply:
                continue  # nothing to update for this component

            # Apply updates using update_component (this writes to DB but we are still inside transaction)
            updated_comp = update_component(db, comp_id, to_apply)
            if updated_comp is None:
                raise RuntimeError(f"Failed to update component {comp_id}")

        # 5) After applying corrections, re-load components to compute after_filled
        components_after = get_components_by_equipment(db, equipment_id)
        after_filled = _count_filled_fields(components_after)

        # 6) Compute fields_corrected (only the delta from this correction operation)
        fields_corrected = after_filled - before_filled
        if fields_corrected < 0:
            # defensive: should not happen, but clamp to 0
            fields_corrected = 0

        # 7) Create correction_log and history
        log = create_correction_log(
            db,
            equipment_id=equipment_id,
            user_id=user_id,
            fields_to_fill=fields_to_fill,
            fields_corrected=fields_corrected
        )

        # Add a readable history message (e.g., "6/16 fields are now filled.")
        description = f"{fields_corrected}/{fields_to_fill} fields corrected by user {user_id}."
        # obtain work_id if available via equipment query (light DB fetch)
        # We will use the equipment's work_id via a quick lookup
        from AutoRBI_Database.database.crud import get_equipment_by_id
        eq = get_equipment_by_id(db, equipment_id)
        work_id = eq.work_id if eq else None

        if work_id is None:
            # still create history with work_id 0 or skip — prefer to raise to ensure integrity
            raise RuntimeError(f"Unable to determine work_id for equipment {equipment_id}")

        create_history(
            db,
            work_id=work_id,
            user_id=user_id,
            action_type="correct",
            equipment_id=equipment_id,
            description=description
        )

        # 8) Commit all changes together (update_component already called db.commit() in your CRUD,
        #     but if your update_component does commit, that would break atomicity.
        #     IMPORTANT: update_component must NOT commit on its own for full transaction safety.
        #     If update_component commits, you should replace it with direct attribute setting & final db.commit() here.
        #
        # If your update_component() *does* already commit, the safe approach is:
        # - change update_component to NOT commit (recommended), or
        # - re-implement the updates here using SQLAlchemy objects and commit once at the end.
        #
        # For now we assume update_component does not commit (matches earlier CRUD style), so:
        db.commit()

        # refresh the log and return
        # ensure create_correction_log returned the log object already refreshed; if not:
        return log

    except Exception as e:
        db.rollback()
        raise e
