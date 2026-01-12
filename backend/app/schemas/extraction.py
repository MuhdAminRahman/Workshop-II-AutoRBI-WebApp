"""
Extraction Schemas
Pydantic models for extraction request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# REQUESTS (What client sends to API)
# ============================================================================


class StartExtractionRequest(BaseModel):
    """Start new extraction job"""
    
    excel_file: Optional[str] = Field(None, description="Cloudinary URL to Excel masterfile")
    """Excel masterfile URL (if already uploaded)"""
    
    ppt_template: Optional[str] = Field(None, description="Cloudinary URL to PPT template")
    """PPT template URL (if already uploaded)"""
    
    class Config:
        example = {
            "excel_file": "https://res.cloudinary.com/.../masterfile.xlsx",
            "ppt_template": "https://res.cloudinary.com/.../template.pptx"
        }


# ============================================================================
# RESPONSES (What API sends back to client)
# ============================================================================


class ComponentExtractedResponse(BaseModel):
    """Extracted component data"""
    
    component_name: str
    """Component name"""
    
    phase: Optional[str] = None
    """Phase: Vapor, Liquid, Two-phase"""
    
    fluid: Optional[str] = None
    """Fluid type"""
    
    material_spec: Optional[str] = None
    """Material specification"""
    
    material_grade: Optional[str] = None
    """Material grade"""
    
    insulation: Optional[str] = None
    """Insulation type"""
    
    design_temp: Optional[str] = None
    """Design temperature"""
    
    design_pressure: Optional[str] = None
    """Design pressure"""
    
    operating_temp: Optional[str] = None
    """Operating temperature"""
    
    operating_pressure: Optional[str] = None
    """Operating pressure"""


class EquipmentExtractedResponse(BaseModel):
    """Extracted equipment data"""
    
    equipment_number: str
    """Equipment identifier (e.g., E-101)"""
    
    pmt_number: Optional[str] = None
    """PMT number"""
    
    description: Optional[str] = None
    """Description"""
    
    components: List[ComponentExtractedResponse] = []
    """List of components"""


class ExtractionStartResponse(BaseModel):
    """Response when starting extraction"""
    
    extraction_id: int
    """Extraction job ID (use for polling/WebSocket)"""
    
    work_id: int
    """Work project ID"""
    
    status: str
    """Status: pending, in_progress, completed, failed"""
    
    message: str
    """Info message"""
    
    class Config:
        example = {
            "extraction_id": 5,
            "work_id": 1,
            "status": "pending",
            "message": "Extraction queued and will process asynchronously"
        }


class ExtractionStatusResponse(BaseModel):
    """Extraction job status"""
    
    id: int
    """Extraction ID"""
    
    work_id: int
    """Work ID"""
    
    status: str
    """pending, in_progress, completed, failed"""
    
    total_pages: int
    """Total PDF pages"""
    
    processed_pages: int
    """Pages processed so far"""
    
    progress_percent: float
    """Progress percentage (0-100)"""
    
    error_message: Optional[str] = None
    """Error message if failed"""
    
    created_at: datetime
    """When extraction started"""
    
    completed_at: Optional[datetime] = None
    """When extraction completed"""
    
    class Config:
        example = {
            "id": 5,
            "work_id": 1,
            "status": "in_progress",
            "total_pages": 10,
            "processed_pages": 3,
            "progress_percent": 30,
            "error_message": None,
            "created_at": "2024-01-15T10:30:00",
            "completed_at": None
        }


class ExtractionCompleteResponse(BaseModel):
    """Response when extraction completes"""
    
    status: str
    """completed"""
    
    equipment_extracted: List[EquipmentExtractedResponse]
    """List of extracted equipment"""
    
    equipment_count: int
    """Total equipment extracted"""
    
    total_components: int
    """Total components extracted"""
    
    excel_url: Optional[str] = None
    """URL to generated Excel file with extracted data"""
    
    message: str
    """Success message"""
    
    class Config:
        example = {
            "status": "completed",
            "equipment_extracted": [
                {
                    "equipment_number": "E-101",
                    "components": [
                        {
                            "component_name": "Shell",
                            "fluid": "Steam"
                        }
                    ]
                }
            ],
            "equipment_count": 5,
            "total_components": 12,
            "excel_url": "https://res.cloudinary.com/.../work_1_excel_v1.xlsx",
            "message": "Extraction completed successfully"
        }


# ============================================================================
# WEBSOCKET MESSAGES
# ============================================================================


class ProgressMessage(BaseModel):
    """Progress update message (via WebSocket)"""
    
    type: str = "progress"
    """Message type: always 'progress'"""
    
    page: int
    """Current page number"""
    
    total: int
    """Total pages"""
    
    percent: float
    """Progress percentage"""


class CompletionMessage(BaseModel):
    """Completion message (via WebSocket)"""
    
    type: str = "completed"
    """Message type: always 'completed'"""
    
    equipment_count: int
    """Total equipment extracted"""
    
    equipment_extracted: List[EquipmentExtractedResponse]
    """List of extracted equipment"""
    
    excel_url: Optional[str] = None
    """Generated Excel file URL"""


class ErrorMessage(BaseModel):
    """Error message (via WebSocket)"""
    
    type: str = "error"
    """Message type: always 'error'"""
    
    message: str
    """Error description"""