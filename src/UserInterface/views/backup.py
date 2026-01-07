"""New Work view for AutoRBI application (CustomTkinter)."""

import os
from typing import List, Optional, Dict
from tkinter import filedialog, messagebox
import shutil
import threading
import time

import customtkinter as ctk
from data_extractor import MasterfileExtractor
from data_extractor.utils import get_equipment_number_from_image_path
from excel_manager import ExcelManager
from powerpoint_generator import PowerPointGenerator
from convert_mypdf_to_image import PDFToImageConverter
from models import Equipment, Component

class BackupNewWorkView:
    """Handles the New Work interface (file upload + extraction flow)."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.selected_files: List[str] = []
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.progress_label: Optional[ctk.CTkLabel] = None
        self.extraction_log_textbox: Optional[ctk.CTkTextbox] = None
        self.extracted_tabs: Optional[ctk.CTkTabview] = None
        self.file_to_textboxes: Dict[str, List[ctk.CTkTextbox]] = {}
        self.selected_excel: Optional[str] = None
        self.current_page: int = 1
        self.extraction_complete: bool = False
        self.next_button: Optional[ctk.CTkButton] = None
        self.extracted_equipment_data: Dict[str, Dict[str, Equipment]] = {}
        
        # Core processing instances
        self.excel_manager: Optional[ExcelManager] = None
        self.equipment_map: Dict[str, Equipment] = {}
        self.extractor: Optional[MasterfileExtractor] = None
        self.pdf_converter: Optional[PDFToImageConverter] = None
        self.converted_images_dir: Optional[str] = None
        
        # UI state tracking
        self._last_log_message: str = ""
        self.page_1_widgets_available: bool = False
        self.page_2_widgets_available: bool = False

    # ============================================================================
    # PUBLIC API - Progress & Logging
    # ============================================================================

    def set_progress(self, value: float, text: Optional[str] = None) -> None:
        """Update the extraction progress bar (0.0–1.0).
        Thread-safe: Can be called from any thread."""
        try:
            if self.progress_bar is not None and self.progress_bar.winfo_exists():
                self.progress_bar.set(value)
        except Exception as e:
            print(f"Progress bar update error: {e}")
            
        try:
            if text is not None and self.progress_label is not None and self.progress_label.winfo_exists():
                self.progress_label.configure(text=text)
        except Exception as e:
            print(f"Progress label update error: {e}")

    def log_callback(self, message: str) -> None:
        """Callback for logging messages from the extractor.
        CRITICAL: This is called from background threads, so we MUST schedule
        UI updates on the main thread using parent.after()."""
        if hasattr(self.parent, 'after'):
            self.parent.after(0, lambda m=message: self.append_extraction_log(m))
        else:
            print(f"LOG (no parent.after): {message}")

    def append_extraction_log(self, message: str) -> None:
        """Append a message to the extraction log textbox.
        This method should ONLY be called from the main thread."""
        try:
            if (self.current_page == 1 and 
                self.page_1_widgets_available and 
                self.extraction_log_textbox is not None and 
                hasattr(self.extraction_log_textbox, 'winfo_exists') and 
                self.extraction_log_textbox.winfo_exists()):
                
                self.extraction_log_textbox.configure(state="normal")
                self.extraction_log_textbox.insert("end", message + "\n")
                self.extraction_log_textbox.see("end")
                self.extraction_log_textbox.configure(state="disabled")
            else:
                print(f"LOG (page {self.current_page}): {message}")
        except Exception as e:
            print(f"LOG ERROR: {message}\nException: {e}")

    # ============================================================================
    # DATA MANAGEMENT
    # ============================================================================

    def set_extracted_equipment_data(self, file_path: str, equipment_list: Dict[str, Equipment]) -> None:
        """Set extracted equipment data for a file."""
        self.extracted_equipment_data[file_path] = equipment_list

    def get_work_excel_path(self, work_id: str = None) -> Optional[str]:
        """Get path to Excel file for the current/specified work."""
        if work_id is None:
            work = self.controller.current_work
            work_id = work.get("id") if work else None
        
        if not work_id:
            return None
        
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            excel_dir = os.path.join(project_root, "src", "output_files", work_id, "excel")
            if os.path.isdir(excel_dir):
                for fname in os.listdir(excel_dir):
                    if fname.lower().endswith(('.xlsx', '.xls')):
                        return os.path.join(excel_dir, fname)
            return None
        except Exception:
            return None

    def work_has_excel(self, work_id: str = None) -> bool:
        """Check if current/specified work has an Excel file."""
        return self.get_work_excel_path(work_id) is not None

    # ============================================================================
    # FILE OPERATIONS
    # ============================================================================

    def upload_excel_for_work(self, work_id: str = None) -> None:
        """Upload Excel file for current/specified work."""
        if work_id is None:
            work = self.controller.current_work
            work_id = work.get("id") if work else None
        
        if not work_id:
            messagebox.showwarning("No Work Selected", "Please select a work first.")
            return
        
        filetypes = [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        path = filedialog.askopenfilename(
            title=f"Select Excel file for {work_id}",
            filetypes=filetypes
        )
        if not path:
            return
        
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            dest_dir = os.path.join(project_root, "src", "output_files", work_id, "excel")
            os.makedirs(dest_dir, exist_ok=True)
            dest_file = os.path.join(dest_dir, os.path.basename(path))
            shutil.copy2(path, dest_file)
            
            messagebox.showinfo("Success", f"Excel file uploaded successfully for {work_id}.")
            self._refresh_file_list()
        except Exception as e:
            messagebox.showerror("Upload Failed", f"Failed to upload Excel file:\n{e}")

    def _select_files(self, mode: str = "single") -> None:
        """Open file/folder dialog to select PDF files and convert to images."""
        filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        
        try:
            if mode == "single":
                path = filedialog.askopenfilename(filetypes=filetypes)
                if path:
                    converted = self._convert_pdf_to_images([path])
                    self._add_converted_files(converted)
            elif mode == "multiple":
                paths = filedialog.askopenfilenames(filetypes=filetypes)
                if paths:
                    converted = self._convert_pdf_to_images(list(paths))
                    self._add_converted_files(converted)
            elif mode == "folder":
                folder_path = filedialog.askdirectory(title="Select folder containing PDF files")
                if folder_path:
                    pdf_files = self._find_pdf_files_in_folder(folder_path)
                    if pdf_files:
                        converted = self._convert_pdf_to_images(pdf_files)
                        self._add_converted_files(converted)
                    else:
                        messagebox.showwarning("No PDFs Found", f"No PDF files found in: {folder_path}")
        except Exception as e:
            messagebox.showerror("File Selection Error", f"Error selecting files:\n{e}")
            self.append_extraction_log(f"❌ File selection error: {e}")

    def _add_converted_files(self, converted_images: List[str]) -> None:
        """Add converted image files to selected files list."""
        if converted_images:
            for item in converted_images:
                if item not in self.selected_files:
                    self.selected_files.append(item)
            self._refresh_file_list()

    def _find_pdf_files_in_folder(self, folder_path: str) -> List[str]:
        """Find all PDF files in a folder."""
        pdf_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        return pdf_files

    def _convert_pdf_to_images(self, pdf_paths: List[str]) -> List[str]:
        """Convert PDF files to images and return equipment numbers."""
        try:
            if self.pdf_converter is None:
                self.pdf_converter = PDFToImageConverter()
                
                work_id = self.controller.current_work.get("id") if self.controller.current_work else None
                if work_id:
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                    self.converted_images_dir = os.path.join(
                        project_root, "src", "output_files", work_id, "converted_images"
                    )
                    self.pdf_converter.output_folder = self.converted_images_dir
            
            all_converted_images = []
            for pdf_path in pdf_paths:
                if not os.path.exists(pdf_path):
                    self.append_extraction_log(f"⚠️ PDF not found: {os.path.basename(pdf_path)}")
                    continue
                
                filename = os.path.basename(pdf_path)
                self.append_extraction_log(f"📄 Converting PDF to images: {filename}")
                
                image_paths = self.pdf_converter.convert_single(pdf_path)
                
                if image_paths:
                    for img_path in image_paths:
                        equip_no = get_equipment_number_from_image_path(img_path)
                        self.append_extraction_log(f"    - Generated image for Equipment No.: {equip_no}")
                        all_converted_images.append(equip_no)
                    self.append_extraction_log(f"  ✅ Created {len(image_paths)} image(s) from {filename}")
                else:
                    self.append_extraction_log(f"  ❌ Failed to convert {filename}")
            
            return all_converted_images
            
        except Exception as e:
            error_msg = f"Error converting PDFs to images: {str(e)}"
            self.append_extraction_log(f"❌ {error_msg}")
            messagebox.showerror("Conversion Error", error_msg)
            return []

    def _refresh_file_list(self) -> None:
        """Update file list display with Excel and GA files."""
        if hasattr(self, "file_listbox"):
            self.file_listbox.configure(state="normal")
            self.file_listbox.delete("1.0", "end")
            
            work_id = self.controller.current_work.get("id") if self.controller.current_work else None
            if work_id and self.work_has_excel(work_id):
                excel_path = self.get_work_excel_path(work_id)
                excel_filename = os.path.basename(excel_path) if excel_path else "Unknown"
                self.file_listbox.insert("end", f"[MASTERFILE] 📋 {excel_filename}\n")
            else:
                if work_id:
                    self.file_listbox.insert("end", "[MASTERFILE] ⚠️  No Excel uploaded\n")
            
            if self.selected_files:
                self.file_listbox.insert("end", "\n[GA DRAWINGS]\n")
                for idx, path in enumerate(self.selected_files, start=1):
                    filename = os.path.basename(path)
                    self.file_listbox.insert("end", f"  {idx}. 📄 {filename}\n")
            else:
                self.file_listbox.insert("end", "\n[GA DRAWINGS] No files selected\n")
            
            self.file_listbox.configure(state="disabled")

    def _clear_files(self) -> None:
        """Clear selected files list."""
        self.selected_files = []
        self._refresh_file_list()

    # ============================================================================
    # EXTRACTION LOGIC
    # ============================================================================

    def _start_extraction(self) -> None:
        """Entry point for starting extraction."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files first.")
            return
        
        if hasattr(self.controller, 'show_loading'):
            self.controller.show_loading("Starting extraction...", show_progress=True)
        
        self.set_progress(0.0, "Initializing extraction...")
        self._masterfile_extraction()

    def _masterfile_extraction(self) -> None:
        """Run extraction in background thread with proper error handling."""
        def extraction_thread():
            try:
                # Initialize managers
                self._initialize_extraction_managers()
                
                # Process files
                total_files = len(self.selected_files)
                for idx, equipment_number in enumerate(self.selected_files):
                    self._process_single_file(equipment_number, idx, total_files)
                
                # Finalize
                self._finalize_extraction(total_files)
                
            except Exception as e:
                error_msg = f"Extraction error: {str(e)}"
                self.parent.after(0, lambda: self.append_extraction_log(f"❌ {error_msg}"))
                self.parent.after(0, lambda: messagebox.showerror("Extraction Error", error_msg))
                if hasattr(self.controller, 'hide_loading'):
                    self.parent.after(0, self.controller.hide_loading)
        
        thread = threading.Thread(target=extraction_thread, daemon=True)
        thread.start()

    def _initialize_extraction_managers(self) -> None:
        """Initialize Excel manager and extractor."""
        if self.excel_manager is None:
            excel_path = self.get_work_excel_path()
            if not excel_path:
                raise FileNotFoundError("No Excel masterfile found. Please upload one first.")
            self.excel_manager = ExcelManager(excel_path, log_callback=self.log_callback)
        
        if self.extractor is None:
            self.extractor = MasterfileExtractor(log_callback=self.log_callback)
        
        self.equipment_map = self.excel_manager.read_masterfile()

    def _process_single_file(self, equipment_number: str, idx: int, total: int) -> None:
        """Process a single equipment file."""
        progress = (idx + 1) / total
        status = f"Processing {idx + 1}/{total}: {equipment_number}"
        
        self.parent.after(0, lambda p=progress, s=status: self.set_progress(p, s))
        self.parent.after(0, lambda: self.append_extraction_log(f"▶ Processing: {equipment_number}"))
        
        if hasattr(self.controller, 'update_loading_progress'):
            self.parent.after(0, lambda p=progress, s=status: self.controller.update_loading_progress(p, s))
        
        if equipment_number in self.equipment_map:
            # Extract and update
            self.equipment_map = self.extractor.process_and_update_single_equipment(
                self.equipment_map,
                equipment_number,
                self.converted_images_dir
            )
            
            # Store for this file
            file_specific_data = {equipment_number: self.equipment_map[equipment_number]}
            # Use actual file path as key, not equipment number
            file_path = self._get_file_path_for_equipment(equipment_number)
            self.set_extracted_equipment_data(file_path, file_specific_data)
            
            self.parent.after(0, lambda: self.append_extraction_log(f"✓ Completed: {equipment_number}"))
        else:
            self.parent.after(0, lambda: self.append_extraction_log(f"⚠️ No equipment '{equipment_number}' in masterfile"))

    def _get_file_path_for_equipment(self, equipment_number: str) -> str:
        """Get the file path that corresponds to an equipment number.
        This is a helper to maintain the mapping between files and equipment."""
        # For now, use the equipment number as the key
        # In a more complex system, this might need to track the actual file paths
        return equipment_number

    def _finalize_extraction(self, total_files: int) -> None:
        """Finalize extraction process."""
        try:
            self.parent.after(0, lambda: self.set_progress(1.0, "Extraction complete!"))
            self.parent.after(0, lambda: self.append_extraction_log("✓ All files extracted successfully."))
            self.extraction_complete = True
            self.parent.after(0, lambda: self._show_next_button())
            
            if hasattr(self.controller, 'hide_loading'):
                self.parent.after(0, self.controller.hide_loading)
            
            # Safely show notification
            if hasattr(self.controller, 'show_notification'):
                # Check if window exists before showing notification
                def safe_notification():
                    try:
                        if hasattr(self.controller, 'root') and self.controller.root.winfo_exists():
                            self.controller.show_notification(
                                f"Successfully extracted data from {total_files} file(s)!",
                                "success",
                                5000
                            )
                    except:
                        pass  # Silently fail if window is destroyed
                
                self.parent.after(100, safe_notification)
                
        except Exception as e:
            print(f"Error in finalize extraction: {e}")

    def _show_next_button(self) -> None:
        """Enable the Next button after extraction completes."""
        if self.next_button is not None:
            self.next_button.configure(state="normal")

    # ============================================================================
    # SAVE TO EXCEL
    # ============================================================================

    def _save_to_excel(self) -> None:
        """Save edited data back to Excel."""
        if not self.excel_manager:
            messagebox.showerror("No Data", "No Excel manager available. Please extract data first.")
            return
        
        if not self.equipment_map:
            messagebox.showerror("No Data", "No equipment data available. Please extract data first.")
            return
        
        if hasattr(self.controller, 'show_loading'):
            try:
                self.controller.show_loading("Checking for changes...", show_progress=True)
            except:
                print("Could not show loading")
        
        updated_equipment_map = self._update_equipment_map_from_ui()
        
        if not updated_equipment_map:
            messagebox.showinfo("No Changes", "No changes were made to the equipment data.")
            if hasattr(self.controller, 'hide_loading'):
                try:
                    self.controller.hide_loading()
                except:
                    pass
            return
        
        print(f"📊 Found changes in {len(updated_equipment_map)} equipment items")
        
        if hasattr(self.controller, 'update_loading_progress'):
            try:
                self.controller.update_loading_progress(0.5, f"Saving {len(updated_equipment_map)} equipment items...")
            except:
                pass
        
        save_thread = threading.Thread(target=self._run_save_with_dict, args=(updated_equipment_map,), daemon=True)
        save_thread.start()

    def _run_save_with_dict(self, updated_equipment_map: Dict[str, Equipment]) -> None:
        """Run the save process in a background thread."""
        try:
            print("💾 Preparing data for Excel...")
            
            user_id = self.controller.current_work.get("id")
            
            if user_id is not None:
                success = self.excel_manager.save_to_excel_with_dict(updated_equipment_map, user_id)
            else:
                success = self.excel_manager.save_to_excel_with_dict(updated_equipment_map)
            
            if success:
                print("✅ Save complete!")
                
                # Merge updated equipment back into main map
                for equip_no, updated_equipment in updated_equipment_map.items():
                    if equip_no in self.equipment_map:
                        self.equipment_map[equip_no] = updated_equipment
                
                if hasattr(self.controller, 'hide_loading'):
                    try:
                        self.parent.after(0, self.controller.hide_loading)
                    except:
                        pass
                
                self.parent.after(0, lambda: messagebox.showinfo(
                    "Save Successful",
                    f"Successfully saved {len(updated_equipment_map)} equipment items to Excel!"
                ))
                
                if (hasattr(self.controller, 'show_notification') and 
                    hasattr(self.controller, 'root') and 
                    self.controller.root.winfo_exists()):
                    try:
                        self.parent.after(0, lambda: self.controller.show_notification(
                            f"Successfully saved {len(updated_equipment_map)} equipment items to Excel!",
                            "success",
                            5000
                        ))
                    except Exception as e:
                        print(f"Could not show notification: {e}")
            else:
                error_msg = "Failed to save data to Excel"
                print(f"❌ {error_msg}")
                
                if hasattr(self.controller, 'hide_loading'):
                    try:
                        self.parent.after(0, self.controller.hide_loading)
                    except:
                        pass
                
                self.parent.after(0, lambda: messagebox.showerror("Save Failed", error_msg))
                
        except Exception as e:
            error_msg = f"Error saving data: {str(e)}"
            print(f"❌ {error_msg}")
            
            if hasattr(self.controller, 'hide_loading'):
                try:
                    self.parent.after(0, self.controller.hide_loading)
                except:
                    pass
            
            self.parent.after(0, lambda: messagebox.showerror("Save Error", error_msg))
            
            import traceback
            traceback.print_exc()

    def _update_equipment_map_from_ui(self) -> Dict[str, Equipment]:
        """Update equipment_map with data from UI entries.
        Returns only equipment that have changes."""
        if not self.equipment_map:
            return {}
        
        equipment_changed = {}
        updated_equipment_map = {}
        
        # Deep copy equipment map
        for equip_no, equipment in self.equipment_map.items():
            new_equipment = Equipment(
                equipment_number=equipment.equipment_number,
                pmt_number=equipment.pmt_number,
                equipment_description=equipment.equipment_description,
                row_index=equipment.row_index
            )
            
            for component in equipment.components:
                new_component = Component(
                    component_name=component.component_name,
                    phase=component.phase,
                    existing_data=component.existing_data.copy(),
                    row_index=component.row_index
                )
                new_equipment.add_component(new_component)
            
            updated_equipment_map[equip_no] = new_equipment
            equipment_changed[equip_no] = False

        # Update with data from UI entries
        for path, entries in self.file_to_textboxes.items():
            if not entries:
                continue
            
            num_columns = 15
            num_rows = len(entries) // num_columns
            
            for row_idx in range(num_rows):
                start_idx = row_idx * num_columns
                end_idx = start_idx + num_columns
                
                if end_idx <= len(entries):
                    row_entries = entries[start_idx:end_idx]
                    
                    equipment_no = row_entries[1].get().strip()
                    parts = row_entries[4].get().strip()
                    
                    if equipment_no and equipment_no in updated_equipment_map and parts:
                        equipment = updated_equipment_map[equipment_no]
                        
                        for component in equipment.components:
                            if component.component_name == parts:
                                changes_made = False
                                current_data = component.existing_data.copy()
                                
                                ui_updates = {
                                    'fluid': row_entries[6].get().strip(),
                                    'type': row_entries[7].get().strip(),
                                    'spec': row_entries[8].get().strip(),
                                    'grade': row_entries[9].get().strip(),
                                    'insulation': row_entries[10].get().strip(),
                                    'design_temp': row_entries[11].get().strip(),
                                    'design_pressure': row_entries[12].get().strip(),
                                    'operating_temp': row_entries[13].get().strip(),
                                    'operating_pressure': row_entries[14].get().strip(),
                                }
                                
                                existing_keys = list(current_data.keys())
                                updates = {}
                                
                                for ui_key, ui_value in ui_updates.items():
                                    if ui_value:
                                        matching_key = None
                                        for existing_key in existing_keys:
                                            if existing_key.lower() == ui_key.lower():
                                                matching_key = existing_key
                                                break
                                        
                                        if matching_key:
                                            current_value = str(current_data.get(matching_key, ''))
                                            if current_value != ui_value:
                                                updates[matching_key] = ui_value
                                                changes_made = True
                                        else:
                                            updates[ui_key] = ui_value
                                            changes_made = True
                                
                                if updates:
                                    try:
                                        component.update_existing_data(updates)
                                    except KeyError:
                                        for key, value in updates.items():
                                            component.existing_data[key] = value
                                    
                                    if changes_made:
                                        equipment_changed[equipment_no] = True
                                
                                break

        changed_count = sum(1 for changed in equipment_changed.values() if changed)
        
        if changed_count > 0:
            changed_equipment = {k: v for k, v in updated_equipment_map.items() if equipment_changed[k]}
            self._last_log_message = f"Found changes in {len(changed_equipment)} equipment items"
            print(f"📊 {self._last_log_message}")
            return changed_equipment
        else:
            self._last_log_message = "No changes detected in equipment data"
            print(f"📊 {self._last_log_message}")
            return {}

    # ============================================================================
    # PAGE DISPLAY METHODS
    # ============================================================================
    def show(self) -> None:
        """Display the New Work interface (Page 1: Upload & Extract)."""
        self.show_page_1()

    def show_page_1(self) -> None:
        """Page 1: File selection, extraction, and logs."""
        self.current_page = 1
        self.extraction_complete = False
        self.page_1_widgets_available = True
        self.page_2_widgets_available = False
        
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Outer frame with scrollable content inside
        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header with back button
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        back_btn = ctk.CTkButton(
            header,
            text="← Back to Main Menu",
            command=self.controller.show_main_menu,
            width=180,
            height=32,
            font=("Segoe UI", 10),
            fg_color="transparent",
            text_color=("gray20", "gray90"),
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        back_btn.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            header,
            text="AutoRBI",
            font=("Segoe UI", 24, "bold"),
        )
        title_label.grid(row=0, column=1, sticky="e")

        # Scrollable main content area
        scroll_container = ctk.CTkScrollableFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        scroll_container.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        main_frame = scroll_container

        main_frame.grid_rowconfigure(4, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            main_frame,
            text="New Work - Step 1: Upload & Extract",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Select work, upload Excel masterfile, and GA drawings for extraction.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        # --- Section 1: Work Selection with ComboBox -------------------------------------------
        work_section = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray15"), corner_radius=12)
        work_section.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 16))
        work_section.grid_columnconfigure(1, weight=1)

        work_label = ctk.CTkLabel(
            work_section,
            text="Work Assignment:",
            font=("Segoe UI", 11, "bold"),
            text_color=("gray20", "gray90"),
        )
        work_label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))

        # Get list of work names for ComboBox
        work_names = [w.get("name", w.get("id", "Unknown")) for w in self.controller.available_works]
        current_work_index = 0
        if self.controller.current_work:
            current_id = self.controller.current_work.get("id")
            for idx, work in enumerate(self.controller.available_works):
                if work.get("id") == current_id:
                    current_work_index = idx
                    break

        self.work_combobox = ctk.CTkComboBox(
            work_section,
            values=work_names,
            state="readonly",
            font=("Segoe UI", 10),
            height=32,
            command=lambda choice: self._on_work_selected(choice),
        )
        self.work_combobox.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=(12, 6))
        self.work_combobox.set(work_names[current_work_index] if work_names else "No Works Available")

        work_section.grid_rowconfigure(1, minsize=6)

        # --- Section 2: File Uploads (Excel + GA Drawings) -------------------------------------------
        file_upload_section = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray15"), corner_radius=12)
        file_upload_section.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 16))
        file_upload_section.grid_columnconfigure(0, weight=1)

        # File upload label
        file_upload_label = ctk.CTkLabel(
            file_upload_section,
            text="Files:",
            font=("Segoe UI", 11, "bold"),
            text_color=("gray20", "gray90"),
        )
        file_upload_label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 12))

        # Selected files display (Excel + GA drawings)
        files_display_section = ctk.CTkFrame(file_upload_section, fg_color="transparent")
        files_display_section.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        files_display_section.grid_columnconfigure(1, weight=1)

        self.file_listbox = ctk.CTkTextbox(
            files_display_section,
            height=80,
            font=("Segoe UI", 9),
            fg_color=("white", "gray20"),
        )
        self.file_listbox.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        self.file_listbox.configure(state="disabled")

        # Button row: Upload Excel, Browse GA, GA Mode, Clear
        button_row = ctk.CTkFrame(files_display_section, fg_color="transparent")
        button_row.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 0))

        # Check if Excel exists for current work
        work_id = self.controller.current_work.get("id") if self.controller.current_work else None
        excel_exists = self.work_has_excel(work_id) if work_id else False
        
        # Only show upload button if Excel doesn't exist
        if not excel_exists:
            excel_upload_btn = ctk.CTkButton(
                button_row,
                text="📋 Upload Excel",
                command=lambda: self.upload_excel_for_work(self.controller.current_work.get("id") if self.controller.current_work else None),
                height=32,
                width=120,
                font=("Segoe UI", 10),
            )
            excel_upload_btn.pack(side="left", padx=(0, 8))

        # Browse GA Files button
        ga_browse_btn = ctk.CTkButton(
            button_row,
            text="📁 Browse GA Files (PDF)",
            command=lambda: self._select_files(self.file_mode.get().lower()),
            height=32,
            width=150,
            font=("Segoe UI", 10),
        )
        ga_browse_btn.pack(side="left", padx=(0, 8))

        # File mode selector
        mode_label = ctk.CTkLabel(
            button_row,
            text="Mode:",
            font=("Segoe UI", 9),
            text_color=("gray50", "gray70"),
        )
        mode_label.pack(side="left", padx=(0, 6))

        self.file_mode = ctk.StringVar(value="single")
        mode_switch = ctk.CTkSegmentedButton(
            button_row,
            values=["Single", "Multiple", "Folder"],
            variable=self.file_mode,
            font=("Segoe UI", 9),
            height=28,
        )
        mode_switch.pack(side="left", padx=(0, 8))

        clear_btn = ctk.CTkButton(
            button_row,
            text="Clear All",
            command=self._clear_files,
            height=32,
            width=80,
            font=("Segoe UI", 10),
            fg_color="transparent",
            text_color=("gray20", "gray90"),
            hover_color=("gray85", "gray30"),
            border_width=1,
            border_color=("gray70", "gray50"),
        )
        clear_btn.pack(side="left")

        # --- Section 3: Extraction Progress & Log -------------------------------------------
        extract_section = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray15"), corner_radius=12)
        extract_section.grid(row=4, column=0, sticky="nsew", padx=24, pady=(0, 16))
        extract_section.grid_rowconfigure(2, weight=1)
        extract_section.grid_columnconfigure(0, weight=1)

        # Progress bar
        progress_label = ctk.CTkLabel(
            extract_section,
            text="Extraction Progress:",
            font=("Segoe UI", 11, "bold"),
            text_color=("gray20", "gray90"),
        )
        progress_label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        self.progress_bar = ctk.CTkProgressBar(extract_section, height=12)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        self.progress_bar.set(0.0)

        self.progress_label = ctk.CTkLabel(
            extract_section,
            text="Ready to extract.",
            font=("Segoe UI", 9),
            text_color=("gray70", "gray80"),
        )
        self.progress_label.grid(row=1, column=0, sticky="e", padx=16, pady=(0, 4))

        # Extraction log
        log_title = ctk.CTkLabel(
            extract_section,
            text="Log:",
            font=("Segoe UI", 10, "bold"),
            text_color=("gray20", "gray90"),
        )
        log_title.grid(row=2, column=0, sticky="w", padx=16, pady=(8, 4))

        self.extraction_log_textbox = ctk.CTkTextbox(
            extract_section,
            height=120,
            font=("Segoe UI", 8),
            fg_color=("white", "gray20"),
            text_color=("gray20", "gray85"),
        )
        self.extraction_log_textbox.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self.extraction_log_textbox.configure(state="disabled")

        # Start extraction button
        extract_btn = ctk.CTkButton(
            extract_section,
            text="▶ Start Extraction",
            command=self._start_extraction,
            height=36,
            font=("Segoe UI", 11, "bold"),
        )
        extract_btn.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 12))

        # --- Section 4: Bottom Action Buttons -------------------------------------------
        action_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_section.grid(row=5, column=0, sticky="ew", padx=24, pady=(12, 24))
        action_section.grid_columnconfigure(0, weight=1)

        self.next_button = ctk.CTkButton(
            action_section,
            text="➜ Next: Review Extracted Data",
            command=self.show_page_2,
            height=36,
            font=("Segoe UI", 11, "bold"),
            fg_color=("gray20", "gray30"),
            state="disabled",
        )
        self.next_button.pack(side="right")

        # Initial state for file list
        self._refresh_file_list()

    def _on_work_selected(self, choice: str) -> None:
        """Handle work selection from ComboBox."""
        for work in self.controller.available_works:
            if work.get("name", work.get("id")) == choice:
                self.controller.current_work = work
                # Refresh entire page 1 to update button visibility and file list
                self.show_page_1()
                break

    def show_page_2(self) -> None:
        """Page 2: Review and edit extracted data, then save."""
        self.current_page = 2
        self.page_1_widgets_available = False
        self.page_2_widgets_available = True
        
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Outer frame with scrollable content
        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header with back button
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        back_btn = ctk.CTkButton(
            header,
            text="← Back to Step 1",
            command=self.show_page_1,
            width=180,
            height=32,
            font=("Segoe UI", 10),
            fg_color="transparent",
            text_color=("gray20", "gray90"),
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        back_btn.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            header,
            text="AutoRBI",
            font=("Segoe UI", 24, "bold"),
        )
        title_label.grid(row=0, column=1, sticky="e")

        # Scrollable main content area
        scroll_container = ctk.CTkScrollableFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        scroll_container.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        main_frame = scroll_container

        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            main_frame,
            text="New Work - Step 2: Review & Save",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Review extracted data, edit if needed, then save to Excel and database.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        # --- Per-file editable extracted data ----------------------------------------
        data_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        data_section.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
        data_section.grid_rowconfigure(2, weight=1)
        data_section.grid_columnconfigure(0, weight=1)

        data_label = ctk.CTkLabel(
            data_section,
            text="Extracted Data (Editable):",
            font=("Segoe UI", 12, "bold"),
        )
        data_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        helper_label = ctk.CTkLabel(
            data_section,
            text="Review and edit extracted values below. They will be saved to Excel and the database.",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
        )
        helper_label.grid(row=1, column=0, sticky="w", pady=(0, 12))

        # Container that will hold per-file editable fields
        self.files_edit_container = ctk.CTkFrame(
            data_section,
            fg_color="transparent",
        )
        self.files_edit_container.grid(row=2, column=0, sticky="nsew", pady=(0, 12))
        self.files_edit_container.grid_columnconfigure(0, weight=1)
        self.files_edit_container.grid_rowconfigure(0, weight=1)

        # --- Action buttons at bottom -----------------------------------------------
        action_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_section.grid(row=3, column=0, sticky="ew", padx=24, pady=(12, 24))
        action_section.grid_columnconfigure(0, weight=1)

        save_btn = ctk.CTkButton(
            action_section,
            text="Save & Update Excel",
            command=self._save_to_excel,
            height=36,
            font=("Segoe UI", 11, "bold"),
            fg_color=("gray20", "gray30"),
        )
        save_btn.pack(side="right", padx=(8, 0))

        back_extract_btn = ctk.CTkButton(
            action_section,
            text="← Back to Extraction",
            command=self.show_page_1,
            height=36,
            font=("Segoe UI", 11),
        )
        back_extract_btn.pack(side="right")

        if hasattr(self, 'equipment_map') and self.equipment_map:
            powerpoint_btn = ctk.CTkButton(
                action_section,
                text="📊 Export to PowerPoint",
                command=self._open_powerpoint_export_dialog,
                height=36,
                font=("Segoe UI", 11),
                fg_color=("#0066CC", "#004C99"),
                hover_color=("#0052A3", "#003366")
            )
            powerpoint_btn.pack(side="right", padx=(8, 0))

        # Rebuild per-file editable sections with extracted data
        self._rebuild_extracted_data_page_2()

    def _rebuild_extracted_data_page_2(self) -> None:
        """Rebuild extracted data display as a table for Page 2 with dynamic rows."""
        # Clear old sections and mapping
        for child in self.files_edit_container.winfo_children():
            child.destroy()
        self.file_to_textboxes.clear()

        if not self.selected_files:
            info_lbl = ctk.CTkLabel(
                self.files_edit_container,
                text="No input files processed. Go back to Step 1 to select files.",
                font=("Segoe UI", 11),
                text_color=("gray50", "gray75"),
                wraplength=600,
                justify="left",
            )
            info_lbl.grid(row=0, column=0, sticky="w", padx=4, pady=4)
        else:
            # Define masterfile columns exactly as in the Excel sheet
            columns = [
                ("NO.", 40),
                ("EQUIPMENT NO.", 100),
                ("PMT NO.", 90),
                ("EQUIPMENT DESCRIPTION", 150),
                ("PARTS", 100),
                ("PHASE", 70),
                ("FLUID", 80),
                ("TYPE", 80),
                ("SPEC.", 80),
                ("GRADE", 70),
                ("INSULATION\n(yes/No)", 80),
                ("DESIGN\nTEMP. (°C)", 90),
                ("DESIGN\nPRESSURE\n(Mpa)", 90),
                ("OPERATING\nTEMP. (°C)", 90),
                ("OPERATING\nPRESSURE\n(Mpa)", 90),
            ]

            for file_idx, path in enumerate(self.selected_files, start=1):
                filename = os.path.basename(path) or f"File {file_idx}"
                
                # Extract equipment number from image filename
                equipment_number = get_equipment_number_from_image_path(path)
                
                # File section header
                file_section = ctk.CTkFrame(self.files_edit_container, fg_color="transparent")
                file_section.grid(row=file_idx - 1, column=0, sticky="ew", padx=0, pady=(12, 8))
                file_section.grid_columnconfigure(0, weight=1)

                # Show equipment number in the header if available
                if equipment_number:
                    header_text = f"📄 {filename} (Equipment: {equipment_number})"
                else:
                    header_text = f"📄 {filename}"
                
                name_label = ctk.CTkLabel(
                    file_section,
                    text=header_text,
                    font=("Segoe UI", 12, "bold"),
                )
                name_label.pack(anchor="w", pady=(0, 8))

                # Create scrollable table frame with horizontal scrolling
                table_wrapper = ctk.CTkFrame(file_section, fg_color="transparent")
                table_wrapper.pack(fill="both", expand=True)
                table_wrapper.grid_columnconfigure(0, weight=1)

                # Horizontal scrollable frame for table
                table_frame = ctk.CTkScrollableFrame(
                    table_wrapper,
                    fg_color=("gray90", "gray15"),
                    corner_radius=8,
                    height=300,
                    orientation="horizontal",
                )
                table_frame.pack(fill="both", expand=True)

                # Table header with yellow background (matching masterfile)
                header_row = ctk.CTkFrame(table_frame, fg_color=("#FFFF00", "#555500"), corner_radius=0)
                header_row.pack(fill="x", padx=0, pady=0)

                for col_name, col_width in columns:
                    header_label = ctk.CTkLabel(
                        header_row,
                        text=col_name,
                        font=("Segoe UI", 8, "bold"),
                        text_color=("black", "yellow"),
                        fg_color=("#FFFF00", "#555500"),
                        width=col_width,
                        corner_radius=0,
                    )
                    header_label.pack(side="left", padx=1, pady=1)

                # Get equipment data specifically for this file
                equipment_for_this_file = self.extracted_equipment_data.get(path, {})
            
                
                # Convert Equipment dictionary for this file to display rows
                display_rows = []
                row_counter = 0
                
                if equipment_for_this_file:
                    for equipment in equipment_for_this_file.values():
                        
                        for component in equipment.components:
                            display_rows.append({
                                'row_no': str(row_counter + 1),
                                'equipment_no': equipment.equipment_number,
                                'pmt_no': equipment.pmt_number,
                                'description': equipment.equipment_description,
                                'parts': component.component_name,
                                'phase': component.phase,
                                'fluid': component.get_existing_data_value('fluid') or '',
                                'type': component.get_existing_data_value('material_type') or '',
                                'spec': component.get_existing_data_value('spec') or '',
                                'grade': component.get_existing_data_value('grade') or '',
                                'insulation': component.get_existing_data_value('insulation') or '',
                                'design_temp': component.get_existing_data_value('design_temp') or '',
                                'design_pressure': component.get_existing_data_value('design_pressure') or '',
                                'operating_temp': component.get_existing_data_value('operating_temp') or '',
                                'operating_pressure': component.get_existing_data_value('operating_pressure') or '',
                            })
                            row_counter += 1
                else:
                    print(f"  No equipment data found for this file")
                    # No equipment found for this file
                    info_text = "No equipment data found for this file"
                    if equipment_number:
                        info_text = f"No equipment data found for '{equipment_number}'"
                    
                    info_label = ctk.CTkLabel(
                        table_frame,
                        text=info_text,
                        font=("Segoe UI", 10),
                        text_color=("gray50", "gray75"),
                    )
                    info_label.pack(pady=20)
                    continue  # Skip creating rows for this file

                print(f"  Created {len(display_rows)} display rows")
                
                # Create row for each equipment/component
                for row_data in display_rows:
                    row_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
                    row_frame.pack(fill="x", padx=0, pady=1)

                    row_entries = []

                    # Column values in order matching columns list
                    col_values = [
                        row_data.get('row_no', ''),
                        row_data.get('equipment_no', ''),
                        row_data.get('pmt_no', ''),
                        row_data.get('description', ''),
                        row_data.get('parts', ''),
                        row_data.get('phase', ''),
                        row_data.get('fluid', ''),
                        row_data.get('type', ''),
                        row_data.get('spec', ''),
                        row_data.get('grade', ''),
                        row_data.get('insulation', ''),
                        row_data.get('design_temp', ''),
                        row_data.get('design_pressure', ''),
                        row_data.get('operating_temp', ''),
                        row_data.get('operating_pressure', ''),
                    ]

                    for col_idx, (col_name, col_width) in enumerate(columns):
                        # Create editable entry field
                        entry = ctk.CTkEntry(
                            row_frame,
                            placeholder_text="",
                            font=("Segoe UI", 8),
                            width=col_width,
                            height=24,
                        )
                        entry.insert(0, col_values[col_idx])
                        entry.pack(side="left", padx=1, pady=1)
                        row_entries.append(entry)

                    # Store entries for this file path and row
                    if path not in self.file_to_textboxes:
                        self.file_to_textboxes[path] = []
                    self.file_to_textboxes[path].extend(row_entries)

    def set_extracted_text_for_file(self, file_path: str, content: str) -> None:
        """Populate the editable extracted data area for a specific file."""
        textboxes = self.file_to_textboxes.get(file_path)
        textbox = textboxes[0] if textboxes else None
        if textbox is None:
            # Fallback to match by filename only
            filename = os.path.basename(file_path)
            for path, tbs in self.file_to_textboxes.items():
                if os.path.basename(path) == filename and tbs:
                    textbox = tbs[0]
                    break
        if textbox is not None:
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", content)

    def set_extracted_text(self, content: str) -> None:
        """Populate all extracted data fields with the same content (simple case)."""
        for textboxes in self.file_to_textboxes.values():
            for textbox in textboxes:
                textbox.configure(state="normal")
                textbox.delete("1.0", "end")
                textbox.insert("1.0", content)

    def export_to_powerpoint(self, equipment_numbers: List[str] = None, 
                         filename: str = None) -> bool:
        """
        Export equipment data to PowerPoint.
        Note: V-001 is already in Slide 0 (template), so we start with V-002 on Slide 1.
        """
        
        if not hasattr(self, 'equipment_map') or not self.equipment_map:
            self.append_extraction_log("❌ No equipment data available. Extract data first.")
            return False
        
        # Get work ID
        work_id = self.controller.current_work.get("id") if self.controller.current_work else None
        if not work_id:
            self.append_extraction_log("❌ No work selected.")
            return False
        
        # Find template
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            template_path = os.path.join(project_root, "CaseStudy1Resources", "Inspection Plan Template.pptx")
            
            if not os.path.exists(template_path):
                self.append_extraction_log("❌ PowerPoint template not found")
                return False
        except Exception as e:
            self.append_extraction_log(f"❌ Error finding template: {e}")
            return False
        
        # Filter equipment if specific numbers provided
        if equipment_numbers:
            filtered_equipment = {}
            for eq_no in equipment_numbers:
                if eq_no in self.equipment_map:
                    filtered_equipment[eq_no] = self.equipment_map[eq_no]
        else:
            # Use all equipment
            filtered_equipment = self.equipment_map
        
        if not filtered_equipment:
            self.append_extraction_log("❌ No equipment to export")
            return False
        
        # Check if V-001 is in our data
        if "V-001" in filtered_equipment:
            self.append_extraction_log("⚠️ Note: V-001 is already in Slide 0 (template slide)")
            self.append_extraction_log("   Will assign V-002 to Slide 1, V-003 to Slide 2, etc.")
        
        # Generate filename
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"Inspection_Plan_{timestamp}.pptx"
        
        # Get output path
        output_path = self.get_powerpoint_output_path(work_id, filename)
        if not output_path:
            self.append_extraction_log("❌ Could not create output directory")
            return False
        
        # Create and run generator
        try:
            generator = PowerPointGenerator(
                template_path=template_path,
                log_callback=self.append_extraction_log
            )
        except FileNotFoundError as e:
            self.append_extraction_log(f"❌ {e}")
            return False
        
        equipment_count = len(filtered_equipment)
        self.append_extraction_log(f"📊 Generating PowerPoint with {equipment_count} equipment...")
        self.append_extraction_log(f"   Slide 0: Template with V-001 (already filled)")
        
        success = generator.generate_from_equipment_map(filtered_equipment, output_path)
        
        if success:
            self.append_extraction_log(f"✅ PowerPoint saved: {output_path}")
            
            # Show success message safely
            self._safe_show_message(
                "PowerPoint Created",
                f"PowerPoint successfully created!\n\n"
                f"File: {os.path.basename(output_path)}\n"
                f"Location: {os.path.dirname(output_path)}\n\n"
                f"Slide 0: Template with V-001\n"
                f"Slides 1-9: Filled with your equipment data",
                "info"
            )
        else:
            self.append_extraction_log("❌ Failed to generate PowerPoint")
            self._safe_show_message(
                "PowerPoint Error",
                "Failed to create PowerPoint. Check logs for details.",
                "error"
            )
        
        return success

    def get_powerpoint_output_path(self, work_id: str = None, filename: str = "Inspection_Plan.pptx") -> str:
        """Get PowerPoint output path for the current work."""
        if work_id is None:
            work_id = self.controller.current_work.get("id") if self.controller.current_work else None
        
        if not work_id:
            return None
        
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            ppt_dir = os.path.join(project_root, "src", "output_files", work_id, "powerpoint")
            os.makedirs(ppt_dir, exist_ok=True)
            return os.path.join(ppt_dir, filename)
        except Exception as e:
            print(f"Error creating PowerPoint directory: {e}")
            return None

    def _open_powerpoint_export_dialog(self):
        """Open a simple dialog to select equipment for PowerPoint export."""
        if not hasattr(self, 'equipment_map') or not self.equipment_map:
            messagebox.showwarning("No Data", "No equipment data available. Please extract data first.")
            return
        
        # Create dialog window
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Export to PowerPoint")
        dialog.geometry("500x600")
        dialog.grab_set()
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Export to PowerPoint",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=(10, 5))
        
        # Equipment selection
        select_label = ctk.CTkLabel(
            main_frame,
            text="Select equipment to export:",
            font=("Segoe UI", 11)
        )
        select_label.pack(pady=(10, 5))
        
        # Scrollable frame for checkboxes
        scroll_frame = ctk.CTkScrollableFrame(main_frame, height=250)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Equipment checkboxes
        equipment_vars = {}
        for eq_no, equipment in self.equipment_map.items():
            var = ctk.BooleanVar(value=True)
            equipment_vars[eq_no] = var
            
            cb = ctk.CTkCheckBox(
                scroll_frame,
                text=f"{equipment.equipment_number}: {equipment.equipment_description}",
                variable=var,
                font=("Segoe UI", 10)
            )
            cb.pack(anchor="w", padx=5, pady=2)
        
        # Select all/none buttons
        select_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        select_frame.pack(fill="x", padx=10, pady=5)
        
        def select_all():
            for var in equipment_vars.values():
                var.set(True)
        
        def select_none():
            for var in equipment_vars.values():
                var.set(False)
        
        ctk.CTkButton(
            select_frame,
            text="Select All",
            command=select_all,
            width=80,
            height=24,
            font=("Segoe UI", 9)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            select_frame,
            text="Select None",
            command=select_none,
            width=80,
            height=24,
            font=("Segoe UI", 9)
        ).pack(side="left", padx=5)
        
        # Filename
        filename_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        filename_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            filename_frame,
            text="Filename:",
            font=("Segoe UI", 11)
        ).pack(side="left", padx=5)
        
        default_name = f"Inspection_Plan_{time.strftime('%Y%m%d_%H%M%S')}.pptx"
        filename_var = ctk.StringVar(value=default_name)
        
        filename_entry = ctk.CTkEntry(
            filename_frame,
            textvariable=filename_var,
            width=200
        )
        filename_entry.pack(side="left", padx=5)
        
        # Action buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def generate_powerpoint():
            # Get selected equipment
            selected_equipment = []
            for eq_no, var in equipment_vars.items():
                if var.get():
                    selected_equipment.append(eq_no)
            
            if not selected_equipment:
                messagebox.showwarning("No Selection", "Please select at least one equipment.")
                return
            
            # Close dialog
            dialog.destroy()
            
            # Show loading
            if hasattr(self.controller, 'show_loading'):
                try:
                    self.controller.show_loading("Generating PowerPoint...")
                except:
                    pass
            
            # Generate in background thread
            def generate_thread():
                success = self.export_to_powerpoint(
                    equipment_numbers=selected_equipment,
                    filename=filename_var.get()
                )
                
                # Hide loading
                if hasattr(self.controller, 'hide_loading'):
                    try:
                        self.parent.after(0, self.controller.hide_loading)
                    except:
                        pass
                
                # Show result
                self.parent.after(0, lambda s=success: self._show_powerpoint_result(s))
            
            thread = threading.Thread(target=generate_thread, daemon=True)
            thread.start()
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=32,
            font=("Segoe UI", 10)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Generate PowerPoint",
            command=generate_powerpoint,
            width=150,
            height=32,
            font=("Segoe UI", 11, "bold")
        ).pack(side="right", padx=5)

    def _show_powerpoint_result(self, success: bool):
        """Show PowerPoint generation result safely."""
        try:
            if self.parent.winfo_exists():
                if success:
                    messagebox.showinfo(
                        "Success",
                        "PowerPoint created successfully!"
                    )
                else:
                    messagebox.showerror(
                        "Error",
                        "Failed to create PowerPoint. Check logs for details."
                    )
        except:
            # Widget destroyed, just log
            if success:
                print("PowerPoint created successfully!")
            else:
                print("Failed to create PowerPoint")

    def _safe_show_message(self, title: str, message: str, msg_type: str = "info"):
        """Safely show a message box, checking if window exists."""
        try:
            # Check if parent window still exists
            if hasattr(self.parent, 'winfo_exists') and self.parent.winfo_exists():
                # Schedule the message box on the main thread
                if msg_type == "info":
                    self.parent.after(100, lambda: messagebox.showinfo(title, message))
                elif msg_type == "error":
                    self.parent.after(100, lambda: messagebox.showerror(title, message))
                elif msg_type == "warning":
                    self.parent.after(100, lambda: messagebox.showwarning(title, message))
        except Exception as e:
            # If we can't show a message box, just log it
            self.append_extraction_log(f"⚠️ Could not show message: {title} - {message}")

