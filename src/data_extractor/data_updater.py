import logging
from typing import Dict, List
from models import Equipment

logger = logging.getLogger(__name__)

class DataUpdater:
    """Handles updating equipment with extracted data"""
    
    def __init__(self, extraction_rules, log_callback=None):
        self.rules = extraction_rules
        self.missing_equipment = set()  # Track equipment numbers with missing data
        self.log_callback = log_callback
    
    def update_equipment(self, equipment_map: Dict[str, Equipment], extracted_data: Dict[str, Dict[str, any]]):
        """Update equipment with extracted data"""
        self.missing_equipment.clear()  # Reset
        
        for equipment_number, data in extracted_data.items():
            equipment = equipment_map.get(equipment_number)
            if not equipment:
                self.log_warning(f"Equipment {equipment_number} not found in map")
                continue
            
            components_data = data.get('components_data', [])
            
            # If no data was extracted at all, mark for retry
            if not components_data:
                self.missing_equipment.add(equipment_number)
                self.log_warning(f"⚠️ No data extracted for {equipment_number} - will retry")
                continue
            
            for comp_data in components_data:
                self._update_component(equipment, comp_data, equipment_number)
            
            # Check if equipment still has empty fields after update
            if self._has_empty_fields(equipment):
                self.missing_equipment.add(equipment_number)
                self.log_info(f"⚠️ {equipment_number} still has missing data - will retry")
    
    def _has_empty_fields(self, equipment: Equipment) -> bool:
        """Check if equipment has any empty/None fields after update"""
        equipment_number = equipment.equipment_number
        
        # Get required fields for this equipment type
        required_fields = self._get_required_fields(equipment_number)
        
        for component in equipment.components:
            for field in required_fields:
                if not component.get_existing_data_value(field):
                    return True
        return False
    
    def _get_required_fields(self, equipment_number: str) -> List[str]:
        """Get list of required fields for this equipment based on rules"""
        # V-001 and H-001 only need insulation
        if equipment_number in self.rules.INSULATION_ONLY_EQUIPMENT:
            return ['insulation']
        
        # H-002, H-003, H-004 skip operating pressure/temperature
        elif equipment_number in self.rules.SKIP_OPERATING_PRESSURE_TEMPERATURE:
            return ['fluid', 'spec', 'grade', 'insulation', 'design_temp', 'design_pressure']
        
        # Default: all fields required
        else:
            return ['fluid', 'spec', 'grade', 'insulation', 
                   'design_temp', 'design_pressure', 
                   'operating_temp', 'operating_pressure']
    
    def _update_component(self, equipment: Equipment, comp_data: Dict, equipment_number: str):
        """Update a single component with extracted data"""
        component = equipment.get_component(comp_data['component_name'])
        if not component:
            self.log_warning(f"Component {comp_data['component_name']} not found in equipment {equipment_number}")
            return
        
        updates = self._build_updates(comp_data, equipment_number)
        if updates:
            try:
                component.update_existing_data(updates)
                self.log_info(f" Updated {equipment_number} - {comp_data['component_name']}: {', '.join(updates.keys())}")
            except KeyError as e:
                self.log_error(f" Invalid data field {e} for {equipment_number} - {comp_data['component_name']}")
    
    def _build_updates(self, comp_data: Dict, equipment_number: str) -> Dict:
        """Build updates dictionary from extracted component data"""
        updates = {}
        
        skip_operating_pressure_temp = equipment_number in self.rules.SKIP_OPERATING_PRESSURE_TEMPERATURE
        insulation_only = equipment_number in self.rules.INSULATION_ONLY_EQUIPMENT
        
        # For insulation-only equipment, only update insulation
        if insulation_only:
            if self._is_valid_value(comp_data['insulation']):
                updates['insulation'] = comp_data['insulation']
            return updates
        
        # For all other equipment, extract fluid, materials, etc.
        if self._is_valid_value(comp_data['fluid']):
            updates['fluid'] = comp_data['fluid']
        
        if self._is_valid_value(comp_data['material_specification']):
            updates['spec'] = comp_data['material_specification']
        if self._is_valid_value(comp_data['material_grade']):
            updates['grade'] = comp_data['material_grade']
        
        if self._is_valid_value(comp_data['insulation']):
            updates['insulation'] = comp_data['insulation']
        
        # Handle pressure and temperature based on skip rules
        if skip_operating_pressure_temp:
            # Only extract design pressure and temperature
            if self._is_valid_value(comp_data['design_temperature']):
                updates['design_temp'] = self._convert_value(comp_data['design_temperature'])
            if self._is_valid_value(comp_data['design_pressure']):
                updates['design_pressure'] = self._convert_value(comp_data['design_pressure'])
        else:
            # Extract all pressure and temperature fields
            pressure_temp_fields = {
                'design_temperature': 'design_temp',
                'design_pressure': 'design_pressure', 
                'operating_temperature': 'operating_temp',
                'operating_pressure': 'operating_pressure'
            }
            
            for source_field, target_field in pressure_temp_fields.items():
                if self._is_valid_value(comp_data[source_field]):
                    updates[target_field] = self._convert_value(comp_data[source_field])
        
        return updates
    
    def _is_valid_value(self, value: str) -> bool:
        """
        Check if extracted value is valid and not an error message
        Returns False for: NOT_FOUND, empty strings, or text containing error phrases
        """
        if not value or value == 'NOT_FOUND' or value == '':
            return False
        
        # Convert to lowercase for case-insensitive checking
        value_lower = value.lower()
        
        # Reject values wrapped in brackets (AI's way of saying "uncertain")
        if value.startswith('[') and value.endswith(']'):
            return False
        
        # Check for common error phrases that AI might return
        error_phrases = [
            'not found',
            'no corresponding',
            'could not find',
            'unable to locate',
            'cannot find',
            'not located',
            'not present',
            'not available',
            'not visible',
            'not clearly',
            'not legible',
            'cannot be determined',
            'unclear',
            'illegible',
            'missing',
            'n/a',
            'none found',
            'specifications present but',
            'material specifications',
            'grade specifications',
        ]
        
        for phrase in error_phrases:
            if phrase in value_lower:
                return False
        
        return True
    
    def _convert_value(self, value: str) -> any:
        """Convert string values to appropriate types"""
        if value == 'NOT_FOUND' or not value:
            return None
        
        if value.lower() in ['yes', 'no']:
            return value.lower()
        
        try:
            clean_value = ''.join(c for c in value if c.isdigit() or c in ['.', '-'])
            if clean_value and clean_value != '-':
                return float(clean_value)
        except:
            pass
        
        return value
    
    def log_info(self, message: str) -> None:
        """Log info message to both console and UI"""
        logger.info(message)
        if self.log_callback:
            self.log_callback(f"ℹ️ {message}")

    def log_warning(self, message: str) -> None:
        """Log warning message to both console and UI"""
        logger.warning(message)
        if self.log_callback:
            self.log_callback(f"⚠️ {message}")

    def log_error(self, message: str) -> None:
        """Log error message to both console and UI"""
        logger.error(message)
        if self.log_callback:
            self.log_callback(f"❌ {message}")