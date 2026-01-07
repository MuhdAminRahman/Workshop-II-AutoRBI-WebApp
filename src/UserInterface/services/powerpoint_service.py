# File: services/powerpoint_service.py
"""
PowerPoint Export Service - Handles PowerPoint generation and export logic
"""
import os
import time
from typing import List, Dict, Optional
import customtkinter as ctk
from tkinter import messagebox

from models import Equipment
from powerpoint_generator import PowerPointGenerator


class PowerPointExportService:
    """Service for handling PowerPoint export operations"""
    
    def __init__(self, project_root: str, log_callback=None):
        self.project_root = project_root
        self.log_callback = log_callback or (lambda msg: print(f"PPT: {msg}"))
    
    def validate_prerequisites(self, equipment_map: dict, work_id: str) -> tuple[bool, str]:
        """Validate prerequisites for PowerPoint export"""
        if not equipment_map:
            return False, "No equipment data available"
        
        if not work_id:
            return False, "No work selected"
        
        return True, ""
    
    def get_output_path(self, work_id: str, filename: str) -> Optional[str]:
        """Get PowerPoint output path for current work"""
        try:
            ppt_dir = os.path.join(self.project_root, "src", "output_files", work_id, "powerpoint")
            os.makedirs(ppt_dir, exist_ok=True)
            return os.path.join(ppt_dir, filename)
        except Exception as e:
            self._log(f"❌ Error creating output directory: {e}")
            return None
    
    def get_template_path(self) -> Optional[str]:
        """Get PowerPoint template path"""
        template_path = os.path.join(
            self.project_root, "CaseStudy1Resources", "Inspection Plan Template.pptx"
        )
        
        if not os.path.exists(template_path):
            self._log(f"❌ Template not found: {template_path}")
            return None
        
        return template_path
    
    def filter_equipment_data(self, equipment_numbers: List[str], equipment_map: Dict[str, Equipment]) -> dict:
        """Filter equipment data based on selection"""
        filtered_equipment = {}
        
        for eq_no in equipment_numbers:
            if eq_no in equipment_map:
                filtered_equipment[eq_no] = equipment_map[eq_no]
        
        if not filtered_equipment:
            self._log("❌ No equipment to export")
            return {}
        
        # Log V-001 status
        if "V-001" in filtered_equipment:
            self._log("⚠️ Note: V-001 is already in Slide 0 (template slide)")
            self._log("   Will assign V-002 to Slide 1, V-003 to Slide 2, etc.")
        
        self._log(f"📊 Preparing {len(filtered_equipment)} equipment for PowerPoint")
        return filtered_equipment
    
    def generate_powerpoint(self, equipment_data: dict, output_path: str) -> bool:
        """Generate PowerPoint file"""
        try:
            template_path = self.get_template_path()
            if not template_path:
                return False
            
            generator = PowerPointGenerator(
                template_path=template_path,
                log_callback=self._log
            )
            
            self._log(f"🔄 Generating PowerPoint with {len(equipment_data)} equipment...")
            return generator.generate_from_equipment_map(equipment_data, output_path)
            
        except FileNotFoundError as e:
            self._log(f"❌ Template error: {e}")
            return False
        except Exception as e:
            self._log(f"❌ PowerPoint generation error: {e}")
            return False
    
    def get_default_filename(self) -> str:
        """Get default filename for PowerPoint export"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return f"Inspection_Plan_{timestamp}.pptx"
    
    def _log(self, message: str) -> None:
        """Log a message using the callback"""
        if self.log_callback:
            self.log_callback(message)