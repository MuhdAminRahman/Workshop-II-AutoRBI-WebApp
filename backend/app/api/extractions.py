"""
Extractions Routes
File upload, PDF processing, and extraction progress tracking
Handles single and multiple file extractions
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, WebSocket, Query, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
from datetime import datetime

from app.db.database import get_db
from app.models.user import User
from app.models.extraction import Extraction
from app.dependencies import get_current_user
from app.services.work_service import get_work_by_id
from app.services.permission_service import can_edit

logger = logging.getLogger(__name__)

# Create router for extraction endpoints
router = APIRouter()

# ============================================================================
# SCHEMAS
# ============================================================================


class ExtractionStatusResponse(BaseModel):
    id: int
    work_id: int
    pdf_url: str
    status: str
    processed_pages: int
    total_pages: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ExtractionStartResponse(BaseModel):
    extraction_id: int  # Match frontend expectation
    work_id: int
    pdf_url: str
    status: str
    message: str
    
    class Config:
        from_attributes = True
        populate_by_name = True


# ============================================================================
# START EXTRACTION - POST /api/works/{workId}/extraction/start
# ============================================================================


@router.post(
    "/works/{work_id}/extraction/start",
    response_model=ExtractionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start PDF extraction",
    description="Upload a GA drawing PDF and start equipment extraction",
)
async def start_extraction(
    work_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExtractionStartResponse:
    """
    Start extraction process for a PDF file.
    
    Args:
        work_id: ID of the work project
        file: PDF file to extract from
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
        
    Returns:
        ExtractionStartResponse with extraction details
        
    Raises:
        404: Work not found
        403: User doesn't have permission to edit work
        400: Invalid file type
    """
    
    # Get work
    work = get_work_by_id(work_id, db)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work with id {work_id} not found"
        )
    
    # Check permission
    if not can_edit(current_user.id, work_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this work"
        )
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Create extraction record
    try:
        # Read file content
        file_content = await file.read()
        
        # Create extraction in database
        extraction = Extraction(
            work_id=work_id,
            pdf_url=file.filename,  # Store file name as pdf_url for now
            status="pending",
            processed_pages=0,
            total_pages=0,
            error_message=None,
        )
        
        db.add(extraction)
        db.commit()
        db.refresh(extraction)
        
        logger.info(f"Extraction {extraction.id} created for work {work_id}")
        
        return ExtractionStartResponse(
            extraction_id=extraction.id,
            work_id=work_id,
            pdf_url=file.filename,
            status="pending",
            message="Extraction started successfully. Processing will begin shortly."
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting extraction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start extraction"
        )


# ============================================================================
# GET EXTRACTION STATUS - GET /api/extractions/{extractionId}/status
# ============================================================================


@router.get(
    "/extractions/{extraction_id}/status",
    response_model=ExtractionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get extraction status",
    description="Get current status and progress of an extraction",
)
async def get_extraction_status(
    extraction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExtractionStatusResponse:
    """
    Get extraction status and progress.
    
    Args:
        extraction_id: ID of the extraction
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)
        
    Returns:
        ExtractionStatusResponse with current progress
        
    Raises:
        404: Extraction not found
    """
    
    # Get extraction
    extraction = db.query(Extraction).filter(Extraction.id == extraction_id).first()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction with id {extraction_id} not found"
        )
    
    # Verify user has access to the work
    if not can_edit(current_user.id, extraction.work_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this extraction"
        )
    
    return ExtractionStatusResponse(
        id=extraction.id,
        work_id=extraction.work_id,
        pdf_url=extraction.pdf_url,
        status=extraction.status,
        processed_pages=extraction.processed_pages,
        total_pages=extraction.total_pages,
        error_message=extraction.error_message,
        created_at=extraction.created_at,
        updated_at=extraction.updated_at,
    )


# ============================================================================
# WEBSOCKET - ws://localhost:5000/api/ws/extractions/{extractionId}
# ============================================================================

# Store active WebSocket connections
active_connections: dict = {}


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, extraction_id: int, websocket: WebSocket):
        """Connect a WebSocket client"""
        await websocket.accept()
        if extraction_id not in self.active_connections:
            self.active_connections[extraction_id] = []
        self.active_connections[extraction_id].append(websocket)
        logger.info(f"WebSocket connected for extraction {extraction_id}")
    
    def disconnect(self, extraction_id: int, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if extraction_id in self.active_connections:
            self.active_connections[extraction_id].remove(websocket)
            if not self.active_connections[extraction_id]:
                del self.active_connections[extraction_id]
        logger.info(f"WebSocket disconnected for extraction {extraction_id}")
    
    async def broadcast(self, extraction_id: int, message: dict):
        """Broadcast message to all connected clients for an extraction"""
        if extraction_id in self.active_connections:
            for connection in self.active_connections[extraction_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {str(e)}")


manager = ConnectionManager()


@router.websocket("/ws/extractions/{extraction_id}")
async def websocket_extraction_progress(
    websocket: WebSocket,
    extraction_id: int,
    token: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time extraction progress.
    
    Messages received from client:
    - Keep-alive pings
    
    Messages sent to client:
    - {"type": "progress", "page": int, "total": int, "percent": int}
    - {"type": "completed", "extraction_id": int}
    - {"type": "error", "message": str}
    - {"type": "status", "status": str}
    
    Query Parameters:
        token: JWT authentication token
        extraction_id: Extraction ID (in path)
    """
    
    try:
        # Verify extraction exists
        extraction = db.query(Extraction).filter(Extraction.id == extraction_id).first()
        if not extraction:
            await websocket.close(code=1008, reason="Extraction not found")
            return
        
        # Accept connection
        await manager.connect(extraction_id, websocket)
        
        try:
            # Keep connection alive and listen for messages
            while True:
                # Wait for messages from client (keep-alive or control messages)
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    logger.debug(f"WebSocket message from client: {message}")
                    
                    # Handle client messages if needed
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from WebSocket: {data}")
                    
        except WebSocketDisconnect:
            manager.disconnect(extraction_id, websocket)
            logger.info(f"WebSocket client disconnected from extraction {extraction_id}")
            
    except Exception as e:
        logger.error(f"WebSocket error for extraction {extraction_id}: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
