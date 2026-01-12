from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class WorkStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Work(BaseModel):
    __tablename__ = "works"
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(WorkStatus), default=WorkStatus.ACTIVE, nullable=False)
    
    # Template URLs (Cloudinary)
    excel_masterfile_url = Column(String(500))
    ppt_template_url = Column(String(500))
    
    # Relationships
    # ✅ Changed: collaborators instead of single user_id
    collaborators = relationship("WorkCollaborator", back_populates="work", cascade="all, delete-orphan")
    equipment = relationship("Equipment", back_populates="work", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="work", cascade="all, delete-orphan")
    files = relationship("File", back_populates="work", cascade="all, delete-orphan")