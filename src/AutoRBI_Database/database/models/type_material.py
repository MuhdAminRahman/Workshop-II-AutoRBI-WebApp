from sqlalchemy import Column, String
from database import Base

class TypeMaterial(Base):
    __tablename__ = "type_material"

    material_spec = Column(String, primary_key=True)     # Example: SA-516
    material_type = Column(String, nullable=False)       # Example: Carbon Steel

    def __repr__(self):
        return (
            f"TypeMaterial(spec='{self.material_spec}', "
            f"type='{self.material_type}')"
    )

