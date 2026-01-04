from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from datetime import datetime

class Equipment(BaseModel):
    __tablename__ = "equipment"
    
    work_id = Column(Integer, ForeignKey("works.id"), nullable=False, index=True)
    equipment_number = Column(String(50), nullable=False)
    pmt_number = Column(String(50))
    description = Column(Text)
    extracted_date = Column(DateTime)
    
    __table_args__ = (
        UniqueConstraint('work_id', 'equipment_number', name='uq_work_equipment'),
    )
    
    # Relationships
    work = relationship("Work", back_populates="equipment")
    components = relationship("Component", back_populates="equipment", cascade="all, delete-orphan")