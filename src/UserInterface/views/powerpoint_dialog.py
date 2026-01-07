# File: ui/powerpoint_dialog.py
"""
PowerPoint Export Dialog - UI for equipment selection
"""
import customtkinter as ctk
from tkinter import messagebox
import time
from typing import List, Dict, Callable

from models import Equipment


class PowerPointExportDialog:
    """Dialog for selecting equipment for PowerPoint export"""
    
    def __init__(self, 
                 parent, 
                 equipment_map: Dict[str, Equipment],
                 on_export: Callable[[List[str], str], None],
                 on_cancel: Callable[[], None]):
        self.parent = parent
        self.equipment_map = equipment_map
        self.on_export = on_export
        self.on_cancel = on_cancel
        
        self.dialog = None
        self.equipment_vars = {}
        self.filename_var = None
        
    def show(self) -> None:
        """Show the dialog"""
        if not self.equipment_map:
            messagebox.showwarning("No Data", "No equipment data available.")
            return
        
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Export to PowerPoint")
        self.dialog.geometry("500x600")
        self.dialog.grab_set()
        self.dialog.transient(self.parent)
        self.dialog.focus_set()
        
        self._setup_ui()
        self._center_dialog()
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        # Main frame
        main_frame = ctk.CTkFrame(self.dialog, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        self._create_title(main_frame)
        
        # Equipment selection
        self._create_selection_section(main_frame)
        
        # Filename
        self._create_filename_section(main_frame)
        
        # Information
        self._create_info_section(main_frame)
        
        # Buttons
        self._create_button_section(main_frame)
    
    def _create_title(self, parent) -> None:
        """Create dialog title"""
        title = ctk.CTkLabel(
            parent,
            text="Export to PowerPoint",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=(10, 5))
    
    def _create_selection_section(self, parent) -> None:
        """Create equipment selection section"""
        # Label
        select_label = ctk.CTkLabel(
            parent,
            text="Select equipment to export:",
            font=("Segoe UI", 11)
        )
        select_label.pack(pady=(10, 5))
        
        # Scrollable frame with checkboxes
        scroll_frame = ctk.CTkScrollableFrame(parent, height=250)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create checkboxes
        self._create_equipment_checkboxes(scroll_frame)
        
        # Selection buttons
        self._create_selection_buttons(parent)
    
    def _create_equipment_checkboxes(self, parent) -> None:
        """Create equipment checkboxes"""
        self.equipment_vars = {}
        for eq_no, equipment in self.equipment_map.items():
            var = ctk.BooleanVar(value=True)
            self.equipment_vars[eq_no] = var
            
            # Format display text
            description = equipment.equipment_description
            if len(description) > 40:
                description = description[:37] + "..."
            
            cb = ctk.CTkCheckBox(
                parent,
                text=f"{equipment.equipment_number}: {description}",
                variable=var,
                font=("Segoe UI", 10)
            )
            cb.pack(anchor="w", padx=5, pady=2)
    
    def _create_selection_buttons(self, parent) -> None:
        """Create select all/none buttons"""
        select_frame = ctk.CTkFrame(parent, fg_color="transparent")
        select_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            select_frame,
            text="Select All",
            command=self._select_all,
            width=80,
            height=24,
            font=("Segoe UI", 9)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            select_frame,
            text="Select None",
            command=self._select_none,
            width=80,
            height=24,
            font=("Segoe UI", 9)
        ).pack(side="left", padx=5)
    
    def _create_filename_section(self, parent) -> None:
        """Create filename input section"""
        filename_frame = ctk.CTkFrame(parent, fg_color="transparent")
        filename_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            filename_frame,
            text="Filename:",
            font=("Segoe UI", 11)
        ).pack(side="left", padx=5)
        
        default_name = f"Inspection_Plan_{time.strftime('%Y%m%d_%H%M%S')}.pptx"
        self.filename_var = ctk.StringVar(value=default_name)
        
        filename_entry = ctk.CTkEntry(
            filename_frame,
            textvariable=self.filename_var,
            width=200
        )
        filename_entry.pack(side="left", padx=5)
    
    def _create_info_section(self, parent) -> None:
        """Create information section"""
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = (
            "ℹ️ Note: V-001 is already in Slide 0 (template).\n"
            "Selected equipment will fill Slides 1-9."
        )
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=("Segoe UI", 9),
            text_color=("gray50", "gray70"),
            justify="left"
        ).pack(anchor="w", padx=5)
    
    def _create_button_section(self, parent) -> None:
        """Create action buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=100,
            height=32,
            font=("Segoe UI", 10)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Generate PowerPoint",
            command=self._on_export,
            width=150,
            height=32,
            font=("Segoe UI", 11, "bold")
        ).pack(side="right", padx=5)
    
    def _select_all(self) -> None:
        """Select all equipment"""
        for var in self.equipment_vars.values():
            var.set(True)
    
    def _select_none(self) -> None:
        """Deselect all equipment"""
        for var in self.equipment_vars.values():
            var.set(False)
    
    def _safe_destroy(self) -> None:
        """Safely destroy the dialog"""
        try:
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.destroy()
        except:
            pass

    def _on_export(self) -> None:
        """Handle export button click"""
        selected_equipment = self._get_selected_equipment()
        
        if not selected_equipment:
            messagebox.showwarning("No Selection", "Please select at least one equipment.")
            return
        
        self._safe_destroy()
        self.on_export(selected_equipment, self.filename_var.get())
    
    def _get_selected_equipment(self) -> List[str]:
        """Get list of selected equipment numbers"""
        selected = []
        for eq_no, var in self.equipment_vars.items():
            if var.get():
                selected.append(eq_no)
        return selected
    
    def _on_cancel(self) -> None:
        """Handle cancel button click"""
        self._safe_destroy()
        self.on_cancel()
    
    def _center_dialog(self) -> None:
        """Center dialog on screen"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')