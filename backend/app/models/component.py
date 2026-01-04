from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Component(BaseModel):
    __tablename__ = "components"
    
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False, index=True)
    
    # Component identification
    component_name = Column(String(100), nullable=False)
    phase = Column(String(50))  # Vapor, Liquid, Two-phase
    
    # Fluid properties
    fluid = Column(String(100))
    
    # Material specification
    material_spec = Column(String(100))
    material_grade = Column(String(50))
    insulation = Column(String(50))
    
    # Design conditions
    design_temp = Column(String(50))  # e.g., "150°C"
    design_pressure = Column(String(50))  # e.g., "16 bar"
    
    # Operating conditions
    operating_temp = Column(String(50))
    operating_pressure = Column(String(50))
    
    # Relationships
    equipment = relationship("Equipment", back_populates="components")