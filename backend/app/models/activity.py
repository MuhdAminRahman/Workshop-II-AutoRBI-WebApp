from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class EntityType(str, enum.Enum):
    WORK = "work"
    EQUIPMENT = "equipment"
    COMPONENT = "component"
    FILE = "file"
    EXTRACTION = "extraction"


class ActivityAction(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    STATUS_CHANGED = "status_changed"


class Activity(BaseModel):
    __tablename__ = "activities"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False)
    data = Column(JSON)
    
    __table_args__ = (
        Index('ix_user_entity', 'user_id', 'entity_type'),
        Index('ix_entity', 'entity_type', 'entity_id'),
    )
    
    # Relationships
    user = relationship("User")