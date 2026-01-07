# equipment_component.py
from typing import List, Dict, Any, Optional

class Component:
    def __init__(self, component_name: str, phase: str, existing_data: Dict[str, Any], row_index: Optional[int] = None):
        self._component_name = component_name
        self._phase = phase
        self._row_index = row_index
        self._existing_data = existing_data.copy()  # Create copy to avoid reference issues
    
    # Properties (Getters/Setters)
    @property
    def component_name(self) -> str:
        """Get component name"""
        return self._component_name
    
    @component_name.setter
    def component_name(self, value: str) -> None:
        """Set component name with validation"""
        if not value or not isinstance(value, str):
            raise ValueError("Component name must be a non-empty string")
        self._component_name = value
    
    @property
    def phase(self) -> str:
        """Get phase"""
        return self._phase
    
    @phase.setter
    def phase(self, value: str) -> None:
        """Set phase"""
        self._phase = value
    
    @property
    def row_index(self) -> Optional[int]:
        """Get row index"""
        return self._row_index
    
    @row_index.setter
    def row_index(self, value: Optional[int]) -> None:
        """Set row index with validation"""
        if value is not None and (not isinstance(value, int) or value < 1):
            raise ValueError("Row index must be a positive integer or None")
        self._row_index = value
    
    @property
    def existing_data(self) -> Dict[str, Any]:
        """Get existing data (read-only copy)"""
        return self._existing_data.copy()
    
    # Methods for existing_data management
    def get_existing_data_value(self, key: str) -> Any:
        """Get a specific value from existing_data"""
        return self._existing_data.get(key)
    
    def set_existing_data_value(self, key: str, value: Any) -> None:
        """Set a specific value in existing_data"""
        if key not in self._existing_data:
            raise KeyError(f"Key '{key}' not found in existing_data")
        self._existing_data[key] = value
    
    def update_existing_data(self, updates: Dict[str, Any]) -> None:
        """Update multiple values in existing_data"""
        for key, value in updates.items():
            if key not in self._existing_data:
                raise KeyError(f"Key '{key}' not found in existing_data")
            self._existing_data[key] = value
    
    def get_all_existing_data(self) -> Dict[str, Any]:
        """Get all existing data (copy)"""
        return self._existing_data.copy()
    
    def has_empty_data(self) -> bool:
        """Check if any existing_data values are empty/None"""
        return any(value is None or value == '' for value in self._existing_data.values())
    
    def get_empty_data_fields(self) -> List[str]:
        """Get list of fields that are empty/None"""
        return [key for key, value in self._existing_data.items() if value is None or value == '']
    
    def __repr__(self):
        return f"Component(name='{self._component_name}', phase='{self._phase}')"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Component object to dictionary"""
        return {
            'component_name': self._component_name,
            'phase': self._phase,
            'row_index': self._row_index,
            'existing_data': self._existing_data.copy()
        }