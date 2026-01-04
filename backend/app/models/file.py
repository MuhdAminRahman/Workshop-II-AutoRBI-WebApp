from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class FileType(str, enum.Enum):
    EXCEL = "excel"
    POWERPOINT = "powerpoint"

class File(BaseModel):
    __tablename__ = "files"
    
    work_id = Column(Integer, ForeignKey("works.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    file_type = Column(String(20), nullable=False)  # excel, powerpoint
    version_number = Column(Integer, nullable=False)
    file_url = Column(String(500), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('work_id', 'file_type', 'version_number', name='uq_work_file_version'),
    )
    
    # Relationships
    work = relationship("Work", back_populates="files")
    created_by_user = relationship("User", back_populates="files")