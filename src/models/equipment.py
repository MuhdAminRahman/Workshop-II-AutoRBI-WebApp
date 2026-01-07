# equipment.py
from typing import List, Dict, Any, Optional
from .equipment_component import Component

class Equipment:
    def __init__(self, equipment_number: str, pmt_number: str, equipment_description: str, row_index: Optional[int] = None):
        self._equipment_number = equipment_number
        self._pmt_number = pmt_number
        self._equipment_description = equipment_description
        self._row_index = row_index
        self._components: List[Component] = []
    
    # Properties (Getters/Setters)
    @property
    def equipment_number(self) -> str:
        """Get equipment number"""
        return self._equipment_number
    
    @equipment_number.setter
    def equipment_number(self, value: str) -> None:
        """Set equipment number with validation"""
        if not value or not isinstance(value, str):
            raise ValueError("Equipment number must be a non-empty string")
        self._equipment_number = value
    
    @property
    def pmt_number(self) -> str:
        """Get PMT number"""
        return self._pmt_number
    
    @pmt_number.setter
    def pmt_number(self, value: str) -> None:
        """Set PMT number"""
        self._pmt_number = value
    
    @property
    def equipment_description(self) -> str:
        """Get equipment description"""
        return self._equipment_description
    
    @equipment_description.setter
    def equipment_description(self, value: str) -> None:
        """Set equipment description"""
        self._equipment_description = value
    
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
    def components(self) -> List[Component]:
        """Get components list (read-only)"""
        return self._components.copy()  # Return copy to prevent direct modification
    
    # Methods for component management
    def add_component(self, component: Component) -> None:
        """Add a component to this equipment"""
        if not isinstance(component, Component):
            raise TypeError("Can only add Component objects")
        self._components.append(component)
    
    def remove_component(self, component_name: str) -> bool:
        """Remove a component by name, returns True if removed"""
        for i, component in enumerate(self._components):
            if component.component_name == component_name:
                self._components.pop(i)
                return True
        return False
    
    def get_component(self, component_name: str) -> Optional[Component]:
        """Get a component by name"""
        for component in self._components:
            if component.component_name == component_name:
                return component
        return None
    
    def has_component(self, component_name: str) -> bool:
        """Check if equipment has a component with given name"""
        return any(comp.component_name == component_name for comp in self._components)
    
    def __repr__(self):
        return f"Equipment(number='{self._equipment_number}', description='{self._equipment_description}', components_count={len(self._components)})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Equipment object to dictionary"""
        return {
            'equipment_number': self._equipment_number,
            'pmt_number': self._pmt_number,
            'equipment_description': self._equipment_description,
            'row_index': self._row_index,
            'components': [component.to_dict() for component in self._components]
        }