from sqlalchemy import Column, Integer, String, Text, Enum, DateTime
from datetime import datetime
from database.base import Base

class Work(Base):
    __tablename__ = "work"

    work_id = Column(Integer, primary_key=True, index=True)
    work_name = Column(String, nullable=False)
    description = Column(Text)

    status = Column(
        Enum("In progress", "Completed", name="work_statuses"),
        default="In progress",
        nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Must match actual DB columns exactly
    excel_path = Column(Text, nullable=True)
    ppt_path = Column(Text, nullable=True)

    def __repr__(self):
        return (
            f"Work(id={self.work_id}, name='{self.work_name}', "
            f"status='{self.status}', "
            f"excel='{self.excel_path}', "
            f"ppt='{self.ppt_path}', "
            f"created_at='{self.created_at}')"
        )
