from app.db.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.work import Work, WorkStatus
from app.services.auth_service import hash_password

def seed_database():
    """Create test data for development."""
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(User).first():
            print("Database already seeded")
            return
        
        # Create test user
        user = User(
            username="engineer1",
            email="engineer@example.com",
            password_hash=hash_password("password123"),
            full_name="Test Engineer",
            role=UserRole.ENGINEER
        )
        db.add(user)
        db.flush()
        
        # Create test work
        work = Work(
            name="Test Project",
            description="Sample extraction project",
            user_id=user.id,
            status=WorkStatus.ACTIVE,
            excel_masterfile_url="https://example.com/master.xlsx",
            ppt_template_url="https://example.com/template.pptx"
        )
        db.add(work)
        db.commit()
        
        print(f"Seeded database with user: {user.username}, work: {work.name}")
    
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()