from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from datetime import datetime
from database import Base

class WorkHistory(Base):
    __tablename__ = "work_history"

    history_id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    work_id = Column(Integer, ForeignKey("work.work_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    # Nullable because not every action is tied to equipment
    equipment_id = Column(Integer, ForeignKey("equipment.equipment_id"), nullable=True)

    action_type = Column(String, nullable=False)    # e.g. "upload_pdf", "extract", "correct", "generate_excel"
    description = Column(Text, nullable=True)       # Optional extra details

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"WorkHistory(id={self.history_id}, work_id={self.work_id}, "
            f"user_id={self.user_id}, equipment_id={self.equipment_id}, "
            f"action='{self.action_type}', timestamp='{self.timestamp}')"
    )

