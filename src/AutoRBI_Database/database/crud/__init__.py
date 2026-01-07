from .user_crud import *
from .work_crud import *
from .equipment_crud import *
from .component_crud import *
from .assign_work_crud import *
from .correction_log_crud import *
from .work_history_crud import *
from .material_crud import *

__all__ = [
    # User CRUD
    "create_user",
    "register_engineer",
    "get_user_by_id",
    "get_user_by_username",
    "get_all_users",
    "get_active_users",
    "admin_update_user",
    "engineer_update_self",
    "deactivate_user",
    "login_user",

    # Work CRUD
    "create_work",
    "get_work_by_id",
    "get_work_by_name",
    "get_all_works",
    "update_work_info",
    "update_work_status",
    "update_excel_path",
    "update_ppt_path",

    # Equipment CRUD
    "create_equipment",
    "get_equipment_by_id",
    "get_equipment_by_no",
    "get_equipment_by_work",
    "get_all_equipment",
    "update_drawing_path",
    "mark_extracted",
    "update_equipment_info",

    # Component CRUD
    "create_component",
    "get_component_by_id",
    "get_components_by_equipment",
    "update_component",
    "bulk_update_components",

    # Assign Work CRUD
    "assign_user_to_work",
    "unassign_user_from_work",
    "get_engineers_for_work",
    "get_works_for_user",

    # Correction Log CRUD
    "create_correction_log",
    "get_logs_for_equipment",
    "get_logs_for_user",

    # Work History CRUD
    "create_history",
    "get_history_for_work",
    "get_history_for_equipment",
    "get_history_for_user",

    # Material CRUD (missing earlier!)
    "create_material",
    "get_all_materials",
    "get_material_by_spec",
    "update_material_type",
]
