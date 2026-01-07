# test_extraction_rules.py
from typing import Dict, Set

class TestExtractionRules:
    """Test configuration with GENERAL expected values"""
    
    # Equipment that only need insulation extraction
    INSULATION_ONLY_EQUIPMENT: Set[str] = {'V-001', 'H-001'}
    
    # Equipment that skip operating pressure/temperature
    SKIP_OPERATING_PRESSURE_TEMPERATURE: Set[str] = {'H-002', 'H-003', 'H-004'}
    
    INSULATION_CONFIGS: Dict[str, Dict] = {
        # General expected values instead of specific ones
        'V-001': {'field': 'INSULATION (mm)', 'expected_value': 'yes or no based on what you see'},
        'H-001': {'field': 'INSULATIONS MM', 'expected_value': 'yes or no'},
        'V-002': {'field': 'INSULATION/PERSONAL PROTECTION', 'value': '-', 'expected_value': 'yes or no'},
        'V-003': {'field': 'NOT_PRESENT', 'expected_value': 'no'},
        'V-004': {'field': 'INSULATION/PERSONAL PROTECTION', 'value': 'HOT INSULATION 100mm', 'expected_value': 'yes'},
        'V-005': {'field': 'INSULATION', 'value': 'HOT 100 (BY OTHERS)', 'expected_value': 'yes'},
        'V-006': {'field': 'NOT_PRESENT', 'expected_value': 'no'},
        'H-002': {'field': 'INSULATIONS MM', 'value': 'NIL', 'expected_value': 'no'},
        'H-003': {'field': 'INSULATIONS MM', 'value': '100mm (BY OTHERS)', 'expected_value': 'yes'},
        'H-004': {'field': 'INSULATION', 'value': '100 (BY OTHERS)', 'expected_value': 'yes'},
    }
    
    FIELD_INSTRUCTIONS: Dict[str, Dict] = {
        'V-002': {
            'fluid': 'Look for field "FLUID NAME" - extract the fluid name you find',
            'design_pressure': 'Look for field "DESIGN PRESSURE" - extract the number value',
            'design_temperature': 'Look for field "DESIGN TEMPERATURE" - extract the number value',
            'operating_pressure': 'Look for field "OPERATING PRESSURE" - extract the number value',
            'operating_temperature': 'Look for field "OPERATING TEMPERATURE" - extract the number value',
            'materials': {
                'Shell': 'BILL OF MATERIAL table, first row - extract material specification and grade',
                'Top Head': 'BILL OF MATERIAL table, second row - extract material specification and grade',
                'Bottom Head': 'BILL OF MATERIAL table, second row - extract material specification and grade'
            }
        },
        'V-003': {
            'fluid': 'Look for field "MEDIUM OF SERVICE" - extract the fluid name',
            'design_pressure': 'Look for field "PRESSURE" - extract the number value',
            'design_temperature': 'Look for field "TEMPERATURE" - extract the number value',
            'operating_pressure': 'Look for field "PRESSURE" - extract the number value',
            'operating_temperature': 'Look for field "TEMPERATURE" - extract the number value',
            'materials': {
                'Shell': 'Look for MATERIAL table or field "SHELL & DISHED END" - extract specification and grade',
                'Top Head': 'Look for MATERIAL table or field "SHELL & DISHED END" - extract specification and grade',
                'Bottom Head': 'Look for MATERIAL table or field "SHELL & DISHED END" - extract specification and grade'
            }
        },
        'V-004': {
            'fluid': 'Look for field "FLUID NAME" - extract the fluid name',
            'design_pressure': 'Look for field "PRESSURE" - extract the number value',
            'design_temperature': 'Look for field "TEMPERATURE" - extract the number value',
            'operating_pressure': 'Look for field "PRESSURE" - extract the number value',
            'operating_temperature': 'Look for field "TEMPERATURE" - extract the number value',
            'materials': {
                'Shell': 'BILL OF MATERIAL table - extract material specification and grade',
                'Top Head': 'BILL OF MATERIAL table - extract material specification and grade',
                'Bottom Head': 'BILL OF MATERIAL table - extract material specification and grade'
            }
        },
        'V-005': {
            'fluid': {
                'Shell': 'Look for field "FLUID" - extract the fluid name',
                'Top Channel': 'Look for field "FLUID" - extract the fluid name',
                'Bottom Channel': 'Look for field "FLUID" - extract the fluid name'
            },
            'design_pressure': {
                'Shell': 'Look for field "DESIGN PRESS." - extract the number value',
                'Top Channel': 'Look for field "DESIGN PRESS." - extract the number value',
                'Bottom Channel': 'Look for field "DESIGN PRESS." - extract the number value'
            },
            'design_temperature': {
                'Shell': 'Look for field "DESIGN TEMP." - extract the number value',
                'Top Channel': 'Look for field "DESIGN TEMP." - extract the number value',
                'Bottom Channel': 'Look for field "DESIGN TEMP." - extract the number value'
            },
            'operating_pressure': {
                'Shell': 'Look for field "OPERATING PRESS." - extract the number value',
                'Top Channel': 'Look for field "OPERATING PRESS." - extract the number value',
                'Bottom Channel': 'Look for field "OPERATING PRESS." - extract the number value'
            },
            'operating_temperature': {
                'Shell': 'Look for field "OPERATING TEMP." - extract the number value',
                'Top Channel': 'Look for field "OPERATING TEMP." - extract the number value',
                'Bottom Channel': 'Look for field "OPERATING TEMP." - extract the number value'
            },
            'materials': {
                'Shell': 'Material specification table, first row - extract specification and grade',
                'Top Channel': 'Material specification table, first row - extract specification and grade',
                'Bottom Channel': 'Material specification table, first row - extract specification and grade'
            }
        },
        'V-006': {
            'fluid': 'Look for field "MEDIUM OF SERVICE" - extract the fluid name',
            'design_pressure': 'Look for field "DESIGN PRESSURE" - extract the number value',
            'design_temperature': 'Look for field "DESIGN TEMPERATURE" - extract the number value',
            'operating_pressure': 'Look for field "WORKING PRESSURE" - extract the number value',
            'operating_temperature': 'Look for field "WORKING TEMPERATURE" - extract the number value',
            'materials': {
                'Shell': 'Look for field "SHELL & DISHED END" - extract specification and grade',
                'Top Head': 'Look for field "SHELL & DISHED END" - extract specification and grade',
                'Bottom Head': 'Look for field "SHELL & DISHED END" - extract specification and grade'
            }
        },
        'H-002': {
            'fluid': {
                'Shell': 'Look for field "FLUID NAME" - extract the fluid name',
                'Channel': 'Look for field "FLUID NAME" - extract the fluid name',
                'Tube Bundle': 'Look for field "FLUID NAME" - extract the fluid name'
            },
            'design_pressure': {
                'Shell': 'Look for field "PRESSURE" - extract the number value',
                'Channel': 'Look for field "PRESSURE" - extract the number value',
                'Tube Bundle': 'Look for field "PRESSURE" - extract the number value'
            },
            'design_temperature': {
                'Shell': 'Look for field "TEMPERATURE" - extract the number value',
                'Channel': 'Look for field "TEMPERATURE" - extract the number value',
                'Tube Bundle': 'Look for field "TEMPERATURE" - extract the number value'
            },
            'materials': {
                'Shell': 'BILL OF MATERIAL table, second row - extract specification and grade',
                'Channel': 'BILL OF MATERIAL table, first row - extract specification and grade',
                'Tube Bundle': 'BILL OF MATERIAL table, first row - extract specification and grade'
            }
        },
        'H-003': {
            'fluid': {
                'Shell': 'Look for field "FLUID NAME" - extract the fluid name',
                'Channel': 'Look for field "FLUID NAME" - extract the fluid name',
                'Tube Bundle': 'Look for field "FLUID NAME" - extract the fluid name'
            },
            'design_pressure': {
                'Shell': 'Look for field "DESIGN, Pressure BAR" - extract the number value',
                'Channel': 'Look for field "DESIGN, Pressure BAR" - extract the number value',
                'Tube Bundle': 'Look for field "DESIGN, Pressure BAR" - extract the number value'
            },
            'design_temperature': {
                'Shell': 'Look for field "TEMPERATURE" - extract the number value',
                'Channel': 'Look for field "TEMPERATURE" - extract the number value',
                'Tube Bundle': 'Look for field "TEMPERATURE" - extract the number value'
            },
            'materials': {
                'Shell': 'BILL OF MATERIAL table, second row - extract specification and grade',
                'Channel': 'BILL OF MATERIAL table, first row - extract specification and grade',
                'Tube Bundle': 'BILL OF MATERIAL table, first row - extract specification and grade'
            }
        },
        'H-004': {
            'fluid': {
                'Shell': 'Look for field "FLUID" - extract the fluid name',
                'Channel': 'Look for field "FLUID" - extract the fluid name',
                'Tube Bundle': 'Look for field "FLUID" - extract the fluid name'
            },
            'design_pressure': {
                'Shell': 'Look for field "DESIGN PRESS." - extract the number value',
                'Channel': 'Look for field "DESIGN PRESS." - extract the number value',
                'Tube Bundle': 'Look for field "DESIGN PRESS." - extract the number value'
            },
            'design_temperature': {
                'Shell': 'Look for field "DESIGN TEMP." - extract the number value',
                'Channel': 'Look for field "DESIGN TEMP." - extract the number value',
                'Tube Bundle': 'Look for field "DESIGN TEMP." - extract the number value'
            },
            'materials': {
                'Shell': 'Material Specification table - extract specification and grade',
                'Channel': 'Material Specification table - extract specification and grade',
                'Tube Bundle': 'Material Specification table - extract specification and grade'
            }
        }
    }