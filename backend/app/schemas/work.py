"""
Work Schemas
Pydantic models for work project request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# REQUESTS (What client sends to API)
# ============================================================================


class WorkCreateRequest(BaseModel):
    """Create new work request"""
    
    name: str = Field(..., min_length=3, max_length=100)
    """Work project name"""
    
    description: Optional[str] = Field(None, max_length=500)
    """Optional description"""
    
    class Config:
        example = {
            "name": "Refinery Unit A Extraction",
            "description": "Extract equipment data from GA drawings"
        }


class WorkUpdateRequest(BaseModel):
    """Update work request"""
    
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    """Work project name"""
    
    description: Optional[str] = Field(None, max_length=500)
    """Description"""
    
    status: Optional[str] = Field(None)
    """Status: active, completed, archived"""
    
    class Config:
        example = {
            "name": "Updated Name",
            "status": "completed"
        }


class WorkUploadFilesRequest(BaseModel):
    """Upload Excel masterfile and PPT template"""
    
    excel_file_name: str
    """Name of uploaded Excel file (from multipart upload)"""
    
    ppt_file_name: str
    """Name of uploaded PPT file (from multipart upload)"""
    
    class Config:
        example = {
            "excel_file_name": "masterfile.xlsx",
            "ppt_file_name": "template.pptx"
        }


# ============================================================================
# RESPONSES (What API sends back to client)
# ============================================================================


class ComponentResponse(BaseModel):
    """Component data response"""
    
    id: int
    """Component ID"""
    
    component_name: str
    """Component name"""
    
    phase: Optional[str]
    """Phase: Vapor, Liquid, Two-phase"""
    
    fluid: Optional[str]
    """Fluid type"""
    
    material_spec: Optional[str]
    """Material specification"""
    
    material_grade: Optional[str]
    """Material grade"""
    
    insulation: Optional[str]
    """Insulation type"""
    
    design_temp: Optional[str]
    """Design temperature"""
    
    design_pressure: Optional[str]
    """Design pressure"""
    
    operating_temp: Optional[str]
    """Operating temperature"""
    
    operating_pressure: Optional[str]
    """Operating pressure"""
    
    created_at: datetime
    """When component was extracted"""
    
    class Config:
        from_attributes = True


class EquipmentResponse(BaseModel):
    """Equipment with components"""
    
    id: int
    """Equipment ID"""
    
    equipment_number: str
    """Equipment identifier (e.g., E-101)"""
    
    pmt_number: Optional[str]
    """PMT number"""
    
    description: Optional[str]
    """Description"""
    
    extracted_date: Optional[datetime]
    """When equipment was extracted"""
    
    components: List[ComponentResponse] = []
    """List of components"""
    
    created_at: datetime
    """When equipment was created"""
    
    class Config:
        from_attributes = True


class FileVersionResponse(BaseModel):
    """File version response"""
    
    id: int
    """File ID"""
    
    file_type: str
    """excel or powerpoint"""
    
    version_number: int
    """Version number"""
    
    file_url: str
    """URL to download file"""
    
    created_at: datetime
    """When file was created"""
    
    class Config:
        from_attributes = True


class CollaboratorInfo(BaseModel):
    """Collaborator information in work response"""
    
    user_id: int
    """User ID"""
    
    email: str
    """User email"""
    
    full_name: Optional[str]
    """User full name"""
    
    role: str
    """Collaborator role: owner, editor, viewer"""
    
    class Config:
        from_attributes = True


class WorkResponse(BaseModel):
    """Complete work data response"""
    
    id: int
    """Work ID"""
    
    name: str
    """Work project name"""
    
    description: Optional[str]
    """Description"""
    
    status: str
    """Status: active, completed, archived"""
    
    excel_masterfile_url: Optional[str]
    """URL to Excel masterfile template"""
    
    ppt_template_url: Optional[str]
    """URL to PowerPoint template"""
    
    created_at: datetime
    """When work was created"""
    
    class Config:
        from_attributes = True
        example = {
            "id": 1,
            "name": "Refinery Unit A",
            "description": "Heat exchanger extraction",
            "status": "active",
            "excel_masterfile_url": "https://res.cloudinary.com/...",
            "ppt_template_url": "https://res.cloudinary.com/...",
            "created_at": "2024-01-15T10:30:00"
        }


class WorkDetailResponse(BaseModel):
    """Work with equipment and files"""
    
    work: WorkResponse
    """Work project data"""
    
    equipment: List[EquipmentResponse] = []
    """List of equipment with components"""
    
    files: List[FileVersionResponse] = []
    """List of generated files (Excel, PPT versions)"""
    
    collaborators: List[CollaboratorInfo] = []
    """List of collaborators on this work"""
    
    class Config:
        example = {
            "work": {
                "id": 1,
                "name": "Refinery Unit A",
                "description": "Heat exchanger extraction",
                "status": "active",
                "excel_masterfile_url": "https://res.cloudinary.com/...",
                "ppt_template_url": "https://res.cloudinary.com/...",
                "created_at": "2024-01-15T10:30:00"
            },
            "equipment": [
                {
                    "id": 1,
                    "equipment_number": "E-101",
                    "pmt_number": "PMT-2024-001",
                    "description": "Shell and Tube Heat Exchanger",
                    "extracted_date": "2024-01-15T11:00:00",
                    "components": []
                }
            ],
            "files": [],
            "collaborators": [
                {
                    "user_id": 1,
                    "email": "owner@example.com",
                    "full_name": "John Owner",
                    "role": "owner"
                }
            ]
        }


class WorksListResponse(BaseModel):
    """List of works"""
    
    works: List[WorkResponse]
    """Array of work projects"""
    
    total: int
    """Total count"""
    
    class Config:
        example = {
            "works": [
                {
                    "id": 1,
                    "name": "Project 1",
                    "status": "active"
                }
            ],
            "total": 1
        }