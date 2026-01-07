from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# SIMPLE DIRECT CONNECTION (NO dotenv yet)
DATABASE_URL = "postgresql+psycopg2://autorbi_user:StrongPasswordHere@localhost:5432/autorbi1"
# Create the database engine
engine = create_engine(DATABASE_URL)

# Create the Session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# engine = the actual connection to PostgreSQL
# SessionLocal = used to talk to the database
