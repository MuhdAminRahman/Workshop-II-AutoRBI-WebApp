from sqlalchemy import CheckConstraint, Column, Integer, String, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class CollaboratorRole(str, enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class WorkCollaborator(BaseModel):
    __tablename__ = "work_collaborators"
    
    work_id = Column(Integer, ForeignKey("works.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), default='editor', nullable=False)
    
    __table_args__ = (
        UniqueConstraint('work_id', 'user_id', name='uq_work_user'),
        CheckConstraint("role IN ('owner', 'editor', 'viewer')", name='valid_role'),
    )
    
    # Relationships
    work = relationship("Work", back_populates="collaborators")
    user = relationship("User", back_populates="collaborations")


# ============================================================================
# NOTE: This file is imported by work.py and user.py for relationships
# ============================================================================