import os
from typing import Dict, List, Optional, Set
from tkinter import messagebox
import customtkinter as ctk

from UserInterface.services.database_service import DatabaseService
from AutoRBI_Database.database.session import SessionLocal
from data_extractor import MasterfileExtractor
from data_extractor.utils import get_equipment_number_from_image_path
from excel_manager import ExcelManager
from convert_mypdf_to_image import PDFToImageConverter
from models.equipment import Equipment

# Import refactored components
from .constants import Messages
from .page_builders import Page1Builder, Page2Builder
from .ui_updater import UIUpdateManager
from .data_table import DataTableManager
from UserInterface.managers.extraction_manager import ExtractionManager
from UserInterface.managers.state_manager import ViewState
from UserInterface.managers.powerpoint_export_manager import PowerPointExportManager
from UserInterface.services.file_service import FileService
from UserInterface.services.equipment_service import EquipmentService
from UserInterface.utils.threading_utils import SafeThreadExecutor, LoadingContext
from UserInterface.services.excel_validator import (
    ExcelValidator,
    ExcelFileInfo,
    ExcelFileType,
)
from UserInterface.services.data_validator import DataValidator, ValidationResult
from UserInterface.managers.ui_state_manager import (
    UIStateController,
    UIState,
    UIStateConfig,
)


class NewWorkView:
    """
    Main coordinator for New Work interface.

    This class is now much simpler - it delegates to specialized components:
    - FileService: File operations
    - EquipmentService: Business logic
    - ExtractionManager: Extraction coordination
    - Page1Builder/Page2Builder: UI construction
    - UIUpdateManager: Thread-safe UI updates
    - ViewState: State management
    """

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self._initialized = False
        self.is_extracting = False
        self.work_id = (
            self.controller.current_work.get("work_id")
            if self.controller.current_work
            else None
        )
        self.workpathname = (
            self.controller.current_work.get("work_name")
            if self.controller.current_work
            else None
        )

        # Initialize state
        self.state = ViewState()

        # Get project root
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        # Initialize thread executor
        self.executor = SafeThreadExecutor(max_workers=3)

        # Initialize UI update manager
        self.ui_updater = UIUpdateManager(parent, batch_interval_ms=100)
        self._register_ui_handlers()
        self.ui_updater.start()

        # initialized validators and manager
        self.excel_validator = ExcelValidator(self.project_root)
        self.data_validator = DataValidator()
        self.ui_state_controller = UIStateController()

        # Current Excel file info
        self.excel_file_info: Optional[ExcelFileInfo] = None

        # Validation state
        self.validation_result: Optional[ValidationResult] = None
        self.highlighted_entries: Set[int] = set()

        # Initialize core components
        self._initialize_converters()

        # Initialize services
        self.file_service = FileService(
            self.pdf_converter, log_callback=self.log_callback
        )
        self.excel_manager: Optional[ExcelManager] = None
        self._initialize_managers()

        self.equipment_service = EquipmentService(
            self.excel_manager, self.extractor, log_callback=self.log_callback
        )

        self.extraction_manager = ExtractionManager(
            self.equipment_service,
            self.file_service,
            self.executor,
            self.ui_updater,
            self.log_callback,
        )
        self.powerpoint_manager = PowerPointExportManager(
            project_root=self.project_root,
            state=self.state,
            controller=self.controller,
            executor=self.executor,
            log_callback=self.log_callback,
            parent_window=self.parent,  # Pass parent window reference
        )

        # Initialize UI builders (but don't build yet)
        self.page1_builder = Page1Builder(parent, self)
        self.page2_builder = Page2Builder(parent, self)

        # Page frames (built lazily)
        self.page1_frame: Optional[ctk.CTkFrame] = None
        self.page2_frame: Optional[ctk.CTkFrame] = None

        # UI references (set by builders)
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.progress_label: Optional[ctk.CTkLabel] = None
        self.extraction_log_textbox: Optional[ctk.CTkTextbox] = None
        self.next_button: Optional[ctk.CTkButton] = None
        self.file_listbox: Optional[ctk.CTkTextbox] = None
        self.work_combobox: Optional[ctk.CTkComboBox] = None
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.progress_label: Optional[ctk.CTkLabel] = None
        self.extraction_log_textbox: Optional[ctk.CTkTextbox] = None
        self.next_button: Optional[ctk.CTkButton] = None
        self.file_listbox: Optional[ctk.CTkTextbox] = None
        self.work_combobox: Optional[ctk.CTkComboBox] = None
        self.file_mode: Optional[ctk.StringVar] = None
        self.files_edit_container: Optional[ctk.CTkFrame] = None
        self.excel_upload_button: Optional[ctk.CTkButton] = None
        self.file_browse_button: Optional[ctk.CTkButton] = None
        self.file_clear_button: Optional[ctk.CTkButton] = None
        self.start_extraction_button: Optional[ctk.CTkButton] = None
        self.save_excel_button: Optional[ctk.CTkButton] = None
        self.export_ppt_button: Optional[ctk.CTkButton] = None
        self.info_label: Optional[ctk.CTkLabel] = None
        self.data_table_manager = None
    
    # =========================================================================
    # INITIALIZATION
    # =========================================================================

    def _initialize_managers(self) -> None:
        """Initialize PDF converter, Excel manager, and extractor"""
        # Excel Manager
        excel_path = self._get_work_excel_path()
        if excel_path:
            self.excel_manager = ExcelManager(
                excel_path, log_callback=self.log_callback
            )

        # Extractor
        self.extractor = MasterfileExtractor(log_callback=self.log_callback)

    def _initialize_converters(self) -> None:
        # PDF Converter
        self.pdf_converter = PDFToImageConverter()
        if self.work_id:
            self.state.converted_images_dir = os.path.join(
                self.project_root,
                "src",
                "output_files",
                self.workpathname,
                "converted_images",
            )
            self.pdf_converter.output_folder = self.state.converted_images_dir

    def _register_ui_handlers(self) -> None:
        """Register handlers for UI updates from background threads"""
        self.ui_updater.register_handler("progress", self._handle_progress_update)
        self.ui_updater.register_handler("log", self._handle_log_update)
        self.ui_updater.register_handler("enable_next", self._handle_enable_next)

    # =========================================================================
    # UI UPDATE HANDLERS (Called on main thread)
    # =========================================================================

    def _handle_progress_update(self, data: dict) -> None:
        """Handle progress updates on main thread"""
        if self.progress_bar and self.progress_bar.winfo_exists():
            self.progress_bar.set(data.get("value", 0.0))

        if self.progress_label and self.progress_label.winfo_exists():
            text = data.get("text")
            if text:
                self.progress_label.configure(text=text)

    def _handle_log_update(self, message: str) -> None:
        """Handle log updates on main thread"""
        if (
            self.state.current_page == 1
            and self.state.page_1_active
            and self.extraction_log_textbox
            and self.extraction_log_textbox.winfo_exists()
        ):

            self.extraction_log_textbox.configure(state="normal")
            self.extraction_log_textbox.insert("end", message + "\n")
            self.extraction_log_textbox.see("end")
            self.extraction_log_textbox.configure(state="disabled")

    def _handle_enable_next(self, _) -> None:
        """Enable next button"""
        if self.next_button and self.next_button.winfo_exists():
            self.next_button.configure(state="normal")

    # =========================================================================
    # LOGGING (Thread-safe)
    # =========================================================================

    def log_callback(self, message: str) -> None:
        """Thread-safe logging callback"""
        self.ui_updater.queue_update("log", message)

    # =========================================================================
    # UI STATE MANAGEMENT
    # =========================================================================

    def update_ui_state(self) -> None:
        """Update UI elements based on current state"""
        # Check permissions
        has_permission = True

        # Get work and check Excel
        if self.work_id and not self.excel_file_info:
            self.check_excel_file(self.workpathname)

        # Validate data if on page 2
        data_validated = False
        if self.state.current_page == 2:
            # Use existing validation result if available
            if self.validation_result:
                data_validated = self.validation_result.is_valid
            else:
                # If no validation result yet, mark as not validated
                data_validated = False

        # Compute UI state
        ui_config = self.ui_state_controller.compute_ui_state(
            has_permission=has_permission,
            excel_file_info=self.excel_file_info
            or ExcelFileInfo(ExcelFileType.NOT_FOUND, None, False, set(), None),
            has_files_selected=self.state.has_files,
            extraction_complete=self.state.extraction_complete,
            data_validated=data_validated,
            is_extracting=self.is_extracting,
        )

        # Apply UI configuration
        self._apply_ui_config(ui_config)

    def _apply_ui_config(self, config: UIStateConfig) -> None:
        """Apply UI configuration to widgets"""
        # Page 1 controls
        if self.work_combobox:
            state = "readonly" if config.work_selector_enabled else "disabled"
            self.work_combobox.configure(state=state)

        if self.excel_upload_button:
            if config.excel_upload_visible:
                self.excel_upload_button.pack(side="left", padx=(0, 8))
            else:
                self.excel_upload_button.pack_forget()

        if self.file_browse_button:
            state = "normal" if config.file_browse_enabled else "disabled"
            self.file_browse_button.configure(state=state)

        if self.file_clear_button:
            state = "normal" if config.file_clear_enabled else "disabled"
            self.file_clear_button.configure(state=state)

        if self.start_extraction_button:
            state = "normal" if config.start_extraction_enabled else "disabled"
            self.start_extraction_button.configure(state=state)

        if self.next_button:
            state = "normal" if config.next_button_enabled else "disabled"
            self.next_button.configure(state=state)

        # Page 2 controls
        if self.save_excel_button:
            state = "normal" if config.save_excel_enabled else "disabled"
            self.save_excel_button.configure(state=state)

        if self.export_ppt_button:
            state = "normal" if config.export_powerpoint_enabled else "disabled"
            self.export_ppt_button.configure(state=state)

        # Info message
        if self.info_label and config.info_message:
            self.info_label.configure(text=config.info_message)

        # Blocking message
        if config.show_blocking_message:
            messagebox.showwarning("Access Denied", config.info_message)

    # =========================================================================
    # UI UPDATE HANDLERS & LOGGING
    # =========================================================================

    def _register_ui_handlers(self) -> None:
        """Register handlers for UI updates from background threads"""
        self.ui_updater.register_handler("progress", self._handle_progress_update)
        self.ui_updater.register_handler("log", self._handle_log_update)
        self.ui_updater.register_handler("enable_next", self._handle_enable_next)

    def _handle_progress_update(self, data: dict) -> None:
        """Handle progress updates on main thread"""
        if self.progress_bar and self.progress_bar.winfo_exists():
            self.progress_bar.set(data.get("value", 0.0))

        if self.progress_label and self.progress_label.winfo_exists():
            text = data.get("text")
            if text:
                self.progress_label.configure(text=text)

    def _handle_log_update(self, message: str) -> None:
        """Handle log updates on main thread"""
        if (
            self.state.current_page == 1
            and self.state.page_1_active
            and self.extraction_log_textbox
            and self.extraction_log_textbox.winfo_exists()
        ):

            self.extraction_log_textbox.configure(state="normal")
            self.extraction_log_textbox.insert("end", message + "\n")
            self.extraction_log_textbox.see("end")
            self.extraction_log_textbox.configure(state="disabled")

    def _handle_enable_next(self, _) -> None:
        """Enable next button"""
        if self.next_button and self.next_button.winfo_exists():
            self.next_button.configure(state="normal")

    def log_callback(self, message: str) -> None:
        """Thread-safe logging callback"""
        self.ui_updater.queue_update("log", message)

    # =========================================================================
    # PAGE NAVIGATION
    # =========================================================================
    def _clear_parent(self) -> None:
        for widget in self.parent.winfo_children():
            widget.destroy()

    def setInitialized(self, value: bool) -> None:
        self._initialized = value

    def show(self) -> None:
        """Entry point - show Page 1"""
        if not self._initialized:
            self._clear_parent()
            self.setInitialized(True)

        self.show_page_1()

    def show_page_1(self) -> None:
        """Show Page 1 - Upload & Extract"""
        self.state.current_page = 1
        self.state.page_1_active = True
        self.state.page_2_active = False

        # Build page if not built yet
        if self.page1_frame is None:
            self.page1_frame = self.page1_builder.build()

        # Hide page 2 if shown
        if self.page2_frame is not None:
            self.page2_frame.pack_forget()

        # Show page 1 (only if it exists)
        if self.page1_frame.winfo_exists():
            self.page1_frame.pack(expand=True, fill="both")
        else:
            # Recreate if destroyed
            self.page1_frame = self.page1_builder.build()
            self.page1_frame.pack(expand=True, fill="both")

        # Refresh and update UI state
        self.refresh_file_list()
        self.update_ui_state()

    def show_page_2(self) -> None:
        """Show Page 2 - Review & Save"""
        if not self.state.can_proceed_to_page_2:
            messagebox.showwarning(
                "Cannot Proceed",
                "Please complete extraction before proceeding to review.",
            )
            return

        self.state.current_page = 2
        self.state.page_1_active = False
        self.state.page_2_active = True

        # Build page if not built yet
        if self.page2_frame is None:
            self.page2_frame = self.page2_builder.build()

        # Hide page 1
        if self.page1_frame is not None:
            self.page1_frame.pack_forget()

        # Show page 2
        self.page2_frame.pack(expand=True, fill="both")
        
        # Clear any existing content in files_edit_container
        if hasattr(self, 'files_edit_container') and self.files_edit_container:
            for child in self.files_edit_container.winfo_children():
                child.destroy()
        
        # Rebuild data tables
        self.rebuild_data_tables()
        
        # Validate data
        self.validate_data()
        self.update_ui_state()

    # =========================================================================
    # FILE OPERATIONS (Delegates to FileService)
    # =========================================================================

    def select_files(self, mode: str = "single") -> None:
        """Select files with validation"""
        # Check if we can upload files
        if not self._can_upload_files():
            return

        selected = self.file_service.select_files(mode)

        if selected:
            # Convert PDFs to images
            converted = self.file_service.convert_pdfs_to_images(
                selected, self.state.converted_images_dir
            )
            self.state.converted_files.extend(converted)
            # Validate each equipment before adding
            valid_equipment = []
            for eq_no in converted:
                can_upload, reason = self._can_upload_equipment(eq_no)

                if can_upload:
                    valid_equipment.append(eq_no)
                    self.log_callback(f"✅ {eq_no}: Ready to extract")
                else:
                    self.log_callback(f"⚠️ {eq_no}: {reason}")
                    messagebox.showwarning(
                        "Cannot Upload", f"Equipment {eq_no}: {reason}"
                    )

            # Add valid equipment to state
            for eq_no in valid_equipment:
                self.state.add_file(eq_no)

            if valid_equipment:
                self.log_callback(
                    f"📁 Added {len(valid_equipment)} file(s) for extraction"
                )

                # DATABASE INTEGRATION: Log PDF upload
                db = SessionLocal()
                try:
                    work_id = int(self.controller.current_work.get("work_id"))
                    user_id = self.controller.current_user.get("id")

                    DatabaseService.log_work_history(
                        db,
                        work_id,
                        user_id,
                        action_type="upload_pdf",
                        description=f"Uploaded {len(valid_equipment)} GA drawing(s) with the name: {', '.join(valid_equipment)}",
                    )
                except Exception as e:
                    self.log_callback(f"⚠️ Could not log upload: {e}")
                finally:
                    db.close()

            self.refresh_file_list()
            self.update_ui_state()

    def _can_upload_files(self) -> bool:
        """Check if files can be uploaded"""
        # Must have Excel file
        if (
            not self.excel_file_info
            or self.excel_file_info.file_type == ExcelFileType.NOT_FOUND
        ):
            messagebox.showwarning(
                "No Excel File",
                "Please upload the default Excel masterfile before selecting GA drawings.",
            )
            return False

        # Cannot upload if extraction is complete (must start over)
        if self.state.extraction_complete:
            messagebox.showwarning(
                "Extraction Complete",
                "Extraction is already complete. Please proceed to review or start a new work.",
            )
            return False

        return True

    def _can_upload_equipment(self, equipment_number: str) -> tuple[bool, str]:
        """Check if specific equipment can be uploaded"""
        if not self.excel_file_info:
            return False, "No Excel file loaded"

        # Check if work already done for this equipment
        can_upload, reason = self.excel_validator.can_upload_equipment(
            self.excel_file_info, equipment_number
        )

        return can_upload, reason

    def clear_files(self) -> None:
        """Clear selected files"""
        self.state.clear_files()
        self.refresh_file_list()

    def refresh_file_list(self) -> None:
        """Refresh the file list display"""
        if not hasattr(self, "file_listbox") or self.file_listbox is None:
            return

        self.file_listbox.configure(state="normal")
        self.file_listbox.delete("1.0", "end")

        # Show Excel status
        if self.work_id:
            excel_path = self._get_work_excel_path()
            if excel_path:
                excel_filename = os.path.basename(excel_path)
                self.file_listbox.insert("end", f"[MASTERFILE] 📋 {excel_filename}\n")
            else:
                self.file_listbox.insert("end", "[MASTERFILE] ⚠️ No Excel uploaded\n")

        # Show GA files
        if self.state.selected_files:
            self.file_listbox.insert("end", "\n[GA DRAWINGS]\n")
            for idx, file_path in enumerate(self.state.selected_files, start=1):
                filename = os.path.basename(file_path)
                self.file_listbox.insert("end", f"  {idx}. 📄 {filename}\n")
        else:
            self.file_listbox.insert("end", "\n[GA DRAWINGS] No files selected\n")

        self.file_listbox.configure(state="disabled")

    # =========================================================================
    # EXTRACTION (Delegates to ExtractionManager)
    # =========================================================================

    def start_extraction(self) -> None:
        """Start extraction with validation"""
        # Validate prerequisites
        if not self.state.has_files:
            messagebox.showwarning("No Files", "Please select GA drawing files first.")
            return

        if not self.excel_manager:
            messagebox.showerror("No Excel", "Excel masterfile not loaded.")
            return

        if self.state.extraction_complete:
            messagebox.showwarning(
                "Already Complete",
                "Extraction is already complete. Please proceed to review.",
            )
            return

        # Set extracting flag
        self.is_extracting = True
        self.update_ui_state()

        # Run extraction
        with LoadingContext(
            self.controller, "Starting extraction...", show_progress=True
        ):
            self.executor.submit(self._run_extraction)

    def _run_extraction(self) -> None:
        """Run extraction in background thread"""
        try:
            # Run extraction
            updated_map = self.extraction_manager.run_extraction(
                self.state.selected_files, self.state.converted_images_dir
            )

            # Update state
            self.state.equipment_map = updated_map

            # Store per-file data
            for file_path in self.state.selected_files:
                if file_path in updated_map:
                    self.state.set_equipment_data(
                        file_path, {file_path: updated_map[file_path]}
                    )

            # Mark complete
            self.state.extraction_complete = True
            self.is_extracting = False
            
            # DATABASE INTEGRATION: Save extracted equipment to database
            total_equipment = len(self.state.converted_files)  # Total equipment to process
            
            if total_equipment > 0:  # Only proceed if there are equipment files
                db = SessionLocal()
                try:
                    work_id = int(self.controller.current_work.get("work_id"))
                    user_id = self.controller.current_user.get("id")

                    # Build drawing paths dictionary
                    drawing_paths = {}
                    for file_path in self.state.converted_files:
                        equipment_number = get_equipment_number_from_image_path(file_path)
                        drawing_paths[equipment_number] = file_path

                    # Filter only extracted equipment (those with updated data)
                    extracted_map = {k: v for k, v in updated_map.items() if k in self.state.converted_files}
                    extracted_count = len(extracted_map)

                    # Batch save equipment (only those successfully extracted)
                    if extracted_count > 0:
                        success, failures = DatabaseService.batch_save_equipment(
                            db, work_id, user_id, extracted_map, drawing_paths
                        )

                        self.log_callback(
                            f"💾 Saved {success}/{extracted_count} extracted equipment to database "
                            f"({extracted_count}/{total_equipment} equipment extracted)"
                        )
                        if failures > 0:
                            self.log_callback(f"⚠️ Failed to save {failures} equipment")

                        # Log extraction action to work history
                        DatabaseService.log_work_history(
                            db,
                            work_id,
                            user_id,
                            action_type="extract",
                            description=f"Extracted {extracted_count}/{total_equipment} equipment items ({success} saved successfully)",
                        )
                        
                        # Log individual equipment extraction (only for successfully saved items)
                        for equipment in extracted_map.values():
                            equipment_id = DatabaseService.get_equipment_id_by_equipment_number(
                                db, work_id, equipment.equipment_number
                            )
                            if equipment_id:  # Only log if equipment was saved
                                DatabaseService.log_work_history(
                                    db,
                                    work_id,
                                    user_id,
                                    action_type="extract_equipment",
                                    equipment_id=equipment_id,
                                    description=f"Extracted data for equipment {equipment.equipment_number}",
                                )
                    else:
                        self.log_callback(f"⚠️ No equipment data extracted from {total_equipment} files")

                except Exception as e:
                    self.log_callback(f"⚠️ Database save error: {e}")
                finally:
                    db.close()
            else:
                self.log_callback("ℹ️ No equipment files to process")
            
            # Update UI state
            self.parent.after(0, self.update_ui_state)

            # Show notification
            if hasattr(self.controller, "show_notification"):
                total_files = len(self.state.selected_files)
                extracted_count = len([k for k in updated_map.keys() if k in self.state.converted_files])
                
                if extracted_count > 0:
                    message = f"Successfully extracted {extracted_count}/{total_equipment} equipment from {total_files} file(s)!"
                    msg_type = "success"
                elif total_equipment > 0:
                    message = f"Processed {total_equipment} equipment file(s) but no data was extracted"
                    msg_type = "warning"
                else:
                    message = f"Processed {total_files} file(s)"
                    msg_type = "info"
                
                self.parent.after(
                    100,
                    lambda: self.controller.show_notification(message, msg_type, 5000),
                )

        except Exception as e:
            self.is_extracting = False
            self.log_callback(f"❌ Extraction error: {e}")
            self.parent.after(0, self.update_ui_state)
            self.parent.after(
                0,
                lambda: messagebox.showerror(
                    "Extraction Error", f"Error during extraction:\n{e}"
                ),
            )

    # =========================================================================
    # PAGE 2 DATA VALIDATION
    # =========================================================================

    def validate_data(self) -> ValidationResult:
        """Validate all data on Page 2 using DataTableManager"""
        if not self.data_table_manager:
            # No tables to validate yet
            self.validation_result = ValidationResult(
                is_valid=False,
                empty_cells=[],
                format_errors=[],
                error_message="No data tables found",
                error_widgets=[]
            )
            self.state.can_save = False
            return self.validation_result
        
        # Use the new DataValidator with format checking
        self.validation_result = self.data_validator.validate_and_highlight(data_table_manager=self.data_table_manager)
        
        if self.validation_result.has_errors:
            self.log_callback(
                f"⚠️ Found {self.validation_result.total_errors} error(s): "
                f"{len(self.validation_result.empty_cells)} missing, "
                f"{len(self.validation_result.format_errors)} format errors"
            )
        else:
            self.log_callback("✅ All fields are valid")
        
        self.state.can_save = self.validation_result.is_valid
        
        return self.validation_result

    def _highlight_empty_cells(self) -> None:
        """Highlight empty required cells in red - Updated for DataTableManager"""
        if not self.validation_result or not self.validation_result.has_empty_cells:
            return
        
        # Use the new validator's highlighting method
        # (The highlighting is already done in validate_and_highlight)
        pass

    def _clear_highlights(self) -> None:
        """Clear all cell highlights - Updated for DataTableManager"""
        if self.data_table_manager:
            self.data_validator.clear_highlights(self.data_table_manager)
    # =========================================================================
    # DATA MANAGEMENT
    # =========================================================================

    def rebuild_data_tables(self) -> None:
        """Rebuild data tables on Page 2 using DataTableManager"""
        if not hasattr(self, 'files_edit_container') or self.files_edit_container is None:
            return

        # Clear existing
        for child in self.files_edit_container.winfo_children():
            child.destroy()
        
        # Initialize DataTableManager
        self.data_table_manager = DataTableManager(self.files_edit_container, self.state.equipment_map)
        self.data_table_manager.set_data_change_callback(self._on_table_data_change)
        
        if not self.state.selected_files:
            info = ctk.CTkLabel(
                self.files_edit_container,
                text="No files processed.",
                font=("Segoe UI", 11),
            )
            info.pack(pady=20)
            return

        # Build table for each file
        from .constants import TableColumns
        
        for file_path in self.state.selected_files:
            # Prepare equipment data for this file
            table_data = self._prepare_table_data_for_file(file_path)
            
            if table_data:
                # Create table section
                self.data_table_manager.create_section(
                    file_path,
                    TableColumns.COLUMNS,
                    table_data
                )
    
    def _prepare_table_data_for_file(self, file_path: str) -> List[Dict]:
        """Prepare equipment data for table display"""
        table_data = []
        equipment_data = self.state.get_equipment_for_file(file_path)

        if not equipment_data:
            return table_data
        
        # Convert equipment data to table rows
        for equipment in equipment_data.values():
            for component in equipment.components:
                row_data = {
                    'equipment_number': equipment.equipment_number,
                    'pmt_number': equipment.pmt_number,
                    'equipment_description': equipment.equipment_description,
                    'component_name': component.component_name,
                    'phase': component.phase,
                    'fluid': component.get_existing_data_value('fluid') or '',
                    'material_type': component.get_existing_data_value('material_type') or '',
                    'spec': component.get_existing_data_value('spec') or '',
                    'grade': component.get_existing_data_value('grade') or '',
                    'insulation': component.get_existing_data_value('insulation') or '',
                    'design_temp': component.get_existing_data_value('design_temp') or '',
                    'design_pressure': component.get_existing_data_value('design_pressure') or '',
                    'operating_temp': component.get_existing_data_value('operating_temp') or '',
                    'operating_pressure': component.get_existing_data_value('operating_pressure') or '',
                }
                table_data.append(row_data)
        
        return table_data

    def _on_table_data_change(self, equipment_no: str, 
                         component_name: str, data: Dict[str, str]):
        """Handle data change from table"""
        # Update equipment map immediately
        if equipment_no in self.state.equipment_map:
            equipment = self.state.equipment_map[equipment_no]
            component = equipment.get_component(component_name)
            if component:
                # Update component data
                for field, value in data.items():
                    if value:  # Only update non-empty values
                        component.existing_data[field] = value
                print(f"Updated {equipment_no}/{component_name}: {data}")
    
    # =========================================================================
    # EXCEL FILE MANAGEMENT
    # =========================================================================

    def check_excel_file(self, workpathname: str) -> ExcelFileInfo:
        """Check Excel file status for a work"""
        self.excel_file_info = self.excel_validator.get_excel_file_info(workpathname)

        # Log status
        if self.excel_file_info.file_type == ExcelFileType.NOT_FOUND:
            self.log_callback("📋 No Excel file found for this work")
        elif self.excel_file_info.file_type == ExcelFileType.DEFAULT:
            self.log_callback("📋 Default Excel file found (no work done yet)")
        elif self.excel_file_info.file_type == ExcelFileType.UPDATED:
            self.log_callback(
                f"📋 Updated Excel file found ({len(self.excel_file_info.equipment_with_work)} equipment with work)"
            )

        # Initialize Excel manager if file exists
        if self.excel_file_info.file_path:
            self.excel_manager = ExcelManager(
                self.excel_file_info.file_path, log_callback=self.log_callback
            )
            # Update equipment service
            self.equipment_service.excel_manager = self.excel_manager

        return self.excel_file_info

    def upload_default_excel(self) -> bool:
        """Upload default Excel file for a work"""
        from tkinter import filedialog
        import shutil

        filetypes = [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        path = filedialog.askopenfilename(
            title=f"Select Default Excel Masterfile for {self.workpathname}",
            filetypes=filetypes,
        )

        if not path:
            return False

        try:
            # Save to default location
            dest_dir = os.path.join(
                self.project_root,
                "src",
                "output_files",
                self.workpathname,
                "excel",
                "default",
            )
            os.makedirs(dest_dir, exist_ok=True)
            dest_file = os.path.join(dest_dir, os.path.basename(path))
            shutil.copy2(path, dest_file)

            self.log_callback(f"✅ Default Excel uploaded: {os.path.basename(path)}")

            # Re-check Excel file status
            self.check_excel_file(self.workpathname)

            # Refresh UI
            self.update_ui_state()

            messagebox.showinfo("Success", "Default Excel file uploaded successfully!")
            return True

        except Exception as e:
            self.log_callback(f"❌ Error uploading Excel: {e}")
            messagebox.showerror("Upload Failed", f"Failed to upload Excel file:\n{e}")
            return False

    # =========================================================================
    # SAVE TO EXCEL (Delegates to EquipmentService)
    # =========================================================================

    def save_to_excel(self) -> None:
        """Save with validation using DataTableManager"""
        # Validate data first (includes format checking)
        validation = self.validate_data()

        if not validation.is_valid:
            # Show detailed error message
            error_details = []
            if validation.empty_cells:
                error_details.append(f"{len(validation.empty_cells)} missing required fields")
            if validation.format_errors:
                error_details.append(f"{len(validation.format_errors)} format errors")
            
            error_msg = f"Found {validation.total_errors} error(s): {', '.join(error_details)}\n\n"
            error_msg += validation.error_message
            
            messagebox.showerror(
                "Validation Failed",
                error_msg + "\n\nErrors are highlighted:\n• Red: Missing required fields\n• Yellow: Format errors"
            )
            return
        # Collect data from tables (this updates the state)
        updated_equipment = self.collect_data_from_tables()
        
        if not updated_equipment:
            messagebox.showinfo("No Data", "No equipment data found in UI.")
            return
        
        # Update the state with UI values
        for eq_no, equipment in updated_equipment.items():
            self.state.equipment_map[eq_no] = equipment
        
        print(f"DEBUG: Updated state with {len(self.state.equipment_map)} equipment items")
        
        # Save to Excel file
        with LoadingContext(self.controller, "Saving changes...", show_progress=True) as loading:
            loading.update_progress(0.5, f"Saving {len(updated_equipment)} equipment items...")
            
            # Save Excel in main thread (to avoid file locking issues)
            success = self.equipment_service.save_equipment_data(
                self.state.equipment_map, 
                self.workpathname
            )
            
            if success:
                # Save to database in background thread
                self.executor.submit(self._run_save)
            else:
                # If Excel save failed
                self.parent.after(0, lambda: messagebox.showerror(
                    "Save Failed",
                    Messages.SAVE_FAILED
                ))
    
    def collect_data_from_tables(self) -> Dict[str, Equipment]:
        """Collect all data from tables and return equipment dictionary"""
        if not self.data_table_manager:
            print("DEBUG: No data_table_manager!")
            return {}
        
        # Get all equipment directly from the table manager
        equipment_dict = self.data_table_manager.get_all_equipment()
        print(f"DEBUG: Collected {len(self.state.converted_files)} equipment items")
        
        # Debug output
        equipment_to_debug = set()
        for file_path in self.state.converted_files:
            eq_no = get_equipment_number_from_image_path(file_path)
            equipment_to_debug.add(eq_no)
        for eq_no in equipment_to_debug:
            if eq_no in equipment_dict:
                equipment = equipment_dict[eq_no]
                print(f"DEBUG: Equipment {eq_no} has {len(equipment.components)} components")
                for comp in equipment.components:
                    print(f"  - Component {comp.component_name}: {comp.existing_data}")
            else:
                print(f"DEBUG: Equipment {eq_no} not found in collected data")
        return equipment_dict
    
    def _run_save(self,) -> None:
        """Run save in background thread"""
        try:
            # Get total equipment count from converted files
            total_equipment = len(self.state.converted_files) if hasattr(self.state, 'converted_files') else len(self.state.equipment_map)
            
            if total_equipment > 0:
                db = SessionLocal()
                try:
                    work_id = int(self.controller.current_work.get("work_id"))
                    user_id = self.controller.current_user.get("id")
                    
                    total_equipment_saved = 0
                    total_components_saved = 0
                    failed_equipment = 0
                    
                    # Get equipment numbers from converted files
                    equipment_to_process = set()
                    if hasattr(self.state, 'converted_files'):
                        for file_path in self.state.converted_files:
                            eq_no = get_equipment_number_from_image_path(file_path)
                            equipment_to_process.add(eq_no)
                    else:
                        # Fallback to all equipment in map
                        equipment_to_process = set(self.state.equipment_map.keys())
                    
                    # Process only equipment from converted files
                    for eq_no in equipment_to_process:
                        if eq_no not in self.state.equipment_map:
                            self.log_callback(f"⚠️ Equipment {eq_no} not found in equipment map, skipping")
                            failed_equipment += 1
                            continue
                        
                        ui_equipment = self.state.equipment_map[eq_no]
                        
                        # Get equipment from database (check if exists)
                        db_equipment = DatabaseService.get_equipment_by_work_and_number(
                            db, work_id, eq_no
                        )
                        
                        if db_equipment:
                            # Compare with database original and update
                            print(f"\nDEBUG: Updating existing equipment: {eq_no}")
                            
                            # Get drawing path if available
                            drawing_path = ""
                            if hasattr(self.state, 'converted_files'):
                                for file_path in self.state.converted_files:
                                    if get_equipment_number_from_image_path(file_path) == eq_no:
                                        drawing_path = file_path
                                        break
                            
                            # Save/update equipment with its components
                            result = DatabaseService.save_equipment_with_components(
                                db, work_id, user_id, ui_equipment, drawing_path
                            )
                            
                            if result:
                                # Count corrections (calculate fields changed)
                                corrections_count = 0
                                # You could implement logic here to count specific corrections
                                
                                if corrections_count > 0:
                                    # Log correction (simplified - count all fields as potential corrections)
                                    total_fields = len(ui_equipment.components) * 9  # Approx 9 fields per component
                                    DatabaseService.log_correction(
                                        db, db_equipment.equipment_id, user_id,
                                        total_fields, corrections_count
                                    )
                                
                                total_equipment_saved += 1
                                total_components_saved += len(ui_equipment.components)
                            else:
                                print(f"WARNING: Failed to update equipment {eq_no}")
                                failed_equipment += 1
                        
                        else:
                            # Equipment doesn't exist in database - create it
                            print(f"\nDEBUG: Creating new equipment: {eq_no}")
                            
                            # Get drawing path if available
                            drawing_path = ""
                            if hasattr(self.state, 'converted_files'):
                                for file_path in self.state.converted_files:
                                    if get_equipment_number_from_image_path(file_path) == eq_no:
                                        drawing_path = file_path
                                        break
                            
                            # Save new equipment with components
                            result = DatabaseService.save_equipment_with_components(
                                db, work_id, user_id, ui_equipment, drawing_path
                            )
                            
                            if result:
                                total_equipment_saved += 1
                                total_components_saved += len(ui_equipment.components)
                                
                                # Get the newly created equipment ID
                                new_equipment_id = DatabaseService.get_equipment_id_by_equipment_number(
                                    db, work_id, eq_no
                                )
                                
                                if new_equipment_id:
                                    # Log creation as correction
                                    total_fields = len(ui_equipment.components) * 9
                                    DatabaseService.log_correction(
                                        db, new_equipment_id, user_id,
                                        0, total_fields  # All fields are new
                                    )
                            else:
                                print(f"WARNING: Failed to create equipment {eq_no}")
                                failed_equipment += 1
                    
                    # Log Excel generation to work history
                    if total_equipment_saved > 0:
                        DatabaseService.log_work_history(
                            db,
                            work_id,
                            user_id,
                            action_type="generate_excel",
                            description=f"Generated Excel with {total_equipment_saved}/{total_equipment} equipment and {total_components_saved} components"
                        )
                        
                        self.log_callback(
                            f"💾 Saved {total_equipment_saved}/{total_equipment} equipment "
                            f"with {total_components_saved} components to database"
                        )
                        if failed_equipment > 0:
                            self.log_callback(f"⚠️ Failed to save {failed_equipment} equipment")
                    else:
                        self.log_callback(f"⚠️ No equipment saved to database (0/{total_equipment})")
                    
                    # Commit transaction
                    db.commit()
                    
                    # Show success message with detailed info
                    if total_equipment_saved > 0:
                        message = Messages.SAVE_SUCCESS.format(total_equipment_saved)
                        if failed_equipment > 0:
                            message += f"\n\n⚠️ Failed to save {failed_equipment} equipment"
                        self.parent.after(0, lambda: messagebox.showinfo("Save Successful", message))
                    else:
                        self.parent.after(0, lambda: messagebox.showwarning(
                            "Save Warning",
                            f"No equipment were saved successfully (0/{total_equipment})"
                        ))
                    
                except Exception as e:
                    db.rollback()
                    self.log_callback(f"⚠️ Database update error: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    db.close()
            else:
                self.log_callback("ℹ️ No equipment to save")
                self.parent.after(0, lambda: messagebox.showinfo(
                    "No Data",
                    "No equipment data to save"
                ))

        except Exception as e:
            self.log_callback(f"❌ Save error: {e}")
            import traceback
            traceback.print_exc()
            self.parent.after(0, lambda: messagebox.showerror(
                "Save Error",
                f"Error saving data: {str(e)}"
            ))
    
    # =========================================================================
    # POWERPOINT EXPORT
    # =========================================================================

    def export_to_powerpoint(self) -> None:
        """Export to PowerPoint with validation"""
        print("DEBUG: Starting PowerPoint export...")
        
        # Validate data first
        validation = self.validate_data()

        if not validation.is_valid:
            messagebox.showerror(
                "Validation Failed",
                validation.error_message
                + "\n\nEmpty fields are highlighted in red."
                + "\n\nPlease fill all required fields before exporting.",
            )
            return
        
        # Collect data from tables
        updated_equipment = self.collect_data_from_tables()
        
        if updated_equipment:
            print(f"DEBUG: Updating equipment map with {len(updated_equipment)} equipment")
            # Update the state with UI values
            for eq_no, equipment in updated_equipment.items():
                self.state.equipment_map[eq_no] = equipment
                print(f"  Updated {eq_no}")
        else:
            print("DEBUG: No updated equipment collected")
            messagebox.showinfo("No Data", "No equipment data found in UI.")
            return
        
        print("DEBUG: Proceeding with PowerPoint export")
        # Proceed with export - the state now has updated values
        self.powerpoint_manager.export_to_powerpoint()

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def _get_work_excel_path(self) -> Optional[str]:
        """Get Excel path for current work"""
        if not self.work_id:
            return None

        return self.file_service.get_work_excel_path(
            self.workpathname, self.project_root
        )

    def _on_work_selected(self, choice: str) -> None:
        """Handle work selection"""
        for work in self.controller.available_works:
            if work.get("name", work.get("id")) == choice:
                self.controller.current_work = work
                break

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.ui_updater.stop()
        self.executor.shutdown(wait=False)
