from sqlalchemy import Boolean, Column, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class UserRole(str, enum.Enum):
    ENGINEER = "Engineer"
    ADMIN = "Admin"


class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(SQLEnum(UserRole), default=UserRole.ENGINEER, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    # ❌ Deprecated: works relationship (kept for backward compatibility if needed)
    # works = relationship("Work", back_populates="user", cascade="all, delete-orphan")
    
    # ✅ New: Collaborations on works
    collaborations = relationship("WorkCollaborator", back_populates="user", cascade="all, delete-orphan")
    
    # Existing
    files = relationship("File", back_populates="created_by_user")