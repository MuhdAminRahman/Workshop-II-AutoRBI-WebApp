from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
import customtkinter as ctk
import re


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    empty_cells: List[Tuple[str, str, str]]  # (equipment_no, component, field)
    format_errors: List[Tuple[str, str, str, str]]  # (equipment_no, component, field, error_message)
    error_message: str
    error_widgets: List[Tuple[ctk.CTkEntry, str, str]]  # (widget, field_name, error_type)
    
    @property
    def has_errors(self) -> bool:
        return len(self.empty_cells) > 0 or len(self.format_errors) > 0
    
    @property
    def total_errors(self) -> int:
        return len(self.empty_cells) + len(self.format_errors)


class DataValidator:
    """Validates extracted and edited data for DataTableManager"""
    
    # Required fields that must be filled
    REQUIRED_FIELDS = [
        'equipment_no',
        'pmt_number',
        'equipment_description',
        'component_name',
        'phase',
        'fluid',
        'material_type',
        'spec',
        'grade',
        'insulation',
        'design_temp',
        'design_pressure',
        'operating_temp',
        'operating_pressure'
    ]
    
    # Field mapping: column index -> field name in DataTableRow
    COLUMN_TO_FIELD = {
        1: 'equipment_no',
        2: 'pmt_number',
        3: 'equipment_description',
        4: 'component_name',
        5: 'phase',
        6: 'fluid',
        7: 'material_type',
        8: 'spec',
        9: 'grade',
        10: 'insulation',
        11: 'design_temp',
        12: 'design_pressure',
        13: 'operating_temp',
        14: 'operating_pressure'
    }
    
    # Field-specific validators
    FIELD_VALIDATORS = {
        'insulation': {
            'allowed_values': ['yes', 'no', 'y', 'n', '', None],
            'normalize': lambda x: 'yes' if str(x).lower() in ['yes', 'y', 'true', '1'] 
                                else 'no' if str(x).lower() in ['no', 'n', 'false', '0'] 
                                else str(x).strip()
        },
        'design_temp': {
            'pattern': r'^[-+]?\d*\.?\d+.*?$',  # Number with optional unit
            'message': 'Should be a number (e.g., 150 or 150°C)'
        },
        'design_pressure': {
            'pattern': r'^[-+]?\d*\.?\d+.*?$',
            'message': 'Should be a number (e.g., 10 or 10 bar)'
        },
        'operating_temp': {
            'pattern': r'^[-+]?\d*\.?\d+.*?$',
            'message': 'Should be a number (e.g., 100 or 100°C)'
        },
        'operating_pressure': {
            'pattern': r'^[-+]?\d*\.?\d+.*?$',
            'message': 'Should be a number (e.g., 5 or 5 bar)'
        },
        'spec': {
            'pattern': r'^[A-Za-z0-9\-\.\s]+$',
            'message': 'Should be alphanumeric with dots/dashes (e.g., ASTM A106 or API 5L)'
        },
        'grade': {
            'pattern': r'^[A-Za-z0-9\-\.\s]+$',
            'message': 'Should be alphanumeric (e.g., B, GR.B, 316L)'
        },
        'material_type': {
            'pattern': r'^[A-Za-z\s]+$',
            'message': 'Should contain only letters (e.g., Carbon Steel, Stainless)'
        }
    }
    
    def validate_data_table_manager(
        self,
        data_table_manager
    ) -> ValidationResult:
        """
        Validate all data in DataTableManager for required fields and formats.
        
        Args:
            data_table_manager: DataTableManager instance
            
        Returns:
            ValidationResult with all errors
        """
        empty_cells = []
        format_errors = []
        error_widgets = []
        
        if not hasattr(data_table_manager, 'sections'):
            return ValidationResult(
                is_valid=False,
                empty_cells=[],
                format_errors=[],
                error_message="No data table manager found",
                error_widgets=[]
            )
        
        # Iterate through all sections (files)
        for file_path, section in data_table_manager.sections.items():
            if not hasattr(section, 'rows') or not section.rows:
                continue
            
            for row in section.rows:
                if not hasattr(row, 'entries') or len(row.entries) < 10:
                    continue
                
                equipment_no = row.equipment_no
                component_name = row.component_name
                
                # Check required fields based on column indices
                for col_idx, field_name in self.COLUMN_TO_FIELD.items():
                    if col_idx >= len(row.entries):
                        continue
                    
                    entry_widget = row.entries[col_idx]
                    field_value = entry_widget.get().strip() if hasattr(entry_widget, 'get') else ""
                    
                    # Check if required field is empty
                    if field_name in self.REQUIRED_FIELDS and not field_value:
                        empty_cells.append((equipment_no, component_name, field_name))
                        error_widgets.append((entry_widget, field_name, 'required'))
                    
                    # Check field format (even if not required)
                    if field_value and field_name in self.FIELD_VALIDATORS:
                        format_error = self._validate_field_format(field_name, field_value)
                        if format_error:
                            format_errors.append((equipment_no, component_name, field_name, format_error))
                            error_widgets.append((entry_widget, field_name, 'format'))
        
        # Build comprehensive error message
        error_msg = self._build_error_message(empty_cells, format_errors)
        
        return ValidationResult(
            is_valid=len(empty_cells) == 0 and len(format_errors) == 0,
            empty_cells=empty_cells,
            format_errors=format_errors,
            error_message=error_msg,
            error_widgets=error_widgets
        )
    
    def _validate_field_format(self, field_name: str, value: str) -> Optional[str]:
        """Validate field format based on rules"""
        validator = self.FIELD_VALIDATORS.get(field_name)
        if not validator:
            return None
        
        value_str = str(value).strip()
        
        # Check for allowed values (e.g., insulation)
        if 'allowed_values' in validator:
            normalized = value_str.lower()
            if normalized not in [str(v).lower() for v in validator['allowed_values'] if v is not None]:
                return f"Must be one of: {', '.join([str(v) for v in validator['allowed_values'] if v])}"
        
        # Check regex pattern
        if 'pattern' in validator:
            if not re.match(validator['pattern'], value_str):
                return validator.get('message', f"Invalid format for {field_name}")
        
        return None
    
    def _build_error_message(self, empty_cells: List[Tuple], format_errors: List[Tuple]) -> str:
        """Build comprehensive error message"""
        if not empty_cells and not format_errors:
            return ""
        
        error_msg = "Validation Errors:\n"
        
        # Group empty fields by equipment
        if empty_cells:
            error_msg += "\nRequired fields missing:\n"
            equipment_empty = {}
            for eq_no, comp, field in empty_cells:
                if eq_no not in equipment_empty:
                    equipment_empty[eq_no] = {}
                if comp not in equipment_empty[eq_no]:
                    equipment_empty[eq_no][comp] = []
                equipment_empty[eq_no][comp].append(field)
            
            for eq_no, components in equipment_empty.items():
                error_msg += f"  {eq_no}:\n"
                for comp, fields in components.items():
                    error_msg += f"    {comp}: {', '.join(fields)}\n"
        
        # Group format errors by equipment
        if format_errors:
            error_msg += "\nFormat errors:\n"
            equipment_format = {}
            for eq_no, comp, field, error in format_errors:
                if eq_no not in equipment_format:
                    equipment_format[eq_no] = {}
                if comp not in equipment_format[eq_no]:
                    equipment_format[eq_no][comp] = []
                equipment_format[eq_no][comp].append(f"{field} - {error}")
            
            for eq_no, components in equipment_format.items():
                error_msg += f"  {eq_no}:\n"
                for comp, errors in components.items():
                    for error in errors:
                        error_msg += f"    {comp}: {error}\n"
        
        error_msg += "\nPlease fix all errors before saving."
        return error_msg
    
    def highlight_errors(
    self,
    validation_result: ValidationResult,
    empty_color: str = "#ff0000",  # Red border for empty
    format_color: str = "#ffcc00"   # Yellow border for format errors
) -> None:
        """
        Highlight error cells by changing entry border color.
        """
        for entry_widget, field_name, error_type in validation_result.error_widgets:
            if isinstance(entry_widget, ctk.CTkEntry):
                color = empty_color if error_type == 'required' else format_color
                
                # Increase border width and set color
                entry_widget.configure(
                    border_width=3,  # Make border thicker
                    border_color=color
                )
    
    def clear_highlights(
        self,
        data_table_manager,
        default_color: str = None
    ) -> None:
        """
        Clear all cell highlights.
        
        Args:
            data_table_manager: DataTableManager instance
            default_color: Color to reset to (if None, uses widget default)
        """
        for file_path, section in data_table_manager.sections.items():
            if not hasattr(section, 'rows'):
                continue
            
            for row in section.rows:
                if not hasattr(row, 'entries'):
                    continue
                
                for entry in row.entries:
                    if isinstance(entry, ctk.CTkEntry):
                        if default_color:
                            entry.configure(fg_color=default_color)
                        else:
                            # Reset to default entry color
                            entry.configure(fg_color=ctk.ThemeManager.theme["CTkEntry"]["fg_color"])

    def validate_and_highlight(self, data_table_manager) -> ValidationResult:
        """
        Combined validation and highlighting.
        
        Returns:
            ValidationResult with validation status
        """
        # Clear previous highlights
        self.clear_highlights(data_table_manager)
        
        # Validate
        result = self.validate_data_table_manager(data_table_manager)
        
        # Highlight errors
        if result.has_errors:
            self.highlight_errors(validation_result=result)
        return result
    
    def normalize_insulation(self, value: Any) -> str:
        """Normalize insulation value for database"""
        if value is None:
            return None
        
        value_str = str(value).strip().lower()
        
        if value_str in ["yes", "y", "true", "1", "t"]:
            return "yes"
        if value_str in ["no", "n", "false", "0", "f"]:
            return "no"
        
        return value_str  # Return as-is if not recognized
    
    def normalize_temperature(self, value: Any) -> str:
        """Normalize temperature value for database"""
        if value is None:
            return None
        
        # Extract numeric part and optional unit
        value_str = str(value).strip()
        
        # Remove common unit symbols but keep the value as string
        # Database stores as string, so we just clean it up
        cleaned = value_str.replace('°C', '').replace('°F', '').replace('C', '').replace('F', '').strip()
        
        # Try to convert to float to validate it's a number
        try:
            float(cleaned)
            return cleaned  # Return numeric part
        except ValueError:
            return value_str  # Return original if not numeric
    
    def normalize_pressure(self, value: Any) -> str:
        """Normalize pressure value for database"""
        if value is None:
            return None
        
        value_str = str(value).strip()
        
        # Remove common pressure units
        cleaned = value_str.replace('bar', '').replace('psi', '').replace('kPa', '').replace('MPa', '').strip()
        
        # Try to convert to float to validate it's a number
        try:
            float(cleaned)
            return cleaned
        except ValueError:
            return value_str
    
    def get_validation_summary(
        self,
        validation_result: ValidationResult
    ) -> Dict[str, any]:
        """
        Get a structured summary of validation results.
        """
        summary = {
            'is_valid': validation_result.is_valid,
            'total_errors': validation_result.total_errors,
            'empty_fields': len(validation_result.empty_cells),
            'format_errors': len(validation_result.format_errors),
            'equipment_errors': {},
            'field_breakdown': {},
            'has_errors': validation_result.has_errors
        }
        
        # Group errors by equipment
        for eq_no, component, field in validation_result.empty_cells:
            if eq_no not in summary['equipment_errors']:
                summary['equipment_errors'][eq_no] = []
            summary['equipment_errors'][eq_no].append({
                'component': component,
                'field': field,
                'error_type': 'missing',
                'message': 'Required field is empty'
            })
            
            # Count by field type
            key = f"{field}_missing"
            if key not in summary['field_breakdown']:
                summary['field_breakdown'][key] = 0
            summary['field_breakdown'][key] += 1
        
        for eq_no, component, field, error_msg in validation_result.format_errors:
            if eq_no not in summary['equipment_errors']:
                summary['equipment_errors'][eq_no] = []
            summary['equipment_errors'][eq_no].append({
                'component': component,
                'field': field,
                'error_type': 'format',
                'message': error_msg
            })
            
            # Count by field type
            key = f"{field}_format"
            if key not in summary['field_breakdown']:
                summary['field_breakdown'][key] = 0
            summary['field_breakdown'][key] += 1
        
        return summary