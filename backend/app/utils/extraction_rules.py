"""
Extraction Rules - UPDATED WITH EXPECTED VALUES
Equipment metadata from MLK IPETRO PLANT masterfile
Includes component definitions, expected values, and field instructions
"""

from typing import Dict, List, Optional


class ExtractionRules:
    """Equipment definitions with components and expected values"""
    
    # Master equipment definitions with expected values for validation
    EQUIPMENT_MAP: Dict[str, Dict] = {
        'V-001': {
            'pmt_number': 'MLK PMT 10101',
            'description': 'Air Receiver',
            'components': {
                'Top Head': {
                    'phase': 'Gas',
                    'fluid': 'Air',
                    'material_type': 'Carbon Steel',
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
                    'material_type': 'Carbon Steel',
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
                    'material_type': 'Carbon Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Carbon Steel',
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
                    'material_type': 'Carbon Steel',
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
                    'material_type': 'Carbon Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Carbon Steel',
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
                    'material_type': 'Carbon Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
                    'material_type': 'Stainless Steel',
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
        """Get equipment metadata by equipment number"""
        return cls.EQUIPMENT_MAP.get(equipment_number, {})
    
    @classmethod
    def get_components_for_equipment(cls, equipment_number: str) -> Dict[str, Dict]:
        """Get components with expected values for equipment"""
        eq = cls.get_equipment(equipment_number)
        return eq.get('components', {})
    
    @classmethod
    def get_pmt_number(cls, equipment_number: str) -> str:
        """Get PMT number for equipment"""
        eq = cls.get_equipment(equipment_number)
        return eq.get('pmt_number', '')
    
    @classmethod
    def get_description(cls, equipment_number: str) -> str:
        """Get equipment description"""
        eq = cls.get_equipment(equipment_number)
        return eq.get('description', '')
    
    @classmethod
    def validate_extracted_data(cls, equipment_number: str, component_name: str, extracted_data: Dict) -> Dict[str, bool]:
        """
        Validate extracted data against expected values.
        
        Returns:
            Dict[field_name -> is_valid] for each field
        """
        components = cls.get_components_for_equipment(equipment_number)
        expected = components.get(component_name, {})
        
        validation_result = {}
        
        # Check each field
        for field in ['fluid', 'material_spec', 'material_grade', 'insulation', 
                     'design_temp', 'design_pressure', 'operating_temp', 'operating_pressure']:
            expected_value = expected.get(field, '')
            extracted_value = extracted_data.get(field, '')
            
            # Simple validation: does extracted match expected (case-insensitive for text)
            if field in ['material_spec', 'material_grade', 'fluid']:
                is_valid = extracted_value.upper() == expected_value.upper()
            else:
                # For numbers/pressures, check if extracted contains the expected number
                is_valid = str(expected_value) in str(extracted_value)
            
            validation_result[field] = is_valid
        
        return validation_result