from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from datetime import datetime
import enum

class ExtractionStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Extraction(BaseModel):
    __tablename__ = "extractions"
    
    work_id = Column(Integer, ForeignKey("works.id"), nullable=False, index=True)
    
    status = Column(String(20), default=ExtractionStatus.PENDING, nullable=False, index=True)
    
    # PDF information
    pdf_url = Column(String(500), nullable=False)
    total_pages = Column(Integer, default=0)
    processed_pages = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text)
    
    # Timestamps
    completed_at = Column(DateTime)
    
    # Relationships
    work = relationship("Work", back_populates="extractions")