from sqlalchemy import Column, Integer, ForeignKey, DateTime
from datetime import datetime
from database import Base

class CorrectionLog(Base):
    __tablename__ = "correction_log"

    correction_id = Column(Integer, primary_key=True, index=True)

    equipment_id = Column(Integer, ForeignKey("equipment.equipment_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    fields_to_fill = Column(Integer, nullable=False)
    fields_corrected = Column(Integer, nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"CorrectionLog(id={self.correction_id}, equipment_id={self.equipment_id}, "
            f"user_id={self.user_id}, corrected={self.fields_corrected}/"
            f"{self.fields_to_fill}, timestamp='{self.timestamp}')"
    )

