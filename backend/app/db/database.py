"""
Database Configuration
PostgreSQL connection, session management, and initialization
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE ENGINE
# ============================================================================

# Create database engine
# QueuePool: Connection pooling for concurrent requests
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=30,  # ✓ FIXED: Add timeout for acquiring connections
    pool_pre_ping=True,  # Test connections before using them
    echo=settings.ENVIRONMENT == "development",  # Log SQL queries in dev
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
    },
)

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session in routes.
    
    Usage in routes:
        @app.get("/api/works")
        async def list_works(db: Session = Depends(get_db)):
            works = db.query(Work).all()
            return works
    
    The session is automatically committed/rolled back and closed
    after the route returns.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session (for non-route code).
    
    Usage in services:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        db.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================


def init_db():
    """
    Initialize database - create all tables.
    
    Called on application startup via lifespan in main.py.
    Safe to call multiple times (idempotent).
    
    Note: Uses synchronous operation, not async.
    """
    try:
        # Import all models so they're registered with SQLAlchemy
        from app.models.base import Base
        # These imports register the models with the ORM metadata
        from app.models.user import User  # noqa: F401
        from app.models.work import Work  # noqa: F401
        from app.models.work_collaborator import WorkCollaborator  # noqa: F401
        from app.models.equipment import Equipment  # noqa: F401
        from app.models.component import Component  # noqa: F401
        from app.models.extraction import Extraction  # noqa: F401
        from app.models.file import File  # noqa: F401
        from app.models.activity import Activity  # noqa: F401
        
        # Create all tables (idempotent - won't error if they exist)
        Base.metadata.create_all(bind=engine)
        
        logger.info("[OK] Database tables created successfully")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize database: {str(e)}")
        raise


# ============================================================================
# CONNECTION POOLING EVENTS
# ============================================================================

# Optional: Log pool events for debugging
@event.listens_for(QueuePool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Called when a new connection is created"""
    logger.debug("[POOL] New database connection created")


@event.listens_for(QueuePool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Called when a connection is returned to the pool"""
    logger.debug("[POOL] Connection returned to pool")


@event.listens_for(QueuePool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Called when a connection is taken from the pool"""
    logger.debug("[POOL] Connection checked out from pool")


# ============================================================================
# HEALTH CHECK
# ============================================================================


def health_check_db() -> bool:
    """
    Check if database is accessible.
    
    Usage:
        if health_check_db():
            print("Database is healthy")
    """
    try:
        with get_db_context() as db:
            db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


# ============================================================================
# CLEANUP
# ============================================================================


def close_db():
    """
    Close all database connections.
    Called on application shutdown.
    """
    engine.dispose()
    logger.info("[OK] Database connections closed")