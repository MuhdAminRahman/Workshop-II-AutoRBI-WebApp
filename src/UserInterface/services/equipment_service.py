from typing import Dict, List, Optional
from models import Equipment, Component
import logging

logger = logging.getLogger(__name__)

class EquipmentService:
    """Business logic for equipment operations"""
    
    def __init__(self, excel_manager, extractor, log_callback: Optional[callable] = None):
        self.excel_manager = excel_manager
        self.extractor = extractor
        self.log_callback = log_callback or print
    
    def initialize_extraction(self) -> Dict[str, Equipment]:
        """Initialize extraction and read masterfile"""
        self.log_callback("📖 Reading masterfile...")
        equipment_map = self.excel_manager.read_masterfile()
        self.log_callback(f"✓ Found {len(equipment_map)} equipment in masterfile")
        return equipment_map
    
    def extract_single_equipment(
        self, 
        equipment_map: Dict[str, Equipment],
        equipment_number: str,
        images_dir: str
    ) -> Optional[Equipment]:
        """Extract data for a single equipment"""
        try:
            if equipment_number not in equipment_map:
                self.log_callback(f"⚠️ Equipment '{equipment_number}' not in masterfile")
                return None
            
            self.log_callback(f"▶ Processing: {equipment_number}")
            
            updated_map = self.extractor.process_and_update_single_equipment(
                equipment_map,
                equipment_number,
                images_dir
            )
            
            self.log_callback(f"✓ Completed: {equipment_number}")
            return updated_map.get(equipment_number)
        
        except Exception as e:
            logger.error(f"Error extracting {equipment_number}: {e}")
            self.log_callback(f"❌ Error extracting {equipment_number}: {e}")
            return None
    
    def save_equipment_data(
        self, 
        equipment_map: Dict[str, Equipment],
        user_id: str
    ) -> bool:
        """Save equipment data to Excel"""
        try:
            self.log_callback(f"💾 Saving {len(equipment_map)} equipment items...")
            success = self.excel_manager.save_to_excel_with_dict(equipment_map, user_id)
            
            if success:
                self.log_callback("✅ Save complete!")
            else:
                self.log_callback("❌ Save failed")
            
            return success
        
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            self.log_callback(f"❌ Error saving: {e}")
            return False
    
    def detect_changes(
        self,
        original_equipment: Equipment,
        updated_component_data: Dict[str, str]
    ) -> bool:
        """Detect if there are changes in component data"""
        for component in original_equipment.components:
            component_name = updated_component_data.get('parts', '')
            
            if component.component_name == component_name:
                # Check each field for changes
                fields_to_check = [
                    'fluid', 'material_type', 'spec', 'grade', 'insulation',
                    'design_temp', 'design_pressure', 
                    'operating_temp', 'operating_pressure'
                ]
                
                for field in fields_to_check:
                    ui_value = updated_component_data.get(field, '').strip()
                    current_value = str(component.get_existing_data_value(field) or '')
                    
                    if ui_value and ui_value != current_value:
                        return True
        
        return False