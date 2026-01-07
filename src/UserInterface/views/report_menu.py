"""Enhanced Report Menu view with in-app editing, versioning, and database integration."""

import os
import subprocess
import platform
from typing import List, Dict, Any, Optional
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, messagebox
from UserInterface.views.edit_report_view import EditReportView
from UserInterface.services.report_version_service import ReportVersionService
from UserInterface.services.database_service import DatabaseService
from AutoRBI_Database.database.session import SessionLocal
from powerpoint_generator import PowerPointGenerator


class ReportMenuView:
    """Handles the Report Menu interface with editing and versioning capabilities."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.report_rows: List[Dict[str, Any]] = []
        self.table_body: Optional[ctk.CTkScrollableFrame] = None
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        self.edit_report_view = EditReportView(self.parent, self)
        self.version_service = ReportVersionService(self.project_root)
        self.db = SessionLocal()
        self.available_works = []  # Store works for current user

    def _get_available_works(self) -> List[Dict[str, Any]]:
        """Get list of works available to the current user from controller."""
        try:
            if hasattr(self.controller, 'available_works'):
                return getattr(self.controller, 'available_works', [])
            else:
                # Fallback to empty list
                return []
        except Exception as e:
            print(f"Error getting available works: {e}")
            return []

    def _load_reports_from_filesystem(self) -> List[Dict[str, Any]]:
        """Load reports by scanning output_files directory structure with versioning."""
        reports = []
        
        # Get available works from controller
        self.available_works = self._get_available_works()
        
        # Create a set of work names for quick lookup
        assigned_work_names = {work['work_name'] for work in self.available_works}
        
        output_files_dir = os.path.join(self.project_root, "src", "output_files")
        
        if not os.path.isdir(output_files_dir):
            return reports
        
        try:
            # Only show works that are assigned to current user
            for work in self.available_works:
                work_name = work['work_name']
                work_id = work['work_id']
                work_path = os.path.join(output_files_dir, work_name)
                
                if not os.path.isdir(work_path):
                    # Work directory doesn't exist, but we still want to show it
                    # so users can generate files from database
                    has_database_data = self._check_database_data_exists(work_id)
                    
                    if has_database_data:
                        reports.append({
                            'work_name': work_name,
                            'work_id': work_id,
                            'name': f"Work: {work_name}",
                            'created_at': "-",
                            'excel_versions': [],
                            'ppt_versions': [],
                            'version_count': 0,
                            'has_database_data': True,
                            'has_files': False
                        })
                    continue
                
                # Get all versions of Excel files
                excel_versions = self._get_file_versions(
                    os.path.join(work_path, "excel"),
                    ['.xlsx', '.xls']
                )
                
                # Get all versions of PowerPoint files
                ppt_versions = self._get_file_versions(
                    os.path.join(work_path, "powerpoint"),
                    ['.pptx']
                )
                
                # Check if data exists in database
                has_database_data = self._check_database_data_exists(work_id)
                
                # Create report entry
                latest_time = self._get_latest_modification_time(excel_versions, ppt_versions)
                created_at = datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M') if latest_time else "-"
                
                reports.append({
                    'work_name': work_name,
                    'work_id': work_id,
                    'name': f"Work: {work_name}",
                    'created_at': created_at,
                    'excel_versions': excel_versions,
                    'ppt_versions': ppt_versions,
                    'version_count': max(len(excel_versions), len(ppt_versions)),
                    'has_database_data': has_database_data,
                    'has_files': bool(excel_versions or ppt_versions)
                })
        
        except Exception as e:
            print(f"Error loading reports from filesystem: {e}")
        
        # Sort by creation date (most recent first)
        reports.sort(key=lambda x: x['created_at'] if x['created_at'] != "-" else "0000-00-00 00:00", reverse=True)
        return reports

    def _check_database_data_exists(self, work_id: str) -> bool:
        """Check if equipment data exists in database for this work."""
        try:
            from AutoRBI_Database.database.models.equipment import Equipment
            
            # Convert work_id to int if it's a string
            try:
                work_id_int = int(work_id)
            except (ValueError, TypeError):
                # If work_id is not an int, try to find by name
                from AutoRBI_Database.database.models.work import Work
                work = self.db.query(Work).filter(Work.work_name == work_id).first()
                if not work:
                    return False
                work_id_int = work.work_id
            
            equipment_count = self.db.query(Equipment).filter(
                Equipment.work_id == work_id_int
            ).count()
            
            return equipment_count > 0
            
        except Exception as e:
            print(f"Error checking database data: {e}")
            return False

    def _get_file_versions(self, base_dir: str, extensions: List[str]) -> List[Dict[str, Any]]:
        """Get all versions of files in a directory structure."""
        versions = []
        
        # Check if directory exists
        if not os.path.isdir(base_dir):
            return versions
        
        # Check 'updated' folder for extraction versions
        updated_dir = os.path.join(base_dir, "updated")
        if os.path.isdir(updated_dir):
            for fname in os.listdir(updated_dir):
                if any(fname.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(updated_dir, fname)
                    versions.append({
                        'path': file_path,
                        'version_type': 'extraction',
                        'version_number': 1,
                        'modified': os.path.getmtime(file_path),
                        'display_name': 'Original Extraction'
                    })
        
        # Check 'edited' folder for edited versions
        edited_dir = os.path.join(base_dir, "edited")
        if os.path.isdir(edited_dir):
            edited_files = []
            for fname in os.listdir(edited_dir):
                if any(fname.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(edited_dir, fname)
                    edited_files.append((os.path.getmtime(file_path), file_path, fname))
            
            edited_files.sort()
            
            for idx, (mtime, file_path, fname) in enumerate(edited_files, start=2):
                versions.append({
                    'path': file_path,
                    'version_type': 'edited',
                    'version_number': idx,
                    'modified': mtime,
                    'display_name': f'Edited Version {idx - 1}'
                })
        
        versions.sort(key=lambda x: x['version_number'])
        return versions

    def _get_latest_modification_time(self, excel_versions: List, ppt_versions: List) -> Optional[float]:
        """Get the latest modification time from all versions."""
        all_times = []
        
        for version in excel_versions:
            all_times.append(version['modified'])
        
        for version in ppt_versions:
            all_times.append(version['modified'])
        
        return max(all_times) if all_times else None

    def _add_report_row(self, index: int, report: Dict[str, Any]) -> None:
        """Add a row to the report table with version support."""
        if self.table_body is None:
            return

        name = report.get("name", f"Report {index}")
        created_at = report.get("created_at", "-")
        excel_versions = report.get('excel_versions', [])
        ppt_versions = report.get('ppt_versions', [])
        version_count = report.get('version_count', 0)
        has_database_data = report.get('has_database_data', False)
        has_files = report.get('has_files', False)
        work_name = report.get('work_name', '')

        row_frame = ctk.CTkFrame(
            self.table_body,
            corner_radius=4,
            border_width=1,
            border_color=("gray80", "gray30"),
            height=60,
        )
        row_frame.grid(row=index, column=0, columnspan=4, sticky="ew", pady=2)
        row_frame.grid_columnconfigure(0, weight=0, minsize=50)
        row_frame.grid_columnconfigure(1, weight=2)
        row_frame.grid_columnconfigure(2, weight=1)
        row_frame.grid_columnconfigure(3, weight=2)

        no_label = ctk.CTkLabel(
            row_frame,
            text=str(index),
            font=("Segoe UI", 11),
            anchor="center",
        )
        no_label.grid(row=0, column=0, sticky="ew", padx=12, pady=12)

        name_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        name_frame.grid(row=0, column=1, sticky="ew", padx=12, pady=12)
        
        name_label = ctk.CTkLabel(
            name_frame,
            text=name,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        name_label.pack(anchor="w")
        
        # Show database and file status
        status_texts = []
        if has_database_data:
            status_texts.append("📊 Data in DB")
        if has_files:
            if version_count > 1:
                status_texts.append(f"{version_count} file versions")
            elif excel_versions or ppt_versions:
                status_texts.append("Files available")
        
        if status_texts:
            status_label = ctk.CTkLabel(
                name_frame,
                text=" • ".join(status_texts),
                font=("Segoe UI", 9),
                text_color=("gray60", "gray70"),
                anchor="w",
            )
            status_label.pack(anchor="w")

        date_label = ctk.CTkLabel(
            row_frame,
            text=created_at,
            font=("Segoe UI", 10),
            text_color=("gray60", "gray80"),
            anchor="w",
        )
        date_label.grid(row=0, column=2, sticky="ew", padx=12, pady=12)

        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=3, sticky="e", padx=12, pady=8)

        # Generate PowerPoint button - only enabled if data exists in DB
        generate_ppt_btn = ctk.CTkButton(
            actions_frame,
            text="🎬 Generate PPT",
            width=90,
            height=28,
            font=("Segoe UI", 9),
            state="normal" if has_database_data else "disabled",
            command=lambda r=report: self._generate_powerpoint_from_db(r),
        )
        generate_ppt_btn.pack(side="left", padx=(0, 4))

        open_btn = ctk.CTkButton(
            actions_frame,
            text="Open",
            width=70,
            height=28,
            font=("Segoe UI", 9),
            state="normal" if has_files else "disabled",
            command=lambda r=report: self._show_open_menu(r),
        )
        open_btn.pack(side="left", padx=(0, 4))

        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️ Edit",
            width=70,
            height=28,
            font=("Segoe UI", 9),
            state="normal" if has_files else "disabled",
            command=lambda r=report: self._edit_report(r),
        )
        edit_btn.pack(side="left", padx=(0, 4))

        download_btn = ctk.CTkButton(
            actions_frame,
            text="Download",
            width=80,
            height=28,
            font=("Segoe UI", 9),
            fg_color=("gray20", "gray30"),
            state="normal" if has_files else "disabled",
            command=lambda r=report: self._show_download_menu(r),
        )
        download_btn.pack(side="left")

    def _show_open_menu(self, report: Dict[str, Any]) -> None:
        """Show menu for selecting version and file type to open."""
        excel_versions = report.get('excel_versions', [])
        ppt_versions = report.get('ppt_versions', [])
        
        if not excel_versions and not ppt_versions:
            messagebox.showwarning("No Files", "No files available to open.")
            return
        
        menu = ctk.CTkToplevel(self.parent)
        menu.title("Open Report")
        menu.geometry("400x500")
        menu.transient(self.parent)
        menu.grab_set()
        
        menu.update_idletasks()
        x = (menu.winfo_screenwidth() // 2) - (400 // 2)
        y = (menu.winfo_screenheight() // 2) - (500 // 2)
        menu.geometry(f'400x500+{x}+{y}')
        
        title_label = ctk.CTkLabel(
            menu,
            text="Select Version to Open",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(pady=(20, 10))
        
        scroll_frame = ctk.CTkScrollableFrame(menu, width=360, height=380)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        if excel_versions:
            excel_header = ctk.CTkLabel(
                scroll_frame,
                text="📊 Excel Versions",
                font=("Segoe UI", 12, "bold"),
                anchor="w"
            )
            excel_header.pack(anchor="w", pady=(5, 5))
            
            for version in excel_versions:
                self._create_version_button(
                    scroll_frame,
                    version,
                    "excel",
                    menu,
                    report
                )
        
        if ppt_versions:
            ppt_header = ctk.CTkLabel(
                scroll_frame,
                text="📑 PowerPoint Versions",
                font=("Segoe UI", 12, "bold"),
                anchor="w"
            )
            ppt_header.pack(anchor="w", pady=(15, 5))
            
            for version in ppt_versions:
                self._create_version_button(
                    scroll_frame,
                    version,
                    "powerpoint",
                    menu,
                    report
                )
        
        close_btn = ctk.CTkButton(
            menu,
            text="Close",
            width=120,
            command=menu.destroy
        )
        close_btn.pack(pady=(0, 20))

    def _create_version_button(self, parent: ctk.CTkFrame, version: Dict, file_type: str, menu_window, report: Dict) -> None:
        """Create a button for a specific version."""
        version_frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        version_frame.pack(fill="x", pady=2, padx=5)
        
        info_frame = ctk.CTkFrame(version_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=version['display_name'],
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        date_str = datetime.fromtimestamp(version['modified']).strftime('%Y-%m-%d %H:%M')
        date_label = ctk.CTkLabel(
            info_frame,
            text=f"Modified: {date_str}",
            font=("Segoe UI", 8),
            text_color=("gray60", "gray70"),
            anchor="w"
        )
        date_label.pack(anchor="w")
        
        open_btn = ctk.CTkButton(
            version_frame,
            text="Open",
            width=60,
            height=25,
            font=("Segoe UI", 9),
            command=lambda: (self._open_file(version['path'], report, file_type), menu_window.destroy())
        )
        open_btn.pack(side="right", padx=10)

    def _open_file(self, file_path: str, report: Dict[str, Any], file_type: str) -> None:
        """Open a file and log the action to database."""
        if not os.path.exists(file_path):
            messagebox.showerror("File Not Found", f"File does not exist:\n{file_path}")
            return
        
        try:
            # Log action to database
            self._log_action_to_database(report['work_name'], "open_report", f"Opened {file_type} file")
            
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', file_path])
            else:
                subprocess.Popen(['xdg-open', file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def _edit_report(self, report: Dict[str, Any]) -> None:
        """Open dialog to select which file to edit."""
        work_name = report['work_name']
        excel_versions = report.get('excel_versions', [])
        ppt_versions = report.get('ppt_versions', [])
        
        # Get latest files for each type
        latest_excel = excel_versions[-1]['path'] if excel_versions else None
        latest_ppt = ppt_versions[-1]['path'] if ppt_versions else None
        
        menu = ctk.CTkToplevel(self.parent)
        menu.title("Select File to Edit")
        menu.geometry("400x280")  # Increased height to accommodate more info
        menu.transient(self.parent)
        menu.grab_set()
        
        menu.update_idletasks()
        x = (menu.winfo_screenwidth() // 2) - (400 // 2)
        y = (menu.winfo_screenheight() // 2) - (280 // 2)
        menu.geometry(f'400x280+{x}+{y}')
        
        title_label = ctk.CTkLabel(
            menu,
            text="Select File to Edit",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(pady=(20, 10))
        
        subtitle_label = ctk.CTkLabel(
            menu,
            text=f"Work: {work_name}",
            font=("Segoe UI", 10),
            text_color=("gray60", "gray70")
        )
        subtitle_label.pack(pady=(0, 15))
        
        # Excel option
        excel_frame = ctk.CTkFrame(menu, fg_color=("gray95", "gray15"))
        excel_frame.pack(pady=5, padx=20, fill="x")
        
        excel_btn = ctk.CTkButton(
            excel_frame,
            text="📊 Edit Excel Data",
            height=40,
            state="normal" if latest_excel else "disabled",
            command=lambda: self._open_edit_view(report, latest_excel, menu, file_type='excel')
        )
        excel_btn.pack(pady=5, padx=10, fill="x")
        
        if latest_excel:
            excel_info = ctk.CTkLabel(
                excel_frame,
                text=f"{len(excel_versions)} version(s) available",
                font=("Segoe UI", 9),
                text_color=("gray60", "gray70")
            )
            excel_info.pack(pady=(0, 5))
        else:
            excel_info = ctk.CTkLabel(
                excel_frame,
                text="No Excel file available for editing",
                font=("Segoe UI", 9),
                text_color=("red", "orange")
            )
            excel_info.pack(pady=(0, 5))
        
        # PowerPoint option
        ppt_frame = ctk.CTkFrame(menu, fg_color=("gray95", "gray15"))
        ppt_frame.pack(pady=5, padx=20, fill="x")
        
        ppt_btn = ctk.CTkButton(
            ppt_frame,
            text="📑 Edit PowerPoint File",
            height=40,
            font=("Segoe UI", 11),
            fg_color=("purple", "mediumpurple"),
            state="normal" if latest_ppt else "disabled",
            command=lambda: self._open_edit_view(report, latest_ppt, menu, file_type='powerpoint')
        )
        ppt_btn.pack(pady=5, padx=10, fill="x")
        
        if latest_ppt:
            ppt_info = ctk.CTkLabel(
                ppt_frame,
                text=f"{len(ppt_versions)} version(s) available",
                font=("Segoe UI", 9),
                text_color=("gray60", "gray70")
            )
            ppt_info.pack(pady=(0, 5))
        else:
            ppt_info = ctk.CTkLabel(
                ppt_frame,
                text="No PowerPoint file available for editing",
                font=("Segoe UI", 9),
                text_color=("red", "orange")
            )
            ppt_info.pack(pady=(0, 5))
        
        cancel_btn = ctk.CTkButton(
            menu,
            text="Cancel",
            height=36,
            font=("Segoe UI", 10),
            fg_color=("gray50", "gray40"),
            command=menu.destroy
        )
        cancel_btn.pack(pady=(15, 20), padx=20, fill="x")
    
    def _get_latest_file(self, work_name: str, file_type: str) -> Optional[str]:
        """Get the latest file from the updated directory."""
        if file_type == 'excel':
            base_dir = os.path.join(self.project_root, "src", "output_files", work_name, "excel", "updated")
            extensions = ['.xlsx', '.xls']
        elif file_type == 'powerpoint':
            base_dir = os.path.join(self.project_root, "src", "output_files", work_name, "powerpoint", "updated")
            extensions = ['.pptx']
        else:
            return None
        
        if not os.path.isdir(base_dir):
            return None
        
        matching_files = []
        for fname in os.listdir(base_dir):
            if any(fname.lower().endswith(ext) for ext in extensions):
                file_path = os.path.join(base_dir, fname)
                matching_files.append((os.path.getmtime(file_path), file_path))
        
        if not matching_files:
            return None
        
        matching_files.sort(reverse=True)
        return matching_files[0][1]
    
    def _open_edit_view(self, report: Dict[str, Any], file_path: str, menu_window, file_type: str = 'excel') -> None:
        """Open the edit view with the selected file."""
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found:\n{file_path}")
            return
        
        edit_context = {
            'work_name': report['work_name'],
            'file_path': file_path,
            'file_type': file_type,
            'report_data': report,
            'db': self.db,
            'user_id': getattr(self.controller, 'current_user', {}).get('id')
        }
        
        menu_window.destroy()
        self.edit_report_view.show(edit_context)

    def _show_download_menu(self, report: Dict[str, Any]) -> None:
        """Show menu for downloading specific versions."""
        excel_versions = report.get('excel_versions', [])
        ppt_versions = report.get('ppt_versions', [])
        
        if not excel_versions and not ppt_versions:
            messagebox.showwarning("No Files", "No files available for download.")
            return
        
        menu = ctk.CTkToplevel(self.parent)
        menu.title("Download Report")
        menu.geometry("400x500")
        menu.transient(self.parent)
        menu.grab_set()
        
        menu.update_idletasks()
        x = (menu.winfo_screenwidth() // 2) - (400 // 2)
        y = (menu.winfo_screenheight() // 2) - (500 // 2)
        menu.geometry(f'400x500+{x}+{y}')
        
        title_label = ctk.CTkLabel(
            menu,
            text="Select Version to Download",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(pady=(20, 10))
        
        scroll_frame = ctk.CTkScrollableFrame(menu, width=360, height=380)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        if excel_versions:
            excel_header = ctk.CTkLabel(
                scroll_frame,
                text="📊 Excel Versions",
                font=("Segoe UI", 12, "bold"),
                anchor="w"
            )
            excel_header.pack(anchor="w", pady=(5, 5))
            
            for version in excel_versions:
                self._create_download_button(
                    scroll_frame,
                    version,
                    "excel",
                    menu,
                    report
                )
        
        if ppt_versions:
            ppt_header = ctk.CTkLabel(
                scroll_frame,
                text="📑 PowerPoint Versions",
                font=("Segoe UI", 12, "bold"),
                anchor="w"
            )
            ppt_header.pack(anchor="w", pady=(15, 5))
            
            for version in ppt_versions:
                self._create_download_button(
                    scroll_frame,
                    version,
                    "powerpoint",
                    menu,
                    report
                )
        
        close_btn = ctk.CTkButton(
            menu,
            text="Close",
            width=120,
            command=menu.destroy
        )
        close_btn.pack(pady=(0, 20))

    def _create_download_button(self, parent: ctk.CTkFrame, version: Dict, file_type: str, menu_window, report: Dict) -> None:
        """Create a button for downloading a specific version."""
        version_frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        version_frame.pack(fill="x", pady=2, padx=5)
        
        info_frame = ctk.CTkFrame(version_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=version['display_name'],
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        date_str = datetime.fromtimestamp(version['modified']).strftime('%Y-%m-%d %H:%M')
        date_label = ctk.CTkLabel(
            info_frame,
            text=f"Modified: {date_str}",
            font=("Segoe UI", 8),
            text_color=("gray60", "gray70"),
            anchor="w"
        )
        date_label.pack(anchor="w")
        
        download_btn = ctk.CTkButton(
            version_frame,
            text="Download",
            width=80,
            height=25,
            font=("Segoe UI", 9),
            command=lambda: self._save_file_copy(version['path'], file_type, report)
        )
        download_btn.pack(side="right", padx=10)

    def _save_file_copy(self, source_path: str, file_type: str, report: Dict[str, Any]) -> None:
        """Save a copy of the file and log the action."""
        if not os.path.exists(source_path):
            messagebox.showerror("File Not Found", f"File does not exist:\n{source_path}")
            return
        
        if file_type == "excel":
            filetypes = [("Excel files", "*.xlsx"), ("All files", "*.*")]
        elif file_type == "powerpoint":
            filetypes = [("PowerPoint files", "*.pptx"), ("All files", "*.*")]
        else:
            filetypes = [("All files", "*.*")]
        
        default_name = os.path.basename(source_path)
        save_path = filedialog.asksaveasfilename(
            defaultextension=os.path.splitext(default_name)[1],
            initialfile=default_name,
            filetypes=filetypes
        )
        
        if not save_path:
            return
        
        try:
            import shutil
            shutil.copy2(source_path, save_path)
            
            # Log action to database
            self._log_action_to_database(report['work_name'], "download_report", f"Downloaded {file_type} file")
            
            messagebox.showinfo("Success", f"File saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")

    def _log_action_to_database(self, work_name: str, action_type: str, description: str) -> None:
        """Log an action to the database work_history table."""
        try:
            from AutoRBI_Database.database.models.work import Work
            
            work = self.db.query(Work).filter(Work.work_name == work_name).first()
            if work:
                user_id = getattr(self.controller, 'current_user', {}).get('id')
                if user_id:
                    DatabaseService.log_work_history(
                        self.db,
                        work.work_id,
                        user_id,
                        action_type=action_type,
                        description=description
                    )
        except Exception as e:
            print(f"Error logging action to database: {e}")

    def show(self) -> None:
        """Display the Report Menu interface."""
        for widget in self.parent.winfo_children():
            widget.destroy()

        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header
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

        # Main content
        main_frame = ctk.CTkFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        main_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            main_frame,
            text="Report Menu",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="View, edit, and export work reports with version control.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        # Table
        table_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        table_container.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Header
        header_row = ctk.CTkFrame(
            table_container,
            corner_radius=8,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("gray90", "gray20"),
        )
        header_row.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        header_row.grid_columnconfigure(0, weight=0, minsize=50)
        header_row.grid_columnconfigure(1, weight=2)
        header_row.grid_columnconfigure(2, weight=1)
        header_row.grid_columnconfigure(3, weight=2)

        headers = ["No.", "Work Name", "Date", "Actions"]
        for col, header_text in enumerate(headers):
            header_label = ctk.CTkLabel(
                header_row,
                text=header_text,
                font=("Segoe UI", 11, "bold"),
                anchor="w" if col < 3 else "e",
            )
            header_label.grid(row=0, column=col, sticky="ew", padx=12, pady=10)

        # Body
        self.table_body = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.table_body.grid(row=1, column=0, sticky="nsew")
        self.table_body.grid_columnconfigure(0, weight=0, minsize=50)
        self.table_body.grid_columnconfigure(1, weight=2)
        self.table_body.grid_columnconfigure(2, weight=1)
        self.table_body.grid_columnconfigure(3, weight=2)

        # Load and display reports
        reports = self._load_reports_from_filesystem()
        
        if reports:
            for idx, report in enumerate(reports, start=1):
                self._add_report_row(idx, report)
        else:
            hint_label = ctk.CTkLabel(
                self.table_body,
                text="No reports available. Complete a 'New Work' to generate reports.",
                font=("Segoe UI", 11),
                text_color=("gray40", "gray75"),
                justify="left",
            )
            hint_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(8, 8))

        # Refresh button
        refresh_btn = ctk.CTkButton(
            main_frame,
            text="🔄 Refresh Reports",
            command=self.show,
            height=36,
            font=("Segoe UI", 11),
            width=150,
        )
        refresh_btn.grid(row=3, column=0, sticky="e", padx=24, pady=(0, 24))

    def _generate_powerpoint_from_db(self, report: Dict[str, Any]) -> None:
        """Generate PowerPoint directly from database data."""
        work_name = report['work_name']
        work_id = report['work_id']
        
        # Show progress dialog
        progress_window = self._create_progress_window("Generating PowerPoint")
        
        try:
            # Step 1: Fetch equipment data from database
            progress_window.update_progress(0.1, "Loading equipment data from database...")
            equipment_map = self._get_equipment_from_database(work_id)
            
            if not equipment_map:
                progress_window.close()
                messagebox.showerror(
                    "No Data", 
                    f"No equipment data found in database for '{work_name}'.\n"
                    "Please complete data extraction first."
                )
                return
            
            progress_window.update_progress(0.3, f"Loaded {len(equipment_map)} equipment items...")
            
            # Step 2: Get template path
            progress_window.update_progress(0.4, "Locating PowerPoint template...")
            template_path = self._get_powerpoint_template()
            
            if not template_path:
                progress_window.close()
                messagebox.showerror("Template Not Found", "PowerPoint template not found.")
                return
            
            progress_window.update_progress(0.5, "Template found, preparing generator...")
            
            # Step 3: Create output directory
            work_dir = os.path.join(self.project_root, "src", "output_files", work_name, "powerpoint", "updated")
            os.makedirs(work_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{work_name}_generated_{timestamp}.pptx"
            output_path = os.path.join(work_dir, output_filename)
            
            progress_window.update_progress(0.6, "Generating PowerPoint file...")
            
            # Step 4: Generate PowerPoint
            generator = PowerPointGenerator(template_path)
            success = generator.generate_from_equipment_map(equipment_map, output_path)
            
            if success:
                progress_window.update_progress(0.8, "Updating database records...")
                
                # Step 5: Update Work record with new PowerPoint path
                self._update_work_powerpoint_path(work_id, output_path)
                
                # Step 6: Log the action
                self._log_action_to_database(work_name, "generate_ppt_from_db", 
                                           f"Generated PowerPoint with {len(equipment_map)} equipment")
                
                progress_window.update_progress(1.0, "Complete!")
                progress_window.close()
                
                # Show success message
                response = messagebox.askyesno(
                    "Success",
                    f"✅ PowerPoint generated successfully!\n\n"
                    f"File: {output_filename}\n"
                    f"Equipment: {len(equipment_map)} items\n\n"
                    f"Would you like to open the PowerPoint file now?"
                )
                
                if response:
                    self._open_file(output_path, report, 'powerpoint')
                else:
                    # Refresh the report list to show the new file
                    self.show()
            else:
                progress_window.close()
                messagebox.showerror("Error", "Failed to generate PowerPoint. Check logs for details.")
                
        except Exception as e:
            progress_window.close()
            messagebox.showerror("Error", f"Failed to generate PowerPoint:\n{e}")
            import traceback
            traceback.print_exc()

    def _get_equipment_from_database(self, work_id: str) -> Dict[str, Any]:
        """Fetch equipment data from database."""
        try:
            from AutoRBI_Database.database.models.work import Work
            from AutoRBI_Database.database.models.equipment import Equipment as DbEquipment
            from AutoRBI_Database.database.models.component import Component as DbComponent
            from models.equipment import Equipment as ModelEquipment
            from models.equipment_component import Component as ModelComponent
            
            # Convert work_id to int
            try:
                work_id_int = int(work_id)
            except (ValueError, TypeError):
                # If work_id is a name, find by name
                work = self.db.query(Work).filter(Work.work_name == work_id).first()
                if not work:
                    print(f"No work found with ID/name: {work_id}")
                    return {}
                work_id_int = work.work_id
            
            # Fetch all equipment for this work
            db_equipment_list = self.db.query(DbEquipment).filter(
                DbEquipment.work_id == work_id_int
            ).all()
            
            equipment_map = {}
            
            for db_equipment in db_equipment_list:
                # Create ModelEquipment object
                model_equipment = ModelEquipment(
                    equipment_number=db_equipment.equipment_no,
                    pmt_number=db_equipment.pmt_no,
                    equipment_description=db_equipment.description,
                    row_index=getattr(db_equipment, 'row_index', None)
                )
                
                # Fetch components for this equipment
                db_components = self.db.query(DbComponent).filter(
                    DbComponent.equipment_id == db_equipment.equipment_id
                ).all()
                
                for db_component in db_components:
                    # Extract existing_data from component
                    existing_data = {
                        'fluid': db_component.fluid or "",
                        'material_type': db_component.material_spec or "",  # Note: material_spec, not material_type
                        'spec': getattr(db_component, 'material_spec', "") or "",
                        'grade': db_component.material_grade or "",
                        'insulation': db_component.insulation or "",
                        'design_temp': db_component.design_temp or "",
                        'design_pressure': db_component.design_pressure or "",
                        'operating_temp': db_component.operating_temp or "",
                        'operating_pressure': db_component.operating_pressure or "",
                        'phase': db_component.phase or ""
                    }
                    
                    # Create ModelComponent object
                    model_component = ModelComponent(
                        component_name=db_component.part_name,  # Note: part_name, not component_name
                        phase=db_component.phase or "",
                        existing_data=existing_data,
                        row_index=getattr(db_component, 'row_index', None)
                    )
                    
                    # Add component to equipment
                    model_equipment.add_component(model_component)
                
                # Add equipment to map
                equipment_map[db_equipment.equipment_no] = model_equipment
            
            print(f"Loaded {len(equipment_map)} equipment from database for work ID {work_id}")
            return equipment_map
            
        except Exception as e:
            print(f"Error loading equipment from database: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _get_powerpoint_template(self) -> Optional[str]:
        """Get the PowerPoint template path."""
        template_path = os.path.join(
            self.project_root, "CaseStudy1Resources", "Inspection Plan Template.pptx"
        )
        
        if os.path.exists(template_path):
            return template_path
        
        # Try alternative paths
        alternative_paths = [
            os.path.join(self.project_root, "resources", "Inspection Plan Template.pptx"),
            os.path.join(self.project_root, "templates", "Inspection Plan Template.pptx"),
        ]
        
        for path in alternative_paths:
            if os.path.exists(path):
                return path
        
        return None

    def _update_work_powerpoint_path(self, work_id: str, ppt_path: str) -> None:
        """Update Work record with new PowerPoint path."""
        try:
            from AutoRBI_Database.database.models.work import Work
            
            # Convert work_id to int
            try:
                work_id_int = int(work_id)
                work = self.db.query(Work).filter(Work.work_id == work_id_int).first()
            except (ValueError, TypeError):
                # If work_id is a name, find by name
                work = self.db.query(Work).filter(Work.work_name == work_id).first()
            
            if work:
                work.ppt_path = ppt_path
                self.db.commit()
                print(f"Updated PowerPoint path for work '{work.work_name}'")
        except Exception as e:
            print(f"Error updating work PowerPoint path: {e}")

    def _create_progress_window(self, title: str = "Processing"):
        """Create a progress window for long operations."""
        return ProgressWindow(self.parent, title)

class ProgressWindow:
    """Simple progress window for long operations."""
    
    def __init__(self, parent, title="Processing"):
        self.window = ctk.CTkToplevel(parent)
        self.window.title(title)
        self.window.geometry("400x150")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 200
        y = (self.window.winfo_screenheight() // 2) - 75
        self.window.geometry(f'400x150+{x}+{y}')
        
        self.label = ctk.CTkLabel(
            self.window,
            text="Processing...",
            font=("Segoe UI", 12)
        )
        self.label.pack(pady=(30, 10))
        
        self.progress = ctk.CTkProgressBar(self.window, width=350)
        self.progress.pack(pady=10)
        self.progress.set(0)
        
        self.status = ctk.CTkLabel(
            self.window,
            text="",
            font=("Segoe UI", 10),
            text_color=("gray60", "gray70")
        )
        self.status.pack(pady=5)
    
    def update_progress(self, value: float, text: str = ""):
        """Update progress bar and text."""
        self.progress.set(value)
        self.status.configure(text=text)
        self.window.update()
    
    def close(self):
        """Close the progress window."""
        self.window.destroy()