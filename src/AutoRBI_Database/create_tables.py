from database.base import Base
from database.session import engine

# Import ALL models so SQLAlchemy knows them
from database.models import (
    User,
    Work,
    TypeMaterial,
    Equipment,
    Component,
    AssignWork,
    CorrectionLog,
    WorkHistory,
)

print("Creating tables...")

Base.metadata.create_all(bind=engine)

print("All tables created successfully!")
