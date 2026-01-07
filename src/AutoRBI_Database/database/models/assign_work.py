from sqlalchemy import Column, Integer, ForeignKey, DateTime
from datetime import datetime
from database import Base


class AssignWork(Base):
    __tablename__ = "assign_work"

    assignment_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    work_id = Column(Integer, ForeignKey("work.work_id"), nullable=False)

    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"AssignWork(id={self.assignment_id}, user_id={self.user_id}, "
            f"work_id={self.work_id}, assigned_at='{self.assigned_at}')"
        )
