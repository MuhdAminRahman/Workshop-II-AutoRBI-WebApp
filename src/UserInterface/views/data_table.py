# file: data_table.py
import os
import customtkinter as ctk
from typing import Dict, List, Optional, Callable, Any
from .constants import Colors, Fonts, Sizes
from models.equipment import Equipment
from models.equipment_component import Component


class DataTableRow:
    """Represents a single row in the data table"""
    
    def __init__(self, parent, columns: List[tuple], row_data: List[str], 
                 equipment_no: str, component_name: str):
        self.parent = parent
        self.columns = columns
        self.equipment_no = equipment_no
        self.component_name = component_name
        self.entries = []
        self.row_frame = None
        
        self._build_row(row_data)
    
    def _build_row(self, row_data: List[str]):
        """Build a single row with entry widgets"""
        self.row_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.row_frame.pack(fill="x", padx=0, pady=1)
        
        # Create entry for each column
        for col_idx, (col_name, col_width) in enumerate(self.columns):
            entry = ctk.CTkEntry(
                self.row_frame,
                font=Fonts.TINY,
                width=col_width,
                height=24,
            )
            # Set initial value
            entry.insert(0, row_data[col_idx])
            entry.pack(side="left", padx=1, pady=1)
            
            # Tag entries for easy identification
            if col_idx >= 6:  # Data columns (fluid, material_type, etc.)
                entry.bind("<FocusOut>", self._on_entry_change)
                entry.bind("<Return>", self._on_entry_change)
            
            self.entries.append(entry)
    
    def _on_entry_change(self, event=None):
        """Callback when entry value changes"""
        if hasattr(self.parent, 'on_data_change'):
            self.parent.on_data_change(self.equipment_no, self.component_name, self.get_data())
    
    def get_data(self) -> Dict[str, str]:
        """Get data from this row"""
        # Map column indices to field names
        field_map = {
            6: 'fluid',
            7: 'material_type',
            8: 'spec',
            9: 'grade',
            10: 'insulation',
            11: 'design_temp',
            12: 'design_pressure',
            13: 'operating_temp',
            14: 'operating_pressure',
        }
        
        data = {}
        for col_idx, entry in enumerate(self.entries):
            if col_idx in field_map:
                data[field_map[col_idx]] = entry.get().strip()
        
        return data
    
    def update_from_equipment(self, equipment_data: Dict[str, str]):
        """Update UI from equipment data"""
        field_to_col = {
            'fluid': 6,
            'material_type': 7,
            'spec': 8,
            'grade': 9,
            'insulation': 10,
            'design_temp': 11,
            'design_pressure': 12,
            'operating_temp': 13,
            'operating_pressure': 14,
        }
        
        for field, col_idx in field_to_col.items():
            if field in equipment_data:
                self.entries[col_idx].delete(0, 'end')
                self.entries[col_idx].insert(0, equipment_data[field])


class DataTableSection:
    """Represents a table section for a single file"""
    
    def __init__(self, parent, file_path: str, on_data_change: Optional[Callable] = None):
        self.parent = parent
        self.file_path = file_path
        self.on_data_change = on_data_change
        self.rows = []
        
        self.section_frame = None
        self.table_frame = None
        self._build_section()
    
    def _build_section(self):
        """Build the table section"""
        from data_extractor.utils import get_equipment_number_from_image_path
        
        filename = os.path.basename(self.file_path)
        equipment_number = get_equipment_number_from_image_path(self.file_path)
        
        # Create section frame
        self.section_frame = ctk.CTkFrame(self.parent, fg_color=Colors.TRANSPARENT)
        self.section_frame.pack(fill="x", padx=0, pady=(12, 8))
        
        # Header
        header_text = f"📄 {filename}"
        if equipment_number:
            header_text += f" (Equipment: {equipment_number})"
        
        header = ctk.CTkLabel(self.section_frame, text=header_text, font=Fonts.SECTION_LABEL)
        header.pack(anchor="w", pady=(0, 8))
    
    def add_table(self, columns: List[tuple], equipment_data: List[Dict]):
        """Add a table to this section"""
        from .constants import Colors, Sizes
        estimated_height = min(600, max(200, len(equipment_data) * 30 + 50))
        # Create scrollable table frame
        self.table_frame = ctk.CTkScrollableFrame(
            self.section_frame,
            fg_color=Colors.SECTION_BG,
            corner_radius=Sizes.CORNER_RADIUS_XS,
            height=estimated_height,
            orientation="vertical",
        )
        self.table_frame.pack(fill="both", expand=True)
        
        # Build header
        self._build_header(self.table_frame, columns)
        
        # Build rows
        self._build_rows(self.table_frame, columns, equipment_data)
    
    def _build_header(self, parent: ctk.CTkFrame, columns: List[tuple]):
        """Build table header"""
        header_row = ctk.CTkFrame(parent, fg_color=Colors.TABLE_HEADER_BG, corner_radius=0)
        header_row.pack(fill="x", padx=0, pady=0)
        
        for col_name, col_width in columns:
            label = ctk.CTkLabel(
                header_row,
                text=col_name,
                font=Fonts.TABLE_HEADER,
                text_color=Colors.TABLE_HEADER_TEXT,
                fg_color=Colors.TABLE_HEADER_BG,
                width=col_width,
                corner_radius=0,
            )
            label.pack(side="left", padx=1, pady=1)
    
    def _build_rows(self, parent: ctk.CTkFrame, columns: List[tuple], equipment_data: List[Dict]):
        """Build table rows"""
        for row_idx, data in enumerate(equipment_data):
            row_values = [
                str(row_idx + 1),
                data['equipment_number'],
                data['pmt_number'],
                data['equipment_description'],
                data['component_name'],
                data['phase'],
                data.get('fluid', ''),
                data.get('material_type', ''),
                data.get('spec', ''),
                data.get('grade', ''),
                data.get('insulation', ''),
                data.get('design_temp', ''),
                data.get('design_pressure', ''),
                data.get('operating_temp', ''),
                data.get('operating_pressure', ''),
            ]
            
            # Create row
            row = DataTableRow(
                parent=parent,
                columns=columns,
                row_data=row_values,
                equipment_no=data['equipment_number'],
                component_name=data['component_name']
            )
            
            # Connect data change callback
            if self.on_data_change:
                row.parent = self  # So row can call on_data_change
            
            self.rows.append(row)
    
    def get_all_data(self) -> List[Dict[str, Any]]:
        """Get all data from all rows in this section"""
        data = []
        for row in self.rows:
            row_data = row.get_data()
            row_data.update({
                'equipment_number': row.equipment_no,
                'component_name': row.component_name,
                'file_path': self.file_path
            })
            data.append(row_data)
        return data
    
    def get_equipment_dict(self) -> Dict[str, Equipment]:
        """Get equipment dictionary from this section"""
        equipment_dict = {}
        
        for row in self.rows:
            equipment_no = row.equipment_no
            component_name = row.component_name
            row_data = row.get_data()
            
            # Create or get existing Equipment object
            if equipment_no not in equipment_dict:
                # We need to find the base equipment data from the row entries
                # The row contains all the data, so we need to extract the equipment-level info
                pmt_number = row.entries[2].get().strip() if len(row.entries) > 2 else ""
                equipment_description = row.entries[3].get().strip() if len(row.entries) > 3 else ""
                row_index = int(row.entries[0].get().strip()) if row.entries[0].get().strip().isdigit() else None
                
                equipment_dict[equipment_no] = Equipment(
                    equipment_number=equipment_no,
                    pmt_number=pmt_number,
                    equipment_description=equipment_description,
                    row_index=row_index
                )
            
            # Create Component object
            phase = row.entries[5].get().strip() if len(row.entries) > 5 else ""
            component_row_index = int(row.entries[0].get().strip()) if row.entries[0].get().strip().isdigit() else None
            
            component = Component(
                component_name=component_name,
                phase=phase,
                existing_data=row_data,  # This contains fluid, material_type, etc.
                row_index=component_row_index
            )
            
            # Add component to equipment
            equipment_dict[equipment_no].add_component(component)
        
        return equipment_dict


class DataTableManager:
    """Manages multiple data table sections with correction tracking"""
    
    def __init__(self, parent_frame, original_equipment_map: Dict[str, Equipment] = None):
        self.parent_frame = parent_frame
        self.sections = {}
        self.on_data_change_callback = None
        self.original_equipment_map = original_equipment_map or {}
        
        # Correction tracking
        self.total_fields_to_fill = 0  # Total empty fields that could be filled
        self.total_fields_corrected = 0  # Fields actually filled by user
        self.correction_details = {}  # Detailed tracking per equipment/component
        
        # Fields to track for corrections
        self.tracked_fields = [
            'fluid', 'material_type', 'spec', 'grade', 'insulation',
            'design_temp', 'design_pressure', 'operating_temp', 'operating_pressure'
        ]
    
    def set_data_change_callback(self, callback: Callable):
        """Set callback for when data changes"""
        self.on_data_change_callback = callback
    
    def create_section(self, file_path: str, columns: List[tuple], 
                       equipment_data: List[Dict]) -> DataTableSection:
        """Create a new table section for a file"""
        # Remove existing section if any
        if file_path in self.sections:
            self.sections[file_path].section_frame.destroy()
        
        # Create new section
        section = DataTableSection(
            self.parent_frame,
            file_path,
            on_data_change=self._handle_data_change
        )
        
        # Add table to section
        section.add_table(columns, equipment_data)
        
        # Store section
        self.sections[file_path] = section
        
        # Initialize correction tracking for this section
        self._initialize_correction_tracking(section, equipment_data)
        
        return section
    
    def _initialize_correction_tracking(self, section: DataTableSection, equipment_data: List[Dict]):
        """Initialize correction tracking for a new section"""
        for row_data in equipment_data:
            eq_no = row_data['equipment_number']
            component_name = row_data['component_name']
            
            # Create tracking key
            key = f"{eq_no}::{component_name}"
            
            if key not in self.correction_details:
                # Count empty fields in original data
                fields_to_fill = 0
                for field in self.tracked_fields:
                    if not row_data.get(field, ''):  # Field is empty
                        fields_to_fill += 1
                
                self.correction_details[key] = {
                    'equipment_no': eq_no,
                    'component_name': component_name,
                    'fields_to_fill': fields_to_fill,
                    'fields_corrected': 0,
                    'original_values': {field: row_data.get(field, '') for field in self.tracked_fields},
                    'current_values': {field: row_data.get(field, '') for field in self.tracked_fields}
                }
                
                self.total_fields_to_fill += fields_to_fill
    
    def _handle_data_change(self, equipment_no: str, component_name: str, data: Dict[str, str]):
        """Handle data change from any row - update correction tracking"""
        key = f"{equipment_no}::{component_name}"
        
        if key in self.correction_details:
            tracking_info = self.correction_details[key]
            new_corrections = 0
            
            # Check each field for corrections
            for field in self.tracked_fields:
                if field in data:
                    old_value = tracking_info['current_values'].get(field, '')
                    new_value = data.get(field, '').strip()
                    
                    # Update current value
                    tracking_info['current_values'][field] = new_value
                    
                    # Check if this is a correction
                    original_empty = not tracking_info['original_values'].get(field, '')
                    now_filled = bool(new_value)
                    value_changed = (old_value != new_value)
                    
                    if original_empty and now_filled and value_changed:
                        # User filled an originally empty field
                        if tracking_info['fields_corrected'] < tracking_info['fields_to_fill']:
                            tracking_info['fields_corrected'] += 1
                            new_corrections += 1
                            self.total_fields_corrected += 1
            
            if new_corrections > 0:
                print(f"DEBUG: {new_corrections} new corrections for {equipment_no}::{component_name}")
                print(f"  Total corrected: {tracking_info['fields_corrected']}/{tracking_info['fields_to_fill']}")
        
        # Call the external callback if set
        if self.on_data_change_callback:
            self.on_data_change_callback(equipment_no, component_name, data)
    
    def get_all_data(self) -> Dict[str, List[Dict]]:
        """Get all data from all sections"""
        all_data = {}
        for file_path, section in self.sections.items():
            all_data[file_path] = section.get_all_data()
        return all_data
    
    def get_all_equipment(self) -> Dict[str, Equipment]:
        """Get all equipment data with correct row indices"""
        equipment_dict = {}
        
        # Start with original equipment to preserve row indices
        for eq_no, original_equipment in self.original_equipment_map.items():
            # Create a copy
            equipment_dict[eq_no] = Equipment(
                equipment_number=original_equipment.equipment_number,
                pmt_number=original_equipment.pmt_number,
                equipment_description=original_equipment.equipment_description,
                row_index=original_equipment.row_index
            )
            
            # Copy components with their row indices
            for original_component in original_equipment.components:
                component_copy = Component(
                    component_name=original_component.component_name,
                    phase=original_component.phase,
                    existing_data=original_component.existing_data.copy(),
                    row_index=original_component.row_index
                )
                equipment_dict[eq_no].add_component(component_copy)
        
        # Now update with UI data from tables
        for file_path, section in self.sections.items():
            for row in section.rows:
                eq_no = row.equipment_no
                component_name = row.component_name
                row_data = row.get_data()
                
                if eq_no in equipment_dict:
                    equipment = equipment_dict[eq_no]
                    
                    # Find the component
                    component = equipment.get_component(component_name)
                    if component:
                        # Update the data but keep the row index
                        for key, value in row_data.items():
                            if value:  # Only update if there's data
                                component.set_existing_data_value(key, value)
        
        return equipment_dict
    
    # CORRECTION TRACKING METHODS
    
    def get_correction_stats(self) -> Dict[str, any]:
        """Get overall correction statistics"""
        return {
            'total_fields_to_fill': self.total_fields_to_fill,
            'total_fields_corrected': self.total_fields_corrected,
            'correction_percentage': (self.total_fields_corrected / self.total_fields_to_fill * 100 
                                     if self.total_fields_to_fill > 0 else 0),
            'equipment_count': len({info['equipment_no'] for info in self.correction_details.values()}),
            'component_count': len(self.correction_details)
        }
    
    def get_correction_details(self) -> Dict[str, List[Dict]]:
        """Get detailed correction information grouped by equipment"""
        equipment_corrections = {}
        
        for key, info in self.correction_details.items():
            eq_no = info['equipment_no']
            
            if eq_no not in equipment_corrections:
                equipment_corrections[eq_no] = []
            
            # Find which specific fields were corrected
            corrected_fields = []
            for field in self.tracked_fields:
                original = info['original_values'].get(field, '')
                current = info['current_values'].get(field, '')
                
                if not original and current:  # Field was empty, now filled
                    corrected_fields.append(field)
            
            equipment_corrections[eq_no].append({
                'component_name': info['component_name'],
                'fields_to_fill': info['fields_to_fill'],
                'fields_corrected': info['fields_corrected'],
                'corrected_fields': corrected_fields,
                'original_values': info['original_values'],
                'current_values': info['current_values']
            })
        
        return equipment_corrections
    
    def get_equipment_correction_summary(self, equipment_no: str) -> Dict[str, any]:
        """Get correction summary for specific equipment"""
        total_to_fill = 0
        total_corrected = 0
        components = []
        
        for key, info in self.correction_details.items():
            if info['equipment_no'] == equipment_no:
                total_to_fill += info['fields_to_fill']
                total_corrected += info['fields_corrected']
                components.append(info['component_name'])
        
        return {
            'equipment_no': equipment_no,
            'components': components,
            'fields_to_fill': total_to_fill,
            'fields_corrected': total_corrected,
            'correction_rate': (total_corrected / total_to_fill * 100 if total_to_fill > 0 else 0)
        }
    
    def reset_correction_stats(self):
        """Reset all correction tracking"""
        self.total_fields_to_fill = 0
        self.total_fields_corrected = 0
        self.correction_details.clear()
        
        # Re-initialize from current sections
        for section in self.sections.values():
            # This would need the original equipment data to re-initialize
            pass
    
    def log_correction_changes(self):
        """Log all correction changes for debugging"""
        print("\n" + "="*60)
        print("CORRECTION TRACKING REPORT")
        print("="*60)
        
        stats = self.get_correction_stats()
        print(f"\nOverall Statistics:")
        print(f"  Total fields to fill: {stats['total_fields_to_fill']}")
        print(f"  Total fields corrected: {stats['total_fields_corrected']}")
        print(f"  Correction rate: {stats['correction_percentage']:.1f}%")
        print(f"  Equipment with corrections: {stats['equipment_count']}")
        print(f"  Components with corrections: {stats['component_count']}")
        
        # Detailed breakdown
        details = self.get_correction_details()
        for eq_no, components in details.items():
            print(f"\nEquipment: {eq_no}")
            for comp_info in components:
                if comp_info['fields_corrected'] > 0:
                    print(f"  Component: {comp_info['component_name']}")
                    print(f"    Corrected: {comp_info['fields_corrected']}/{comp_info['fields_to_fill']}")
                    if comp_info['corrected_fields']:
                        print(f"    Fields: {', '.join(comp_info['corrected_fields'])}")
        
        print("\n" + "="*60)
    
    def clear(self):
        """Clear all sections and reset tracking"""
        for section in self.sections.values():
            if section.section_frame:
                section.section_frame.destroy()
        self.sections.clear()
        
        # Reset correction tracking
        self.total_fields_to_fill = 0
        self.total_fields_corrected = 0
        self.correction_details.clear()