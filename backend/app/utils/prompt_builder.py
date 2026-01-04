"""
Prompt Builder - UPDATED WITH EXPECTED VALUES
Generates targeted, high-precision prompts for specific equipment extraction
"""

from typing import Dict


class PromptBuilder:
    """Builds equipment-specific prompts with expected value guidance"""
    
    @staticmethod
    def build_extraction_prompt(
        equipment_number: str,
        pmt_number: str,
        description: str,
        components: Dict[str, Dict]  # {component_name: {phase, expected_fluid, ...}}
    ) -> str:
        """
        Build high-precision prompt for known equipment with expected values.
        
        Args:
            equipment_number: e.g., 'V-003'
            pmt_number: e.g., 'MLK PMT 10103'
            description: e.g., 'Condensate Vessel'
            components: {component_name: {phase, fluid, material_spec, ...}}
        """
        
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
2. For EACH component listed above, extract its values
3. Look in: Bill of Materials tables, Material tables, Pressure/Temperature tables, Datasheet sections
4. Match the exact values from the drawing (not the expected values above - they are hints only)
5. Extract numbers only for temperatures and pressures (no units)
6. For fluid names, extract the exact name as it appears (e.g., "CHILLED WATER", "CONDENSATE", "Vent Gas")
7. For material specs, extract exactly as shown (e.g., "SA-516", "SA-240", "SA-403")

IMPORTANT NOTES:
- Extract ONLY the components listed above - do not add extra components
- If a value is not visible in the drawing, use empty string ""
- Material specs and grades are typically in Bill of Materials or Material tables
- Temperatures and pressures are usually in technical data sheets or summary tables
- Look carefully at all pages and tables - information may be scattered

RETURN FORMAT:
Return ONLY valid JSON with no markdown, no code blocks, no explanations:
{
  "equipment_number": "%s",
  "pmt_number": "%s",
  "description": "%s",
  "components": [
""" % (equipment_number, pmt_number, description)
        
        # Add component templates with expected hints
        for comp_name, comp_data in components.items():
            prompt += f"""    {{
      "component_name": "{comp_name}",
      "phase": "{comp_data.get('phase')}",
      "fluid": "extracted value here (hint: {comp_data.get('fluid')})",
      "material_spec": "extracted value here (hint: {comp_data.get('material_spec')})",
      "material_grade": "extracted value here (hint: {comp_data.get('material_grade')})",
      "insulation": "extracted value here (hint: {comp_data.get('insulation')})",
      "design_temp": "extracted value here (hint: {comp_data.get('design_temp')})",
      "design_pressure": "extracted value here (hint: {comp_data.get('design_pressure')})",
      "operating_temp": "extracted value here (hint: {comp_data.get('operating_temp')})",
      "operating_pressure": "extracted value here (hint: {comp_data.get('operating_pressure')})"
    }},
"""
        
        prompt += """  ]
}

CRITICAL:
- Return valid JSON only (no markdown, no backticks, no explanations before or after)
- Every component listed above MUST appear in the JSON
- Use empty string "" for missing values, never use null
- Numbers only for temperatures/pressures - strip all units
"""
        
        return prompt.rstrip(',\n')