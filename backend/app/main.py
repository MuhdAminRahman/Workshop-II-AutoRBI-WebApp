"""
AutoRBI FastAPI Application
Main entry point for the backend server
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.database import init_db


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# ============================================================================
# STARTUP & SHUTDOWN EVENTS
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - startup and shutdown.
    
    Startup: Initialize database, log startup info
    Shutdown: Close connections, log shutdown info
    """
    # === STARTUP ===
    logger.info("🚀 Starting AutoRBI API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'unknown'}")
    
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise
    
    yield
    
    # === SHUTDOWN ===
    logger.info("🛑 Shutting down AutoRBI API...")
    logger.info("Database connections closed")


# ============================================================================
# CREATE FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="AutoRBI API",
    description="RBI Data Extraction & Reporting Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# 1. CORS Middleware - Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",  # Flask development frontend
        "http://localhost:5173",  # Vite development frontend
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:5000",  # Flask localhost alternative
        "http://127.0.0.1:5173",  # Vite localhost alternative
        "http://127.0.0.1:3000",  # Alternative port alternative
        "https://workshop-ii-autorbi-webapp-frontend.onrender.com",  # Production frontend
        "https://autorbi-frontend.onrender.com",  # Alternative production frontend
        "https://workshop-ii-autorbi-webapp.onrender.com",  # Same domain (for internal calls)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Type", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=3600,  # Cache CORS preflight for 1 hour
)

# 2. Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses"""
    start_time = datetime.utcnow()
    
    # Log request
    logger.debug(f"{request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Calculate request duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Log response
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)"
    )
    
    return response

# 3. Exception handling middleware
@app.middleware("http")
async def error_middleware(request: Request, call_next):
    """Global error handling"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions globally"""
    logger.error(f"Global exception handler: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc),
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API is running"""
    return {
        "message": "Welcome to AutoRBI API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
    }


@app.get("/status", tags=["Health"])
async def status_check():
    """Detailed status check"""
    return {
        "api": {
            "status": "running",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
        },
        "database": {
            "configured": True,
            "url": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "unknown",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# API ROUTERS (Will add in next steps)
# ============================================================================

# Routes will be included here:
from app.api import auth, works, extractions, reports, history, analytics, equipments,users, admin_works
#
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(works.router, prefix="/api/works", tags=["works"])
app.include_router(extractions.router, prefix="/api", tags=["extractions"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(equipments.router, prefix="/api/equipments", tags=["equipment"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(admin_works.router, prefix="/api/admin", tags=["admin"])


# ============================================================================
# API DOCUMENTATION
# ============================================================================

# When running, visit:
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
# - OpenAPI JSON: http://localhost:8000/openapi.json


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Run development server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info",
    )