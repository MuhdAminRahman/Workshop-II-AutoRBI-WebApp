from dataclasses import dataclass, field
from typing import Dict, List, Optional
from models import Equipment

@dataclass
class ViewState:
    """Centralized view state management"""
    
    # Page state
    current_page: int = 1
    extraction_complete: bool = False
    page_1_active: bool = False
    page_2_active: bool = False
    
    # Data state
    selected_files: List[str] = field(default_factory=list)
    equipment_map: Dict[str, Equipment] = field(default_factory=dict)
    extracted_equipment_data: Dict[str, Dict[str, Equipment]] = field(default_factory=dict)
    file_to_textboxes: Dict[str, List] = field(default_factory=dict)
    converted_files: List[str] = field(default_factory=list)
    
    # Processing state
    converted_images_dir: Optional[str] = None
    selected_excel: Optional[str] = None
    
    # Add this for can_save tracking (make it a field, not a property)
    _can_save: bool = field(default=False, init=False)  # Private attribute
    
    @property
    def has_files(self) -> bool:
        """Check if any files are selected"""
        return len(self.selected_files) > 0
    
    @property
    def has_equipment_data(self) -> bool:
        """Check if equipment data exists"""
        return len(self.equipment_map) > 0
    
    @property
    def can_proceed_to_page_2(self) -> bool:
        """Check if can proceed to page 2"""
        return self.extraction_complete and self.has_files
    
    @property
    def can_save(self) -> bool:
        """Check if data can be saved"""
        return self._can_save  # Return the private attribute
    
    @can_save.setter
    def can_save(self, value: bool) -> None:
        """Set can_save property"""
        self._can_save = value
    
    def add_file(self, file_path: str) -> None:
        """Add file to selection"""
        if file_path not in self.selected_files:
            self.selected_files.append(file_path)
    
    def clear_files(self) -> None:
        """Clear all selected files"""
        self.selected_files.clear()
    
    def set_equipment_data(self, file_path: str, equipment_list: Dict[str, Equipment]) -> None:
        """Set extracted equipment data for a file"""
        self.extracted_equipment_data[file_path] = equipment_list
    
    def get_equipment_for_file(self, file_path: str) -> Dict[str, Equipment]:
        """Get equipment data for a specific file"""
        return self.extracted_equipment_data.get(file_path, {})