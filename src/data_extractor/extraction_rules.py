from typing import Dict, Set

class ExtractionRules:
    """Centralized configuration for extraction rules"""
    
    # Equipment that only need insulation extraction
    INSULATION_ONLY_EQUIPMENT: Set[str] = {'V-001', 'H-001'}
    
    # Equipment that skip operating pressure/temperature (already filled in Excel)
    SKIP_OPERATING_PRESSURE_TEMPERATURE: Set[str] = {'H-002', 'H-003', 'H-004'}
    
    INSULATION_CONFIGS: Dict[str, Dict] = {
        'V-001': {'field': 'INSULATION (mm)', 'expected_value': 'no'},
        'H-001': {'field': 'INSULATIONS MM', 'expected_value': 'yes'},
        'V-002': {'field': 'INSULATION/PERSONAL PROTECTION', 'value': '-', 'expected_value': 'no'},
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
            'fluid': 'SEARCH THOROUGHLY: Look for field "FLUID NAME" with value "CHILLED WATER" - check all text and tables',
            'design_pressure': 'SEARCH THOROUGHLY: Look for field "DESIGN PRESSURE" with value "1.1" - check all tables and data sheets',
            'design_temperature': 'SEARCH THOROUGHLY: Look for field "DESIGN TEMPERATURE" with value "100" - check all tables and data sheets',
            'operating_pressure': 'SEARCH THOROUGHLY: Look for field "OPERATING PRESSURE" with value "1.0" - check all tables and data sheets',
            'operating_temperature': 'SEARCH THOROUGHLY: Look for field "OPERATING TEMPERATURE" with value "100" - check all tables and data sheets',
            'materials': {
                'Shell': 'SEARCH ENTIRE DRAWING: BILL OF MATERIAL table, first row: "PLATE 1571x600x5thk SHELL TO BE ROLLED, SA 240 M 316L/SA 240 316L" → Spec: SA-240, Grade: 316',
                'Top Head': 'SEARCH ENTIRE DRAWING: BILL OF MATERIAL table, second row: "DISH HEAD 8thk TO BE FORMED TO 2.1 TYPE, SA 240 M 316/SA 240 316L" → Spec: SA-240, Grade: 316',
                'Bottom Head': 'SEARCH ENTIRE DRAWING: BILL OF MATERIAL table, second row: "DISH HEAD 8thk TO BE FORMED TO 2.1 TYPE, SA 240 M 316/SA 240 316L" → Spec: SA-240, Grade: 316'
            }
        },
        'V-003': {
            'fluid': 'Look carefully for field "MEDIUM OF SERVICE" with value "condensate" - check all pages',
            'design_pressure': 'Search thoroughly for field "PRESSURE" with value "1,000" - check data sheets',
            'design_temperature': 'Search thoroughly for field "TEMPERATURE" with value "200" - check data sheets',
            'operating_pressure': 'Search thoroughly for field "PRESSURE" with value "1000" - check data sheets',
            'operating_temperature': 'Search thoroughly for field "TEMPERATURE" with value "185" - check data sheets',
            'materials': {
                'Shell': 'SEARCH ENTIRE DRAWING: Look for MATERIAL table or field "SHELL & DISHED END" with value "A/SA 516 Gr. 70" → Spec: SA-516, Grade: 70',
                'Top Head': 'SEARCH ENTIRE DRAWING: Look for MATERIAL table or field "SHELL & DISHED END" with value "A/SA 516 Gr. 70" → Spec: SA-516, Grade: 70',
                'Bottom Head': 'SEARCH ENTIRE DRAWING: Look for MATERIAL table or field "SHELL & DISHED END" with value "A/SA 516 Gr. 70" → Spec: SA-516, Grade: 70'
            }
        },
        'V-004': {
            'fluid': 'Search entire drawing for field "FLUID NAME" with value "HOT WATER" - check all text',
            'design_pressure': 'Search entire drawing for field "PRESSURE" with value "4" - check all tables',
            'design_temperature': 'Search entire drawing for field "TEMPERATURE" with value "120" - check all tables',
            'operating_pressure': 'Search entire drawing for field "PRESSURE" with value "1.0" - check all tables',
            'operating_temperature': 'Search entire drawing for field "TEMPERATURE" with value "90" - check all tables',
            'materials': {
                'Shell': 'SEARCH THOROUGHLY: BILL OF MATERIAL table, look for "SHELL PLATE, ASTM A240 304L" → Spec: A-240, Grade: 304 - check all pages',
                'Top Head': 'SEARCH THOROUGHLY: BILL OF MATERIAL table, look for "2:1 Ellipsoidal Head, ASTM A240 304L" → Spec: A-240, Grade: 304 - check all pages',
                'Bottom Head': 'SEARCH THOROUGHLY: BILL OF MATERIAL table, look for "2:1 Ellipsoidal Head, ASTM A240 304L" → Spec: A-240, Grade: 304 - check all pages'
            }
        },
        'V-005': {
            'fluid': {
                'Shell': 'Look for field "FLUID" with value "AIR GAS/SULPHUR OXIDE"',
                'Top Channel': 'Look for field "FLUID" with value "WATER"',
                'Bottom Channel': 'Look for field "FLUID" with value "WATER"'
            },
            'design_pressure': {
                'Shell': 'Look for field "DESIGN PRESS." with value "4"',
                'Top Channel': 'Look for field "DESIGN PRESS." with value "4"',
                'Bottom Channel': 'Look for field "DESIGN PRESS." with value "4"'
            },
            'design_temperature': {
                'Shell': 'Look for field "DESIGN TEMP." with value "150"',
                'Top Channel': 'Look for field "DESIGN TEMP." with value "150"',
                'Bottom Channel': 'Look for field "DESIGN TEMP." with value "150"'
            },
            'operating_pressure': {
                'Shell': 'Look for field "OPERATING PRESS." with value "0.5 / 2 / 3-4"',
                'Top Channel': 'Look for field "OPERATING PRESS." with value "0.5 – 2"',
                'Bottom Channel': 'Look for field "OPERATING PRESS." with value "0.5 – 2"'
            },
            'operating_temperature': {
                'Shell': 'Look for field "OPERATING TEMP." with value "5.45 / 40 / 150"',
                'Top Channel': 'Look for field "OPERATING TEMP." with value "45"',
                'Bottom Channel': 'Look for field "OPERATING TEMP." with value "45"'
            },
            'materials': {
                'Shell': 'Material specification table, first row: "SHELL & CHANNEL, SA-240-Gr.316/316L" → Spec: SA-240, Grade: 316',
                'Top Channel': 'Material specification table, first row: "SHELL & CHANNEL, SA-240-Gr.316/316L" → Spec: SA-240, Grade: 316',
                'Bottom Channel': 'Material specification table, first row: "SHELL & CHANNEL, SA-240-Gr.316/316L" → Spec: SA-240, Grade: 316'
            }
        },
        'V-006': {
            'fluid': 'Look for field "MEDIUM OF SERVICE" with value "WATER & STEAM"',
            'design_pressure': 'Look for field "DESIGN PRESSURE" with value "350 kPoG"',
            'design_temperature': 'Look for field "DESIGN TEMPERATURE" with value "150° C"',
            'operating_pressure': 'Look for field "WORKING PRESSURE" with value "350 kPoG"',
            'operating_temperature': 'Look for field "WORKING TEMPERATURE" with value "150° C"',
            'materials': {
                'Shell': 'Look for field "SHELL & DISHED END" with value "SA 283 GR.C" → Spec: SA-283, Grade: C',
                'Top Head': 'Look for field "SHELL & DISHED END" with value "SA 283 GR.C" → Spec: SA-283, Grade: C',
                'Bottom Head': 'Look for field "SHELL & DISHED END" with value "SA 283 GR.C" → Spec: SA-283, Grade: C'
            }
        },
        'H-002': {
            'fluid': {
                'Shell': 'Look for field "FLUID NAME" with value "CHILLED WATER"',
                'Channel': 'Look for field "FLUID NAME" with value "ALKALINE WATER"',
                'Tube Bundle': 'Look for field "FLUID NAME" with value "ALKALINE WATER"'
            },
            'design_pressure': {
                'Shell': 'Look for field "PRESSURE" with value "10"',
                'Channel': 'Look for field "PRESSURE" with value "10"',
                'Tube Bundle': 'Look for field "PRESSURE" with value "10"'
            },
            'design_temperature': {
                'Shell': 'Look for field "TEMPERATURE" with value "150"',
                'Channel': 'Look for field "TEMPERATURE" with value "100"',
                'Tube Bundle': 'Look for field "TEMPERATURE" with value "100"'
            },
            'materials': {
                'Shell': 'BILL OF MATERIAL table, second row: "SHELL, SA312-TP316" → Spec: SA-312, Grade: TP316',
                'Channel': 'BILL OF MATERIAL table, first row: "HEAD, SA403- WP316" → Spec: SA-403, Grade: WP316',
                'Tube Bundle': 'BILL OF MATERIAL table, first row: "HEAD, SA403- WP316" → Spec: SA-403, Grade: WP316'
            }
        },
        'H-003': {
            'fluid': {
                'Shell': 'Look for field "FLUID NAME" with value "REFLUX WATER"',
                'Channel': 'Look for field "FLUID NAME" with value "Chilled Water"',
                'Tube Bundle': 'Look for field "FLUID NAME" with value "Chilled Water"'
            },
            'design_pressure': {
                'Shell': 'Look for field "DESIGN, Pressure BAR" with value "8"',
                'Channel': 'Look for field "DESIGN, Pressure BAR" with value "8/-1"',
                'Tube Bundle': 'Look for field "DESIGN, Pressure BAR" with value "8/-1"'
            },
            'design_temperature': {
                'Shell': 'Look for field "TEMPERATURE" with value "90"',
                'Channel': 'Look for field "TEMPERATURE" with value "90"',
                'Tube Bundle': 'Look for field "TEMPERATURE" with value "90"'
            },
            'materials': {
                'Shell': 'BILL OF MATERIAL table, second row: "SHELL, SA312-TP316" → Spec: SA-312, Grade: TP316',
                'Channel': 'BILL OF MATERIAL table, first row: "HEAD, SA403-316" → Spec: SA-403, Grade: 316',
                'Tube Bundle': 'BILL OF MATERIAL table, first row: "HEAD, SA403-316" → Spec: SA-403, Grade: 316'
            }
        },
        'H-004': {
            'fluid': {
                'Shell': 'Look for field "FLUID" with value "REFLUX WATER"',
                'Channel': 'Look for field "FLUID" with value "CHILLED WATER"',
                'Tube Bundle': 'Look for field "FLUID" with value "CHILLED WATER"'
            },
            'design_pressure': {
                'Shell': 'Look for field "DESIGN PRESS." with value "12/F.V"',
                'Channel': 'Look for field "DESIGN PRESS." with value "10"',
                'Tube Bundle': 'Look for field "DESIGN PRESS." with value "10"'
            },
            'design_temperature': {
                'Shell': 'Look for field "DESIGN TEMP." with value "210"',
                'Channel': 'Look for field "DESIGN TEMP." with value "200"',
                'Tube Bundle': 'Look for field "DESIGN TEMP." with value "200"'
            },
            'materials': {
                'Shell': 'Material Specification table (first page), first row: "SHELL, SA-240-GR.316/316L" → Spec: SA-240, Grade: 316',
                'Channel': 'Material Specification table (second page), first row: "TUBESHEET 1, SA-240-GR.316/316L" → Spec: SA-240, Grade: 316',
                'Tube Bundle': 'Material Specification table (second page), first row: "TUBESHEET 1, SA-240-GR.316/316L" → Spec: SA-240, Grade: 316'
            }
        }
    }