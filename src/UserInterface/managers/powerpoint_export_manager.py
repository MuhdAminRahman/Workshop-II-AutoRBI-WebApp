# File: managers/powerpoint_export_manager.py
"""
PowerPoint Export Manager - Coordinates PowerPoint export operations
"""
from typing import List, Callable
from tkinter import messagebox

from UserInterface.services.powerpoint_service import PowerPointExportService
from UserInterface.views.powerpoint_dialog import PowerPointExportDialog


class PowerPointExportManager:
    """Manager for coordinating PowerPoint export operations"""
    
    def __init__(self, 
                 project_root: str,
                 state,
                 controller,
                 executor,
                 log_callback: Callable[[str], None],
                 parent_window):
        self.project_root = project_root
        self.state = state
        self.controller = controller
        self.executor = executor
        self.log_callback = log_callback
        self.parent_window = parent_window  # Store parent window reference
        
        self.service = PowerPointExportService(project_root, log_callback)
    
    def export_to_powerpoint(self) -> None:
        """Main entry point for PowerPoint export"""
        # Validate data first
        if not self._validate_data():
            return
        
        # Open export dialog
        dialog = PowerPointExportDialog(
            parent=self.parent_window,
            equipment_map=self.state.equipment_map,
            on_export=self._handle_export_request,
            on_cancel=self._handle_export_cancel
        )
        dialog.show()
    
    def _validate_data(self) -> bool:
        """Validate data before export"""
        if not self.state.has_equipment_data:
            self._safe_show_message(
                "No Data", 
                "No equipment data available.",
                "warning"
            )
            return False
        return True
    
    def _handle_export_request(self, selected_equipment: List[str], filename: str) -> None:
        """Handle export request from dialog"""
        self.log_callback(f"📊 Exporting {len(selected_equipment)} equipment to PowerPoint...")
        self.executor.submit(
            self._execute_export, 
            selected_equipment, 
            filename
        )
    
    def _handle_export_cancel(self) -> None:
        """Handle export cancellation"""
        self.log_callback("PowerPoint export cancelled")
    
    def _execute_export(self, selected_equipment: List[str], filename: str) -> None:
        """Execute PowerPoint export in background thread"""
        try:
            success = self._generate_powerpoint(selected_equipment, filename)
            if success:
                # DATABASE INTEGRATION: Log PowerPoint generation
                from AutoRBI_Database.database.session import SessionLocal
                from UserInterface.services.database_service import DatabaseService
                
                db = SessionLocal()
                try:
                    work_id = int(self.controller.current_work.get("work_id"))
                    user_id = self.controller.current_user.get("id")
                    
                    DatabaseService.log_work_history(
                        db, work_id, user_id,
                        action_type="generate_ppt",
                        description=f"Generated PowerPoint with {len(selected_equipment)} equipment"
                    )
                except Exception as e:
                    self.log_callback(f"⚠️ Could not log PPT generation: {e}")
                finally:
                    db.close()
            self.parent_window.after(0, self._show_export_result, success, len(selected_equipment))
            
        except Exception as e:
            self.log_callback(f"❌ PowerPoint export error: {e}")
            self.parent_window.after(0, self._show_export_error, str(e))
    
    def _generate_powerpoint(self, equipment_numbers: List[str], filename: str) -> bool:
        """Generate PowerPoint file"""
        # Get work ID
        work_id = self.controller.current_work.get("work_id") if self.controller.current_work else None
        work_name = self.controller.current_work.get("work_name") if self.controller.current_work else None
        
        # Validate prerequisites
        is_valid, error_msg = self.service.validate_prerequisites(
            self.state.equipment_map, 
            work_id
        )
        if not is_valid:
            self.log_callback(f"❌ {error_msg}")
            return False
        
        # Get filtered equipment data
        equipment_data = self.service.filter_equipment_data(
            equipment_numbers, 
            self.state.equipment_map
        )
        if not equipment_data:
            return False
        
        # Get output path
        output_path = self.service.get_output_path(work_name, filename)
        if not output_path:
            return False
        
        # Generate PowerPoint
        return self.service.generate_powerpoint(equipment_data, output_path)
    
    def _show_export_result(self, success: bool, equipment_count: int) -> None:
        """Show export result on main thread"""
        if success:
            self._show_success_message(equipment_count)
        else:
            self._show_error_message()
    
    def _show_success_message(self, equipment_count: int) -> None:
        """Show success message"""
        self._safe_show_message(
            "Success",
            f"PowerPoint created successfully!\n\n"
            f"Exported {equipment_count} equipment items.",
            "info"
        )
    
    def _show_error_message(self) -> None:
        """Show error message"""
        self._safe_show_message(
            "Error",
            "Failed to create PowerPoint. Check logs for details.",
            "error"
        )
    
    def _show_export_error(self, error: str) -> None:
        """Show export error message"""
        self._safe_show_message(
            "Error",
            f"Error creating PowerPoint:\n{error}",
            "error"
        )
    
    def _safe_show_message(self, title: str, message: str, msg_type: str = "info") -> None:
        """Safely show a message box from main thread"""
        def show():
            try:
                if self.parent_window.winfo_exists():
                    if msg_type == "info":
                        messagebox.showinfo(title, message)
                    elif msg_type == "error":
                        messagebox.showerror(title, message)
                    elif msg_type == "warning":
                        messagebox.showwarning(title, message)
            except Exception as e:
                # Fallback to logging
                self.log_callback(f"⚠️ Could not show message: {title}")
        
        # Schedule on main thread
        self.parent_window.after(0, show)