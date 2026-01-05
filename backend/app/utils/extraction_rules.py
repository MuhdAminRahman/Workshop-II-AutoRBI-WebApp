"""
Extraction Rules - STRONG VERSION
Equipment metadata with expected values, field instructions, and insulation configs
Based on MLK IPETRO PLANT masterfile
"""

from typing import Dict, List, Optional, Set


class ExtractionRules:
    """Equipment definitions with complete extraction guidance"""
    
    # Equipment that only need insulation extraction (V-001, H-001)
    INSULATION_ONLY_EQUIPMENT: Set[str] = {'V-001', 'H-001'}
    
    # Equipment that skip operating pressure/temperature
    SKIP_OPERATING_PRESSURE_TEMPERATURE: Set[str] = {'H-002', 'H-003', 'H-004'}
    
    # Insulation configuration per equipment
    INSULATION_CONFIGS: Dict[str, Dict] = {
        'V-001': {'field': 'INSULATION', 'expected_value': 'No'},
        'H-001': {'field': 'INSULATION', 'expected_value': 'yes'},
        'V-002': {'field': 'INSULATION', 'expected_value': 'No'},
        'V-003': {'field': 'INSULATION', 'expected_value': 'No'},
        'V-004': {'field': 'INSULATION', 'expected_value': 'yes'},
        'V-005': {'field': 'INSULATION', 'expected_value': 'yes'},
        'V-006': {'field': 'INSULATION', 'expected_value': 'No'},
        'H-002': {'field': 'INSULATION', 'expected_value': 'No'},
        'H-003': {'field': 'INSULATION', 'expected_value': 'yes'},
        'H-004': {'field': 'INSULATION', 'expected_value': 'yes'},
    }
    
    # Master equipment definitions with expected values for validation
    EQUIPMENT_MAP: Dict[str, Dict] = {
        'V-001': {
            'pmt_number': 'MLK PMT 10101',
            'description': 'Air Receiver',
            'components': {
                'Top Head': {
                    'phase': 'Gas',
                    'fluid': 'Air',
                    'material_spec': 'SA-516',
                    'material_grade': '70',
                    'insulation': 'No',
                    'design_temp': '100',
                    'design_pressure': '4.00',
                    'operating_temp': '50',
                    'operating_pressure': '3.60',
                },
                'Shell': {
                    'phase': 'Gas',
                    'fluid': 'Air',
                    'material_spec': 'SA-516',
                    'material_grade': '70',
                    'insulation': 'No',
                    'design_temp': '100',
                    'design_pressure': '4.00',
                    'operating_temp': '50',
                    'operating_pressure': '3.60',
                },
                'Bottom Head': {
                    'phase': 'Gas',
                    'fluid': 'Air',
                    'material_spec': 'SA-516',
                    'material_grade': '70',
                    'insulation': 'No',
                    'design_temp': '100',
                    'design_pressure': '4.00',
                    'operating_temp': '50',
                    'operating_pressure': '3.60',
                },
            }
        },
        'V-002': {
            'pmt_number': 'MLK PMT 10102',
            'description': 'Expansion Tank',
            'components': {
                'Top Head': {
                    'phase': 'Liquid',
                    'fluid': 'CHILLED WATER',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'No',
                    'design_temp': '100',
                    'design_pressure': '1.10',
                    'operating_temp': '100',
                    'operating_pressure': '1.00',
                },
                'Shell': {
                    'phase': 'Liquid',
                    'fluid': 'CHILLED WATER',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'No',
                    'design_temp': '100',
                    'design_pressure': '1.10',
                    'operating_temp': '100',
                    'operating_pressure': '1.00',
                },
                'Bottom Head': {
                    'phase': 'Liquid',
                    'fluid': 'CHILLED WATER',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'No',
                    'design_temp': '100',
                    'design_pressure': '1.10',
                    'operating_temp': '100',
                    'operating_pressure': '1.00',
                },
            }
        },
        'V-003': {
            'pmt_number': 'MLK PMT 10103',
            'description': 'Condensate Vessel',
            'components': {
                'Top Head': {
                    'phase': 'Gas',
                    'fluid': 'CONDENSATE',
                    'material_spec': 'SA-516',
                    'material_grade': '70',
                    'insulation': 'No',
                    'design_temp': '200',
                    'design_pressure': '1000.00',
                    'operating_temp': '185',
                    'operating_pressure': '1000.00',
                },
                'Shell': {
                    'phase': 'Gas',
                    'fluid': 'CONDENSATE',
                    'material_spec': 'SA-516',
                    'material_grade': '70',
                    'insulation': 'No',
                    'design_temp': '200',
                    'design_pressure': '1000.00',
                    'operating_temp': '185',
                    'operating_pressure': '1000.00',
                },
                'Bottom Head': {
                    'phase': 'Gas',
                    'fluid': 'CONDENSATE',
                    'material_spec': 'SA-516',
                    'material_grade': '70',
                    'insulation': 'No',
                    'design_temp': '200',
                    'design_pressure': '1000.00',
                    'operating_temp': '185',
                    'operating_pressure': '1000.00',
                },
            }
        },
        'V-004': {
            'pmt_number': 'MLK PMT 10104',
            'description': 'Hot Water System',
            'components': {
                'Head': {
                    'phase': 'Liquid',
                    'fluid': 'HOT WATER',
                    'material_spec': 'A-240',
                    'material_grade': '304',
                    'insulation': 'yes',
                    'design_temp': '120',
                    'design_pressure': '4.00',
                    'operating_temp': '90',
                    'operating_pressure': '1.00',
                },
                'Shell': {
                    'phase': 'Liquid',
                    'fluid': 'HOT WATER',
                    'material_spec': 'A-240',
                    'material_grade': '304',
                    'insulation': 'yes',
                    'design_temp': '120',
                    'design_pressure': '4.00',
                    'operating_temp': '90',
                    'operating_pressure': '1.00',
                },
            }
        },
        'V-005': {
            'pmt_number': 'MLK PMT 10105',
            'description': 'Absorber for Neutralization of Acid Gases',
            'components': {
                'Top Channel': {
                    'phase': 'Liquid',
                    'fluid': 'WATER',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '150',
                    'design_pressure': '4.00',
                    'operating_temp': '45',
                    'operating_pressure': '0.5 - 2',
                },
                'Shell': {
                    'phase': 'Liquid',
                    'fluid': 'AIR GAS/SULPHUR OXIDE',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '150',
                    'design_pressure': '4.00',
                    'operating_temp': '5.45 /40 / 150',
                    'operating_pressure': '0.5 / 2 / 3-4',
                },
                'Bottom Channel': {
                    'phase': 'Gas',
                    'fluid': 'WATER',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '150',
                    'design_pressure': '4.00',
                    'operating_temp': '45',
                    'operating_pressure': '0.5 - 2',
                },
            }
        },
        'V-006': {
            'pmt_number': 'MLK PMT 10106',
            'description': 'Thermal Deaerator',
            'components': {
                'Head': {
                    'phase': 'Gas',
                    'fluid': 'WATER & STEAM',
                    'material_spec': 'SA-283',
                    'material_grade': 'C',
                    'insulation': 'No',
                    'design_temp': '150',
                    'design_pressure': '350.00',
                    'operating_temp': '150',
                    'operating_pressure': '350.00',
                },
                'Shell': {
                    'phase': 'Gas',
                    'fluid': 'WATER & STEAM',
                    'material_spec': 'SA-283',
                    'material_grade': 'C',
                    'insulation': 'No',
                    'design_temp': '150',
                    'design_pressure': '350.00',
                    'operating_temp': '150',
                    'operating_pressure': '350.00',
                },
            }
        },
        'H-001': {
            'pmt_number': 'MLK PMT 10107',
            'description': 'Cooling of Steam- Gas Mix at The Exit of the Reactor',
            'components': {
                'Channel': {
                    'phase': 'Gas',
                    'fluid': 'Vent Gas',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '535',
                    'design_pressure': '0.50',
                    'operating_temp': '450',
                    'operating_pressure': '0.05',
                },
                'Shell': {
                    'phase': 'Gas',
                    'fluid': 'Vent Gas',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '335',
                    'design_pressure': '0.50',
                    'operating_temp': '250',
                    'operating_pressure': '0.05',
                },
                'Tube Bundle': {
                    'phase': 'Gas',
                    'fluid': 'Vent Gas',
                    'material_spec': 'SA-213',
                    'material_grade': 'TP316',
                    'insulation': 'yes',
                    'design_temp': '535',
                    'design_pressure': '0.50',
                    'operating_temp': '450',
                    'operating_pressure': '0.05',
                },
            }
        },
        'H-002': {
            'pmt_number': 'MLK PMT 10108',
            'description': 'Gas Scrubber Cooler',
            'components': {
                'Channel': {
                    'phase': 'Liquid',
                    'fluid': 'CHILLED WATER',
                    'material_spec': 'SA-403',
                    'material_grade': '316',
                    'insulation': 'No',
                    'design_temp': '100',
                    'design_pressure': '10',
                    'operating_temp': '10',
                    'operating_pressure': '0.5',
                },
                'Shell': {
                    'phase': 'Liquid',
                    'fluid': 'ALKALINE WATER',
                    'material_spec': 'SA-312',
                    'material_grade': '316',
                    'insulation': 'No',
                    'design_temp': '150',
                    'design_pressure': '10',
                    'operating_temp': '40',
                    'operating_pressure': '0.3',
                },
                'Tube Bundle': {
                    'phase': 'Liquid',
                    'fluid': 'CHILLED WATER',
                    'material_spec': 'SA-403',
                    'material_grade': '316',
                    'insulation': 'No',
                    'design_temp': '100',
                    'design_pressure': '10',
                    'operating_temp': '10',
                    'operating_pressure': '0.5',
                },
            }
        },
        'H-003': {
            'pmt_number': 'MLK PMT 10109',
            'description': 'Cooling of Water on Irrigation of An Absorber',
            'components': {
                'Channel': {
                    'phase': 'Liquid',
                    'fluid': 'CHILLED WATER',
                    'material_spec': 'SA-403',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '90',
                    'design_pressure': '8 /-1',
                    'operating_temp': '40',
                    'operating_pressure': '0.7',
                },
                'Shell': {
                    'phase': 'Liquid',
                    'fluid': 'REFLUX WATER',
                    'material_spec': 'SA-312',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '90',
                    'design_pressure': '8.00',
                    'operating_temp': '40',
                    'operating_pressure': '0.25',
                },
                'Tube Bundle': {
                    'phase': 'Liquid',
                    'fluid': 'CHILLED WATER',
                    'material_spec': 'SA-403',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '90',
                    'design_pressure': '8 /-1',
                    'operating_temp': '40',
                    'operating_pressure': '0.7',
                },
            }
        },
        'H-004': {
            'pmt_number': 'MLK PMT 10110',
            'description': 'Reflux Condensor of Drying Tower',
            'components': {
                'Channel': {
                    'phase': 'Liquid',
                    'fluid': 'CHILLED WATER',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '35 ~ 40',
                    'design_pressure': '5.00',
                    'operating_temp': '40',
                    'operating_pressure': '0.50',
                },
                'Shell': {
                    'phase': 'Liquid',
                    'fluid': 'REFLUX WATER',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '50',
                    'design_pressure': '0.10',
                    'operating_temp': '50',
                    'operating_pressure': '0.01',
                },
                'Tube Bundle': {
                    'phase': 'Liquid',
                    'fluid': 'CHILLED WATER',
                    'material_spec': 'SA-240',
                    'material_grade': '316',
                    'insulation': 'yes',
                    'design_temp': '35 ~ 40',
                    'design_pressure': '5.00',
                    'operating_temp': '40',
                    'operating_pressure': '0.50',
                },
            }
        },
    }
    
    @classmethod
    def get_equipment(cls, equipment_number: str) -> Dict:
        """Get equipment metadata"""
        return cls.EQUIPMENT_MAP.get(equipment_number, {})
    
    @classmethod
    def get_components_for_equipment(cls, equipment_number: str) -> Dict[str, Dict]:
        """Get components with expected values"""
        eq = cls.get_equipment(equipment_number)
        return eq.get('components', {})
    
    @classmethod
    def get_pmt_number(cls, equipment_number: str) -> str:
        """Get PMT number"""
        eq = cls.get_equipment(equipment_number)
        return eq.get('pmt_number', '')
    
    @classmethod
    def get_description(cls, equipment_number: str) -> str:
        """Get description"""
        eq = cls.get_equipment(equipment_number)
        return eq.get('description', '')
    
    @classmethod
    def validate_extracted_data(cls, equipment_number: str, component_name: str, extracted_data: Dict) -> tuple[int, List[str]]:
        """
        Validate extracted data against expected values.
        
        Returns:
            (valid_field_count, missing_fields_list)
        """
        components = cls.get_components_for_equipment(equipment_number)
        expected = components.get(component_name, {})
        
        missing_fields = []
        valid_count = 0
        
        # Check each field
        for field in ['fluid', 'material_spec', 'material_grade', 'insulation', 
                     'design_temp', 'design_pressure', 'operating_temp', 'operating_pressure']:
            expected_value = expected.get(field, '')
            extracted_value = extracted_data.get(field, '')
            
            # Check if field is populated
            if not extracted_value or extracted_value.strip() == '':
                missing_fields.append(field)
            else:
                # Basic validation: text fields case-insensitive
                if field in ['material_spec', 'material_grade', 'fluid']:
                    if str(expected_value).upper() in str(extracted_value).upper():
                        valid_count += 1
                else:
                    # For numbers, accept if extracted contains expected
                    if str(expected_value) in str(extracted_value):
                        valid_count += 1
        
        return valid_count, missing_fields
    
    @classmethod
    def get_completeness_score(cls, equipment_number: str, extracted_data: Dict) -> tuple[float, Dict[str, List[str]]]:
        """
        Calculate overall completeness score.
        
        Returns:
            (overall_completeness_percent, missing_fields_by_component)
        """
        expected_comps = cls.get_components_for_equipment(equipment_number)
        
        all_missing = {}
        total_valid = 0
        total_fields = 0
        
        for comp_name in expected_comps.keys():
            # Find this component in extracted data
            extracted_comp = None
            for comp in extracted_data.get('components', []):
                if comp.get('component_name') == comp_name:
                    extracted_comp = comp
                    break
            
            if not extracted_comp:
                all_missing[comp_name] = ['fluid', 'material_spec', 'material_grade', 'insulation',
                                         'design_temp', 'design_pressure', 'operating_temp', 'operating_pressure']
                total_fields += 8
            else:
                valid, missing = cls.validate_extracted_data(equipment_number, comp_name, extracted_comp)
                total_valid += valid
                total_fields += 8
                if missing:
                    all_missing[comp_name] = missing
        
        completeness = (total_valid / total_fields * 100) if total_fields > 0 else 0
        
        return completeness, all_missing