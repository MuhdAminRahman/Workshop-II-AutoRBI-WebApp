from typing import List, Dict
from models import Equipment

class PromptBuilder:
    """Handles construction of equipment-specific prompts"""
    
    @staticmethod
    def build_insulation_only_prompt(equipment_number: str, equipment: Equipment, insulation_config: dict) -> str:
        """Build prompt for equipment that only need insulation extraction"""
        components_list = [comp.component_name for comp in equipment.components]
        
        prompt = f"""
        EXTRACT ONLY INSULATION DATA FOR: {equipment_number} - {equipment.equipment_description}
        
        COMPONENTS TO EXTRACT INSULATION FOR:
        {', '.join(components_list)}
        
        INSULATION EXTRACTION:
        Look for field: "{insulation_config['field']}"
        """
        
        if 'value' in insulation_config:
            prompt += f"Value to look for: \"{insulation_config['value']}\"\n"
        
        if 'expected_value' in insulation_config:
            prompt += f"Expected value: {insulation_config['expected_value']}\n"
        else:
            prompt += "Extract whatever value you find (yes/no or description)\n"
        
        prompt += """
        IMPORTANT: 
        - All components share the same insulation value
        - DO NOT EXTRACT any other data - only insulation
        - Use the exact component names listed above
        
        RETURN FORMAT (for each component):
        COMPONENT: [Exact Component Name from list above]
        INSULATION: [yes/no or extracted value]
        
        Extract for ALL components listed above.
        """
        
        return prompt
    
    @staticmethod
    def build_full_extraction_prompt(equipment_number: str, equipment: Equipment, 
                                   field_instructions: dict, insulation_config: dict, 
                                   skip_operating_pressure_temp: bool) -> str:
        """Build prompt for equipment needing full extraction"""
        components_list = [comp.component_name for comp in equipment.components]
        
        prompt_parts = [
            f"EXTRACT TECHNICAL DATA FOR: {equipment_number} - {equipment.equipment_description}",
            "",
            "COMPONENTS TO EXTRACT: " + ", ".join(components_list),
            "",
            "EXTRACTION INSTRUCTIONS:"
        ]
        
        PromptBuilder._add_field_instructions(prompt_parts, field_instructions, components_list, skip_operating_pressure_temp)
        
        PromptBuilder._add_insulation_instructions(prompt_parts, insulation_config)
        
        PromptBuilder._add_return_format(prompt_parts, field_instructions, skip_operating_pressure_temp)
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def _add_field_instructions(prompt_parts: list, instructions: dict, components: list, skip_operating_pressure_temp: bool):
        """Add field-specific extraction instructions"""
        field_mapping = {
            'fluid': 'FLUID',
            'design_pressure': 'DESIGN PRESSURE', 
            'design_temperature': 'DESIGN TEMPERATURE',
            'operating_pressure': 'OPERATING PRESSURE',
            'operating_temperature': 'OPERATING TEMPERATURE'
        }
        
        for field_key, field_name in field_mapping.items():
            if field_key in instructions:
                # Only skip if explicitly told to skip pressure/temperature
                if skip_operating_pressure_temp and field_key in ['operating_pressure', 'operating_temperature']:
                    continue
                    
                instruction = instructions[field_key]
                if isinstance(instruction, dict):
                    prompt_parts.append(f"{field_name}:")
                    for comp, comp_instruction in instruction.items():
                        if comp in components:
                            prompt_parts.append(f"  - {comp}: {comp_instruction}")
                else:
                    prompt_parts.append(f"{field_name}: {instruction}")
        
        # Add materials if present - ALWAYS include materials
        if 'materials' in instructions:
            prompt_parts.append("")
            prompt_parts.append("MATERIAL EXTRACTION (IMPORTANT - MUST EXTRACT):")
            prompt_parts.append("Look carefully in Bill of Materials tables, Material tables, or Material Specification tables")
            for comp, material_instruction in instructions['materials'].items():
                if comp in components:
                    prompt_parts.append(f"  - {comp}: {material_instruction}")
    
    @staticmethod
    def _add_insulation_instructions(prompt_parts: list, insulation_config: dict):
        """Add insulation extraction instructions"""
        prompt_parts.append("")
        prompt_parts.append("INSULATION EXTRACTION:")
        if insulation_config['field'] == 'NOT_PRESENT':
            prompt_parts.append("Field not present in drawing")
        else:
            prompt_parts.append(f"Look for field: \"{insulation_config['field']}\"")
            if 'value' in insulation_config:
                prompt_parts.append(f"Value to look for: \"{insulation_config['value']}\"")
        
        # Handle expected_value if it exists
        if 'expected_value' in insulation_config:
            prompt_parts.append(f"Expected value: {insulation_config['expected_value']}")
        else:
            prompt_parts.append("Extract whatever value you find")
    
    @staticmethod
    def _add_return_format(prompt_parts: list, instructions: dict, skip_operating_pressure_temp: bool):
        """Add the return format section"""
        prompt_parts.extend([
            "",
            "IMPORTANT NOTES:",
            "- Material type should NOT be extracted - field is already filled in Excel",
            "- For temperatures: extract numbers only (ignore °C, °F symbols)",
            "- For pressures: extract numbers only (ignore kPoG, BAR, MPa symbols)",
            "- Use exact field names and locations specified",
            "",
            "RETURN FORMAT (for each component):",
            "COMPONENT: [Component Name]"
        ])
        
        # Dynamic return format based on what fields to extract
        if 'fluid' in instructions:
            prompt_parts.append("FLUID: [extracted value]")
        
        if 'materials' in instructions:
            prompt_parts.append("MATERIAL_SPEC: [extracted specification]")
            prompt_parts.append("MATERIAL_GRADE: [extracted grade]")
        
        prompt_parts.append("INSULATION: [yes/no]")
        
        if skip_operating_pressure_temp:
            pressure_temp_fields = [
                'DESIGN_PRESS: [number]',
                'DESIGN_TEMP: [number]', 
            ]
            prompt_parts.extend(pressure_temp_fields)

        if not skip_operating_pressure_temp:
            pressure_temp_fields = [
                'DESIGN_PRESS: [number]',
                'DESIGN_TEMP: [number]', 
                'OPERATING_PRESS: [number]',
                'OPERATING_TEMP: [number]'
            ]
            prompt_parts.extend(pressure_temp_fields)
        
        prompt_parts.append("")
        prompt_parts.append("Separate each component with a blank line.")