import logging
from typing import Dict, List
from models import Component

logger = logging.getLogger(__name__)

class ResponseParser:
    """Handles parsing of AI responses"""
    
    def __init__(self, extraction_rules, log_callback=None):
        self.rules = extraction_rules
        self.log_callback = log_callback
    
    def parse_response(self, response_text: str, expected_components: List[Component], equipment_number: str) -> Dict[str, List[Dict[str, any]]]:
        """Parse the AI response into structured data"""
        components_data = []
        lines = response_text.split('\n')
        current_component = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('COMPONENT:'):
                if current_component:
                    components_data.append(current_component)
                current_component = self._create_empty_component_data(line.replace('COMPONENT:', '').strip())
            elif current_component:
                self._parse_component_line(current_component, line)
        
        if current_component:
            components_data.append(current_component)
        
        return self._finalize_components_data(components_data, expected_components, equipment_number)
    
    def _create_empty_component_data(self, component_name: str) -> Dict[str, str]:
        """Create a component data dict with all fields set to NOT_FOUND"""
        return {
            'component_name': component_name,
            'fluid': 'NOT_FOUND',
            'material_specification': 'NOT_FOUND', 
            'material_grade': 'NOT_FOUND',
            'insulation': 'NOT_FOUND',
            'design_temperature': 'NOT_FOUND',
            'design_pressure': 'NOT_FOUND',
            'operating_temperature': 'NOT_FOUND',
            'operating_pressure': 'NOT_FOUND'
        }
    
    def _parse_component_line(self, component_data: Dict[str, str], line: str):
        """Parse a single line of component data"""
        field_parsers = {
            'FLUID:': ('fluid', str),
            'MATERIAL_SPEC:': ('material_specification', str),
            'MATERIAL_GRADE:': ('material_grade', str),
            'INSULATION:': ('insulation', lambda x: x.lower()),
            'DESIGN_TEMP:': ('design_temperature', str),
            'DESIGN_PRESS:': ('design_pressure', str),
            'OPERATING_TEMP:': ('operating_temperature', str),
            'OPERATING_PRESS:': ('operating_pressure', str)
        }
        
        for prefix, (field, converter) in field_parsers.items():
            if line.startswith(prefix):
                component_data[field] = converter(line.replace(prefix, '').strip())
                break
    
    def _finalize_components_data(self, components_data: List[Dict], expected_components: List[Component], equipment_number: str) -> Dict[str, List[Dict]]:
        """Finalize components data by adding missing components and applying rules"""
        # Add missing components
        extracted_names = {comp['component_name'] for comp in components_data}
        expected_names = {comp.component_name for comp in expected_components}
        
        for comp_name in expected_names - extracted_names:
            components_data.append(self._create_empty_component_data(comp_name))
        
        # Apply equipment-specific rules
        self._apply_equipment_rules(components_data, equipment_number)
        
        # Log extraction results
        extracted_fields = [k for k,v in components_data[0].items() if v != 'NOT_FOUND'] if components_data else []
        self.log_info(f"✅ Extracted data for {equipment_number}: {', '.join(extracted_fields)}")
        not_extracted_fields = [k for k,v in components_data[0].items() if v == 'NOT_FOUND' or v == ""] if components_data else []
        if equipment_number in self.rules.INSULATION_ONLY_EQUIPMENT:
            # For insulation-only equipment, only log insulation field
            not_extracted_fields = [f for f in not_extracted_fields if f == 'insulation']
            if not_extracted_fields:
                self.log_info(f"⚠️ Missing data for {equipment_number}: {', '.join(not_extracted_fields)}")

        else:
            if not_extracted_fields:
                self.log_info(f"⚠️ Missing data for {equipment_number}: {', '.join(not_extracted_fields)}")
        
        return {'components_data': components_data}
    
    def _apply_equipment_rules(self, components_data: List[Dict], equipment_number: str):
        """Apply equipment-specific rules to the extracted data"""
        is_insulation_only = equipment_number in self.rules.INSULATION_ONLY_EQUIPMENT
        skip_operating_pressure_temp = equipment_number in self.rules.SKIP_OPERATING_PRESSURE_TEMPERATURE
        
        for comp_data in components_data:
            if is_insulation_only:
                insulation_value = comp_data['insulation']
                comp_data.update(self._create_empty_component_data(comp_data['component_name']))
                comp_data['insulation'] = insulation_value
            
            if skip_operating_pressure_temp:
                comp_data.update({
                    'operating_temperature': 'NOT_FOUND',
                    'operating_pressure': 'NOT_FOUND'
                })
    def log_info(self, message: str) -> None:
        """Log info message to both console and UI"""
        logger.info(message)
        if self.log_callback:
            self.log_callback(f"ℹ️ {message}")