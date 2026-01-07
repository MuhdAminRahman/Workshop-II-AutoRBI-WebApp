from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from database import Base

class Component(Base):
    __tablename__ = "component"

    component_id = Column(Integer, primary_key=True, index=True)

    # FK to equipment
    equipment_id = Column(Integer, ForeignKey("equipment.equipment_id"), nullable=False)

    # Basic component info
    part_name = Column(String, nullable=False)
    phase = Column(String, nullable=True)

    # Extracted + corrected fields
    fluid = Column(String, nullable=True)
    material_spec = Column(String, ForeignKey("type_material.material_spec"), nullable=True)
    material_grade = Column(String, nullable=True)
    insulation = Column(Enum("yes", "no", name="insulation_status"), nullable=True)

    # Extracted values should be stored as STRING because OCR may include units/symbols
    design_temp = Column(String, nullable=True)
    design_pressure = Column(String, nullable=True)
    operating_temp = Column(String, nullable=True)
    operating_pressure = Column(String, nullable=True)

    def __repr__(self):
        return (
            f"Component(id={self.component_id}, part='{self.part_name}', "
            f"phase='{self.phase}', equipment_id={self.equipment_id})"
        )
