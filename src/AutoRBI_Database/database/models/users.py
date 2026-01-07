from sqlalchemy import Column, Integer, String, DateTime, Enum, text
from datetime import datetime
from database.base import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)

    role = Column(Enum("Admin", "Engineer", name="user_roles"), nullable=False)
    status = Column(
        Enum("Active", "Inactive", name="user_statuses"),
        default="Active",
        nullable=False,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    email = Column(String, nullable=True, server_default=text("'email@Ipetro.com'"))

    def __repr__(self):
        return (
            f"User(id={self.user_id}, username='{self.username}', "
            f"role='{self.role}', status='{self.status}')"
        )
