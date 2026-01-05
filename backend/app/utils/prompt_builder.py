"""
Prompt Builder - WITH RETRY SUPPORT
Generates extraction prompts, including targeted retry prompts for missing fields
"""

from typing import Dict, List, Optional


class PromptBuilder:
    """Builds extraction prompts with retry support"""
    
    @staticmethod
    def build_extraction_prompt(
        equipment_number: str,
        pmt_number: str,
        description: str,
        components: Dict[str, Dict],
        retry_missing_fields: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """
        Build extraction prompt.
        
        Args:
            equipment_number: e.g., 'V-003'
            pmt_number: e.g., 'MLK PMT 10103'
            description: Equipment description
            components: {component_name: {phase, fluid, material_spec, ...}}
            retry_missing_fields: On retry, dict of {component_name: [missing_field_list]}
        """
        
        if retry_missing_fields:
            return PromptBuilder._build_retry_prompt(
                equipment_number, pmt_number, description, components, retry_missing_fields
            )
        else:
            return PromptBuilder._build_initial_prompt(
                equipment_number, pmt_number, description, components
            )
    
    @staticmethod
    def _build_initial_prompt(
        equipment_number: str,
        pmt_number: str,
        description: str,
        components: Dict[str, Dict]
    ) -> str:
        """Build initial extraction prompt"""
        
        prompt = f"""EXTRACTION TASK: {equipment_number} ({pmt_number}) - {description}

This is a technical drawing/datasheet for equipment {equipment_number}.
Extract the following data for EACH component listed below.

COMPONENTS AND EXPECTED DATA:
"""
        
        # Add expected values for each component
        for comp_name, comp_data in components.items():
            prompt += f"""
{comp_name}:
  - Phase: {comp_data.get('phase')}
  - Fluid/Medium: {comp_data.get('fluid')}
  - Material Spec: {comp_data.get('material_spec')}
  - Material Grade: {comp_data.get('material_grade')}
  - Insulation: {comp_data.get('insulation')}
  - Design Temp (°C): {comp_data.get('design_temp')}
  - Design Pressure (MPa): {comp_data.get('design_pressure')}
  - Operating Temp (°C): {comp_data.get('operating_temp')}
  - Operating Pressure (MPa): {comp_data.get('operating_pressure')}
"""
        
        prompt += """
EXTRACTION INSTRUCTIONS:
1. Find the technical data tables/sheets in this drawing
2. For EACH component listed above, extract ALL values
3. Look in: Bill of Materials tables, Material tables, Pressure/Temperature tables, Datasheet sections
4. Match the exact values from the drawing (the expected values above are hints only)
5. Extract numbers only for temperatures and pressures (no units)
6. For fluid names, extract the exact name as it appears (e.g., "CHILLED WATER", "CONDENSATE")
7. For material specs, extract exactly as shown (e.g., "SA-516", "SA-240", "SA-403")
8. Search every page - information may be scattered across multiple sections

IMPORTANT NOTES:
- Extract ONLY the components listed above - do not add extra components
- If a value is not visible in the drawing, use empty string ""
- Material specs/grades are typically in Bill of Materials or Material tables
- Temperatures and pressures are usually in technical data sheets or summary tables
- Look carefully at all tables, headers, and annotations

RETURN FORMAT:
Return ONLY valid JSON (no markdown, no explanations):
{
  "equipment_number": "%s",
  "pmt_number": "%s",
  "description": "%s",
  "components": [
""" % (equipment_number, pmt_number, description)
        
        # Add component templates
        for comp_name, comp_data in components.items():
            prompt += f"""    {{
      "component_name": "{comp_name}",
      "phase": "{comp_data.get('phase')}",
      "fluid": "",
      "material_spec": "",
      "material_grade": "",
      "insulation": "",
      "design_temp": "",
      "design_pressure": "",
      "operating_temp": "",
      "operating_pressure": ""
    }},
"""
        
        prompt += """  ]
}

CRITICAL:
- Return valid JSON only
- Every component listed above MUST appear in the JSON
- Use empty string "" for missing values
- Numbers only for temperatures/pressures - no units
"""
        
        return prompt.rstrip(',\n')
    
    @staticmethod
    def _build_retry_prompt(
        equipment_number: str,
        pmt_number: str,
        description: str,
        components: Dict[str, Dict],
        missing_fields: Dict[str, List[str]]
    ) -> str:
        """Build targeted retry prompt asking only about missing fields"""
        
        prompt = f"""RETRY EXTRACTION: {equipment_number} ({pmt_number}) - {description}

This is a SECOND PASS extraction. We need to find the missing fields below.

COMPONENTS WITH MISSING DATA:
"""
        
        # Only show components with missing fields
        for comp_name, missing in missing_fields.items():
            if not missing:
                continue
            
            expected = components.get(comp_name, {})
            prompt += f"""
{comp_name} (MISSING: {', '.join(missing)}):
"""
            
            for field in missing:
                expected_value = expected.get(field, '')
                if expected_value:
                    prompt += f"  - {field}: Look for value like '{expected_value}'\n"
                else:
                    prompt += f"  - {field}: Extract from drawing\n"
        
        prompt += """
RETRY INSTRUCTIONS:
1. Focus ONLY on the missing fields listed above
2. Search every page carefully - look in:
   - Bill of Materials tables (check all rows)
   - Material tables/Material Specification sections
   - Technical Data sheets
   - Summary/Property tables
   - Header sections and title blocks
3. For fluid names: Look for labels like "FLUID", "MEDIUM", "SERVICE", "FLUID NAME"
4. For materials: Search for "MATERIAL", "ASTM", "SA-", "ASME" specifications
5. For pressures/temperatures: Look for "DESIGN", "OPERATING", "PRESSURE", "TEMPERATURE", "MPa", "°C"
6. Extract EXACTLY as shown (including hyphens, spaces, numbers)

RETURN FORMAT:
Return ONLY the missing fields as JSON (no markdown):
{
  "equipment_number": "%s",
  "components": [
""" % equipment_number
        
        for comp_name, missing in missing_fields.items():
            if not missing:
                continue
            
            prompt += f"""    {{
      "component_name": "{comp_name}",
"""
            for field in missing:
                prompt += f'      "{field}": "",\n'
            
            prompt += """    },
"""
        
        prompt += """  ]
}

CRITICAL:
- Focus on MISSING fields only
- Return valid JSON only
- Use empty string "" if field still cannot be found
- Extract exactly as appears in the drawing
"""
        
        return prompt.rstrip(',\n')