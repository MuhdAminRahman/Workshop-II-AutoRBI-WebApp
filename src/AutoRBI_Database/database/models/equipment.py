
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, UniqueConstraint
from datetime import datetime
from database import Base

class Equipment(Base):
    __tablename__ = "equipment"

    # Unique within a WORK, not globally
    __table_args__ = (
        UniqueConstraint("work_id", "equipment_no", name="uq_work_equipment_no"),
    )

    equipment_id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    work_id = Column(Integer, ForeignKey("work.work_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    # Equipment fields
    equipment_no = Column(String, nullable=False)  # Removed unique=True
    pmt_no = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    drawing_path = Column(Text, nullable=True)

    extracted_date = Column(DateTime, nullable=True)

    def __repr__(self):
        return (
            f"Equipment(id={self.equipment_id}, work_id={self.work_id}, "
            f"no='{self.equipment_no}', pmt='{self.pmt_no}', "
            f"drawing_path='{self.drawing_path}', extracted_date='{self.extracted_date}')"
        )
