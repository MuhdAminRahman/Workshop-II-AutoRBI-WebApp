# File: UserInterface/services/database_service.py
"""
Database Service Layer for Equipment Management
Handles all database operations for new_work.py
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Import database models
from AutoRBI_Database.database.models.equipment import Equipment as DBEquipment
from AutoRBI_Database.database.models.component import Component as DBComponent
from AutoRBI_Database.database.models.type_material import TypeMaterial
from AutoRBI_Database.database.models.work_history import WorkHistory
from AutoRBI_Database.database.models.correction_log import CorrectionLog
from AutoRBI_Database.services.work_service import get_assigned_works,get_work_details

# Import local models
from models.equipment import Equipment
from models.equipment_component import Component


class DatabaseService:
    """Service for equipment database operations"""
    
    @staticmethod
    def save_equipment_with_components(
        db: Session,
        work_id: int,
        user_id: int,
        equipment: Equipment,
        drawing_path: str
    ) -> Optional[DBEquipment]:
        """
        Save equipment and its components to database.
        Returns the created Equipment DB object or None on failure.
        """
        try:
            # Check if equipment already exists for this work
            existing = db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id,
                DBEquipment.equipment_no == equipment.equipment_number
            ).first()
            
            if existing:
                # Update existing equipment
                db_equipment = existing
                db_equipment.user_id = user_id
                db_equipment.pmt_no = equipment.pmt_number or ""
                db_equipment.description = equipment.equipment_description or ""
                db_equipment.drawing_path = drawing_path
                db_equipment.extracted_date = datetime.utcnow()
            else:
                # Create new equipment
                db_equipment = DBEquipment(
                    work_id=work_id,
                    user_id=user_id,
                    equipment_no=equipment.equipment_number,
                    pmt_no=equipment.pmt_number or "",
                    description=equipment.equipment_description or "",
                    drawing_path=drawing_path,
                    extracted_date=datetime.utcnow()
                )
                db.add(db_equipment)
            
            # Flush to get equipment_id
            db.flush()
            
            # Save components
            for component in equipment.components:
                DatabaseService._save_component(db, db_equipment.equipment_id, component)
            
            db.commit()
            return db_equipment
            
        except IntegrityError as e:
            db.rollback()
            print(f"IntegrityError saving equipment {equipment.equipment_number}: {e}")
            return None
        except Exception as e:
            db.rollback()
            print(f"Error saving equipment {equipment.equipment_number}: {e}")
            return None
    
    @staticmethod
    def _save_component(db: Session, equipment_id: int, component: Component) -> Optional[DBComponent]:
        """Save a single component to database"""
        try:
            # Check if component exists
            existing = db.query(DBComponent).filter(
                DBComponent.equipment_id == equipment_id,
                DBComponent.part_name == component.component_name
            ).first()
            
            # Get existing data values
            existing_data = component.existing_data
            
            if existing:
                # Update existing component
                db_component = existing
            else:
                # Create new component
                db_component = DBComponent(
                    equipment_id=equipment_id,
                    part_name=component.component_name
                )
                db.add(db_component)
            
            # Update component fields
            db_component.phase = component.phase
            db_component.fluid = existing_data.get('fluid')
            all_material_specs = db.query(TypeMaterial).all()
            for mat in all_material_specs:
                if mat.material_spec == existing_data.get('spec'):
                    db_component.material_spec = mat.material_spec
                    break
            db_component.material_grade = str(existing_data.get('grade'))
            
            # Handle insulation (convert to enum-compatible value)
            insulation_value = existing_data.get('insulation', '').lower()
            if insulation_value in ['yes', 'no']:
                db_component.insulation = insulation_value
            
            # Store temperatures/pressures as strings (as per schema)
            db_component.design_temp = existing_data.get('design_temp')
            db_component.design_pressure = existing_data.get('design_pressure')
            db_component.operating_temp = str(existing_data.get('operating_temp'))
            db_component.operating_pressure = str(existing_data.get('operating_pressure'))
            
            return db_component
            
        except Exception as e:
            print(f"Error saving component {component.component_name}: {e}")
            return None
    
    @staticmethod
    def log_work_history(
        db: Session,
        work_id: int,
        user_id: int,
        action_type: str,
        equipment_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Log an action to work history.
        
        Action types:
        - upload_pdf: PDF uploaded
        - extract: Data extracted from PDF
        - correct: Data corrected by user
        - generate_excel: Excel file generated
        - generate_ppt: PowerPoint generated
        """
        try:
            history_entry = WorkHistory(
                work_id=work_id,
                user_id=user_id,
                equipment_id=equipment_id,
                action_type=action_type,
                description=description,
                timestamp=datetime.utcnow()
            )
            db.add(history_entry)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error logging work history: {e}")
            return False
    
    @staticmethod
    def log_correction(
        db: Session,
        equipment_id: int,
        user_id: int,
        fields_to_fill: int,
        fields_corrected: int
    ) -> bool:
        """Log data correction to correction_log table"""
        try:
            correction_entry = CorrectionLog(
                equipment_id=equipment_id,
                user_id=user_id,
                fields_to_fill=fields_to_fill,
                fields_corrected=fields_corrected,
                timestamp=datetime.utcnow()
            )
            db.add(correction_entry)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error logging correction: {e}")
            return False
    
    @staticmethod
    def get_equipment_by_work_and_number(
        db: Session,
        work_id: int,
        equipment_no: str
    ) -> Optional[DBEquipment]:
        """Get equipment by work ID and equipment number"""
        try:
            return db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id,
                DBEquipment.equipment_no == equipment_no
            ).first()
        except Exception as e:
            print(f"Error getting equipment: {e}")
            return None
    
    @staticmethod
    def count_correction_fields(
        original_component: Component,
        updated_data: Dict[str, str]
    ) -> Tuple[int, int]:
        """
        Count fields that needed filling and were corrected.
        
        Returns:
            (fields_to_fill, fields_corrected)
        """
        fields_to_check = [
            'fluid', 'type', 'spec', 'grade', 'insulation',
            'design_temp', 'design_pressure',
            'operating_temp', 'operating_pressure'
        ]
        
        fields_to_fill = 0
        fields_corrected = 0
        
        for field in fields_to_check:
            original_value = original_component.get_existing_data_value(field)
            updated_value = updated_data.get(field, '').strip()
            
            # Field needed filling if it was empty
            if not original_value:
                fields_to_fill += 1
                
                # Field was corrected if it now has a value
                if updated_value:
                    fields_corrected += 1
        
        return fields_to_fill, fields_corrected
    
    @staticmethod
    def batch_save_equipment(
        db: Session,
        work_id: int,
        user_id: int,
        equipment_map: Dict[str, Equipment],
        drawing_paths: Dict[str, str]
    ) -> Tuple[int, int]:
        """
        Batch save multiple equipment items.
        
        Returns:
            (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0
        
        for eq_no, equipment in equipment_map.items():
            drawing_path = drawing_paths.get(eq_no, "")
            
            result = DatabaseService.save_equipment_with_components(
                db, work_id, user_id, equipment, drawing_path
            )
            
            if result:
                success_count += 1
            else:
                failure_count += 1
        
        return success_count, failure_count
    
    @staticmethod
    def update_equipment_data(db, equipment_id: int, equipment):
        """Update equipment data in database with corrected values"""
        # This is a simplified example - adjust based on your schema
        from AutoRBI_Database.database.models import Equipment as DBEquipment
        
        db_equipment = db.query(DBEquipment).filter(DBEquipment.equipment_id == equipment_id).first()
        if db_equipment:
            # Update fields based on your schema
            # You'll need to map the equipment object to your database model
            # Example:
            db_equipment.equipment_number = equipment.equipment_number
            db_equipment.pmt_number = equipment.pmt_number
            db_equipment.equipment_description = equipment.equipment_description
            
            # Update component data if your schema supports it
            # This part depends on your database structure
            
            db.commit()
            return True
        return False

    @staticmethod
    def get_equipment_id_by_equipment_number(
        db: Session,
        work_id: int,
        equipment_no: str
    ) -> Optional[int]:
        """Get equipment ID by work ID and equipment number"""
        try:
            equipment = db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id,
                DBEquipment.equipment_no == equipment_no
            ).first()
            return equipment.equipment_id if equipment else None
        except Exception as e:
            print(f"Error getting equipment ID: {e}")
            return None

    @staticmethod
    def get_total_equipment_count_for_all_works(
        db: Session,
        user_id: int
    ) -> int:
        """Get total equipment count across all assigned works for a user"""
        try:
            assigned_works = get_assigned_works(db, user_id)
            total_count = 0
            
            for work in assigned_works:
                equipment_count = db.query(DBEquipment).filter(
                    DBEquipment.work_id == work.work_id
                ).count()
                total_count += equipment_count
            
            return total_count
        except Exception as e:
            print(f"Error getting total equipment count: {e}")
            return 0

    @staticmethod
    def get_work_completion_percentage(
        db: Session,
        user_id: int
    ) -> Dict[int, float]:
        """
        Calculate completion percentage for all works assigned to a user.
        
        Args:
            db: Database session
            user_id: User ID to get assigned works for
        
        Returns:
            Dict[int, float]: Dictionary with work_id as key and completion percentage (0-100) as value
        """
        try:
            from AutoRBI_Database.database.models.assign_work import AssignWork
            from AutoRBI_Database.database.models.work import Work
            
            # Get all works assigned to the user
            works = db.query(Work).join(
                AssignWork, Work.work_id == AssignWork.work_id
            ).filter(
                AssignWork.user_id == user_id
            ).all()
            
            if not works:
                return {}  # No works assigned
            
            # Calculate completion for each work
            completion_dict = {}
            for work in works:
                completion = DatabaseService._calculate_single_work_completion(db, work.work_id)
                completion_dict[work.work_id] = completion
            
            return completion_dict
            
        except Exception as e:
            print(f"Error calculating work completion percentage: {e}")
            return {}

    @staticmethod
    def _calculate_single_work_completion(db: Session, work_id: int) -> float:
        """
        Calculate completion percentage for a single work.
        
        This is an internal helper method.
        """
        try:
            # Get all equipment for this work
            equipment_list = db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id
            ).all()
            
            if not equipment_list:
                return 0.0  # No equipment means 0% completion
            
            total_score = 0
            achieved_score = 0
            
            # Define field weights (adjust based on importance)
            equipment_field_weights = {
                'pmt_no': 1.0,
                'description': 1.0,
                'drawing_path': 0.5,  # Optional field
                'extracted_date': 1.0  # Important - indicates extraction happened
            }
            
            component_field_weights = {
                'part_name': 2.0,  # Required field
                'phase': 1.0,
                'fluid': 1.0,
                'material_spec': 1.0,
                'material_grade': 1.0,
                'insulation': 1.0,
                'design_temp': 1.0,
                'design_pressure': 1.0,
                'operating_temp': 1.0,
                'operating_pressure': 1.0
            }
            
            for equipment in equipment_list:
                # Calculate equipment score
                for field_name, weight in equipment_field_weights.items():
                    total_score += weight
                    field_value = getattr(equipment, field_name, None)
                    if field_value and str(field_value).strip():
                        achieved_score += weight
                
                # Get components for this equipment
                components = db.query(DBComponent).filter(
                    DBComponent.equipment_id == equipment.equipment_id
                ).all()
                
                # If no components, still count equipment fields
                if not components:
                    # Add base component weight to indicate no components yet
                    total_score += 1.0  # Small penalty for no components
                    continue
                
                # Calculate component scores
                for component in components:
                    for field_name, weight in component_field_weights.items():
                        total_score += weight
                        field_value = getattr(component, field_name, None)
                        if field_value and str(field_value).strip():
                            achieved_score += weight
            
            if total_score == 0:
                return 0.0
            
            percentage = (achieved_score / total_score) * 100
            return round(percentage, 2)
            
        except Exception as e:
            print(f"Error calculating completion for work {work_id}: {e}")
            return 0.0

    @staticmethod
    def get_fully_extracted_equipment_count(db: Session,user_id: Optional[int] = None,work_id: Optional[int] = None) -> int:
        """
        Get the number of equipment that is completely extracted across all works.
        
        Criteria for "completely extracted":
        1. Equipment has extracted_date set
        2. All mandatory fields in Equipment table are filled
        3. Equipment has at least one component
        4. All mandatory fields in Component table are filled for each component
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by assigned works
            work_id: Optional work ID to filter by specific work
            
        Returns:
            int: Count of fully extracted equipment
        """
        try:
            from AutoRBI_Database.database.models.assign_work import AssignWork
            
            # Build the base query for equipment
            query = db.query(DBEquipment)
            
            # Filter by work_id if provided
            if work_id:
                query = query.filter(DBEquipment.work_id == work_id)
            # Filter by user_id if provided (only show assigned works)
            elif user_id:
                # Get work IDs assigned to this user
                assigned_work_ids = db.query(AssignWork.work_id).filter(
                    AssignWork.user_id == user_id
                ).all()
                assigned_work_ids = [work_id[0] for work_id in assigned_work_ids]
                
                if not assigned_work_ids:
                    return 0
                    
                query = query.filter(DBEquipment.work_id.in_(assigned_work_ids))
            
            # Get all equipment matching the filter
            all_equipment = query.all()
            
            if not all_equipment:
                return 0
            
            fully_extracted_count = 0
            
            # Define mandatory fields for Equipment
            equipment_mandatory_fields = [
                'pmt_no', 'description'  # equipment_no is always required (part of PK/filter)
            ]
            
            # Define mandatory fields for Component
            component_mandatory_fields = [
                'part_name',  # This is always required (nullable=False in schema)
                # Add other fields that you consider mandatory for extraction
                'phase', 'fluid', 'material_spec', 'material_grade',
                'insulation', 'design_temp', 'design_pressure',
                'operating_temp', 'operating_pressure'
            ]
            
            for equipment in all_equipment:
                # Check 1: Equipment has extracted_date
                if not equipment.extracted_date:
                    continue
                
                # Check 2: All mandatory equipment fields are filled
                equipment_complete = True
                for field_name in equipment_mandatory_fields:
                    field_value = getattr(equipment, field_name, None)
                    if not field_value or not str(field_value).strip():
                        equipment_complete = False
                        break
                
                if not equipment_complete:
                    continue
                
                # Check 3: Equipment has at least one component
                components = db.query(DBComponent).filter(
                    DBComponent.equipment_id == equipment.equipment_id
                ).all()
                
                if not components:
                    continue  # No components means not fully extracted
                
                # Check 4: All mandatory component fields are filled for each component
                all_components_complete = True
                for component in components:
                    for field_name in component_mandatory_fields:
                        field_value = getattr(component, field_name, None)
                        if not field_value or not str(field_value).strip():
                            all_components_complete = False
                            break
                    
                    if not all_components_complete:
                        break
                
                if all_components_complete:
                    fully_extracted_count += 1
            
            return fully_extracted_count
            
        except Exception as e:
            print(f"Error counting fully extracted equipment: {e}")
            return 0

    @staticmethod
    def calculate_average_health_score(
        db: Session,
        user_id: int
    ) -> float:
        """
        Calculate average health score for all equipment across user's assigned works.
        
        Uses the same RBI health calculation as analytics.py:
        Health Score = (Extraction Rate × 0.4) + (Completeness Rate × 0.4) + (Quality Score × 0.2)
        
        Where:
        - Extraction Rate: Percentage of equipment with extracted_date set
        - Completeness Rate: Percentage of critical fields filled (fluid, material_spec, design_temp, design_pressure)
        - Quality Score: 20 points base, minus 2 points per correction (max penalty 20)
        
        Returns:
            float: Average health score (0-100)
        """
        try:
            from AutoRBI_Database.database.models.assign_work import AssignWork
            from AutoRBI_Database.database.models.work import Work
            
            # Get all works assigned to the user
            works = db.query(Work).join(
                AssignWork, Work.work_id == AssignWork.work_id
            ).filter(
                AssignWork.user_id == user_id
            ).all()
            
            if not works:
                return 0.0
            
            total_health_score = 0
            work_count = 0
            
            # Calculate health score for each work
            for work in works:
                work_health = DatabaseService._calculate_work_health_score(db, work.work_id)
                total_health_score += work_health
                work_count += 1
            
            if work_count == 0:
                return 0.0
            
            average_health = total_health_score / work_count
            return round(average_health, 1)
            
        except Exception as e:
            print(f"Error calculating average health score: {e}")
            return 0.0
    
    @staticmethod
    def _calculate_work_health_score(db: Session, work_id: int) -> float:
        """
        Calculate health score for a single work using RBI assessment factors.
        
        Health Score = (Extraction Rate × 0.4) + (Completeness Rate × 0.4) + (Quality Score × 0.2)
        
        Returns:
            float: Health score (0-100)
        """
        try:
            # Get all equipment for this work
            total_eq = db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id
            ).count()
            
            if total_eq == 0:
                return 0.0
            
            # 1. Calculate extraction rate
            extracted_eq = db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id,
                DBEquipment.extracted_date.isnot(None)
            ).count()
            
            extraction_rate = (extracted_eq / total_eq * 100) if total_eq > 0 else 0
            
            # 2. Calculate completeness rate for critical fields
            critical_fields = ['fluid', 'material_spec', 'design_temp', 'design_pressure']
            
            all_components = db.query(DBComponent).join(DBEquipment).filter(
                DBEquipment.work_id == work_id
            ).all()
            
            if not all_components:
                # No components means incomplete data
                completeness_rate = 0.0
            else:
                filled_critical = sum(
                    1 for comp in all_components
                    for field in critical_fields
                    if getattr(comp, field)
                )
                
                total_critical = len(all_components) * len(critical_fields)
                completeness_rate = (filled_critical / total_critical * 100) if total_critical > 0 else 0
            
            # 3. Calculate quality score (data corrections penalty)
            correction_count = db.query(CorrectionLog).join(DBEquipment).filter(
                DBEquipment.work_id == work_id
            ).count()
            
            # Quality base is 20 points, minus 2 per correction (max penalty is 20)
            correction_penalty = min(20, correction_count * 2)
            quality_score = 20 - correction_penalty
            
            # 4. Calculate final health score
            health_score = (
                (extraction_rate * 0.4) +
                (completeness_rate * 0.4) +
                quality_score
            )
            
            return round(health_score, 1)
            
        except Exception as e:
            print(f"Error calculating health score for work {work_id}: {e}")
            return 0.0