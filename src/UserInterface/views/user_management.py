"""User Management view for AutoRBI application (CustomTkinter).

This view follows the same UI patterns as work_history.py and report_menu.py
to ensure consistent user experience across the application.
"""

from typing import List, Dict, Any, Optional, Callable
import customtkinter as ctk
from tkinter import messagebox

from AutoRBI_Database.validation_rules import (
    RoleRules,
    StatusRules,
    get_username_validation_error,
    get_fullname_validation_error,
    get_password_validation_error,
)


class UserManagementView:
    """Handles the User Management interface (Admin only)."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.user_rows: List[Dict[str, Any]] = []
        self.table_body: Optional[ctk.CTkScrollableFrame] = None

        # Pagination state
        self.current_page = 1
        self.per_page = 15
        self.total_pages = 1
        self.total_users = 0

        # Filter state
        self.current_status_filter: Optional[str] = None
        self.current_role_filter: Optional[str] = None
        self.current_search: str = ""

    def load_users(
        self, users: List[Dict[str, Any]], total: int = 0, total_pages: int = 1
    ) -> None:
        """Populate the users table.

        Each user dict should contain:
        {"id": int, "username": str, "full_name": str, "role": str, "status": str, "created_at": str}
        """
        self.user_rows = users
        self.total_users = total
        self.total_pages = total_pages

        if self.table_body is not None:
            # Clear current rows
            for child in self.table_body.winfo_children():
                child.destroy()

            # Rebuild table
            if users:
                for idx, user in enumerate(users, start=1):
                    self._add_user_row(idx, user)
            else:
                # Show hint if no data
                hint_label = ctk.CTkLabel(
                    self.table_body,
                    text="No users found matching the current filters.",
                    font=("Segoe UI", 11),
                    text_color=("gray40", "gray75"),
                    justify="left",
                )
                hint_label.grid(row=0, column=0, columnspan=6, sticky="w", pady=(8, 8))

        # Update pagination display
        self._update_pagination_display()

    def _add_user_row(self, index: int, user: Dict[str, Any]) -> None:
        """Add a row to the users table with FIXED column widths for consistency."""
        if self.table_body is None:
            return

        username = user.get("username", f"User {index}")
        full_name = user.get("full_name", "-")
        role = user.get("role", "Engineer")
        status = user.get("status", "Active")
        user_id = user.get("id")

        # Table row frame - FIXED HEIGHT
        row_frame = ctk.CTkFrame(
            self.table_body,
            corner_radius=4,
            border_width=1,
            border_color=("gray80", "gray30"),
            height=60,  # Fixed height for all rows
        )
        row_frame.grid(row=index, column=0, columnspan=6, sticky="ew", pady=2)
        row_frame.pack_propagate(False)  # Prevent frame from resizing

        # Configure columns with FIXED widths
        row_frame.grid_columnconfigure(0, weight=0, minsize=60)  # No.
        row_frame.grid_columnconfigure(1, weight=0, minsize=150)  # Username
        row_frame.grid_columnconfigure(2, weight=1, minsize=180)  # Full Name
        row_frame.grid_columnconfigure(3, weight=0, minsize=100)  # Role
        row_frame.grid_columnconfigure(4, weight=0, minsize=100)  # Status
        row_frame.grid_columnconfigure(5, weight=0, minsize=200)  # Actions

        # Column 0: No.
        no_label = ctk.CTkLabel(
            row_frame,
            text=str((self.current_page - 1) * self.per_page + index),
            font=("Segoe UI", 11),
            anchor="center",
        )
        no_label.grid(row=0, column=0, sticky="nsew", padx=8, pady=12)

        # Column 1: Username
        username_label = ctk.CTkLabel(
            row_frame,
            text=username,
            font=("Segoe UI", 11),
            anchor="w",
        )
        username_label.grid(row=0, column=1, sticky="nsew", padx=8, pady=12)

        # Column 2: Full Name
        fullname_label = ctk.CTkLabel(
            row_frame,
            text=full_name,
            font=("Segoe UI", 11),
            anchor="w",
        )
        fullname_label.grid(row=0, column=2, sticky="nsew", padx=8, pady=12)

        # Column 3: Role badge
        role_colors = {
            "Admin": ("#3498db", "#2980b9"),  # Blue for Admin
            "Engineer": ("gray70", "gray60"),  # Gray for Engineer
        }
        role_color = role_colors.get(role, ("gray70", "gray60"))
        role_badge = ctk.CTkLabel(
            row_frame,
            text=role,
            font=("Segoe UI", 9, "bold"),
            fg_color=role_color,
            corner_radius=4,
            width=80,
            height=24,
        )
        role_badge.grid(row=0, column=3, sticky="nsew", padx=8, pady=12)

        # Column 4: Status badge
        status_colors = {
            "Active": ("#2ecc71", "#27ae60"),  # Green
            "Inactive": ("#e74c3c", "#c0392b"),  # Red
        }
        status_color = status_colors.get(status, ("gray70", "gray60"))
        status_badge = ctk.CTkLabel(
            row_frame,
            text=status,
            font=("Segoe UI", 9, "bold"),
            fg_color=status_color,
            corner_radius=4,
            width=80,
            height=24,
        )
        status_badge.grid(row=0, column=4, sticky="nsew", padx=8, pady=12)

        # Column 5: Actions
        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=5, sticky="nsew", padx=8, pady=12)

        # Edit button
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="Edit",
            width=70,
            height=32,
            font=("Segoe UI", 10),
            command=lambda u=user: self._show_edit_dialog(u),
        )
        edit_btn.pack(side="left", padx=(0, 4))

        # Toggle Status button (only show if not current user)
        current_user_id = self.controller.current_user.get("id")
        if user_id != current_user_id:
            is_active = status == "Active"
            toggle_text = "Deactivate" if is_active else "Activate"
            toggle_color = ("gray20", "gray30") if is_active else ("#27ae60", "#1e8449")
            hover_color = ("red", "darkred") if is_active else ("#2ecc71", "#27ae60")

            toggle_btn = ctk.CTkButton(
                actions_frame,
                text=toggle_text,
                width=90,
                height=32,
                font=("Segoe UI", 10),
                fg_color=toggle_color,
                hover_color=hover_color,
                command=lambda u=user: self._toggle_user_status(u),
            )
            toggle_btn.pack(side="left")

    def _toggle_user_status(self, user: Dict[str, Any]) -> None:
        """Toggle user between Active and Inactive."""
        action = "deactivate" if user["status"] == "Active" else "activate"

        if not messagebox.askyesno(
            "Confirm Action",
            f"Are you sure you want to {action} user '{user['username']}'?\n\n"
            f"{'This will prevent them from logging in.' if action == 'deactivate' else 'This will allow them to log in again.'}",
        ):
            return

        result = self.controller.toggle_user_status(user["id"])

        if result.get("success"):
            messagebox.showinfo("Success", result["message"])
            self._refresh_users()
        else:
            messagebox.showerror("Error", result.get("message", "Operation failed"))

    def _show_edit_dialog(self, user: Dict[str, Any]) -> None:
        """Open edit user dialog."""
        UserFormDialog(
            parent=self.parent,
            controller=self.controller,
            mode="edit",
            user_data=user,
            on_save=self._refresh_users,
        )

    def _show_add_dialog(self) -> None:
        """Open add user dialog."""
        UserFormDialog(
            parent=self.parent,
            controller=self.controller,
            mode="add",
            on_save=self._refresh_users,
        )

    def _refresh_users(self) -> None:
        """Reload users from backend with current filters."""
        result = self.controller.get_users_list(
            status_filter=self.current_status_filter,
            role_filter=self.current_role_filter,
            search_query=self.current_search,
            page=self.current_page,
            per_page=self.per_page,
        )

        if result.get("success"):
            self.load_users(
                users=result.get("users", []),
                total=result.get("total", 0),
                total_pages=result.get("total_pages", 1),
            )
        else:
            if result.get("error_type") == "unauthorized":
                messagebox.showerror("Access Denied", result["message"])
                self.controller.show_main_menu()
            else:
                messagebox.showerror(
                    "Error", result.get("message", "Failed to load users")
                )

    def _apply_filters(self) -> None:
        """Apply current filter selections and reload."""
        # Get filter values
        status_val = (
            self.status_filter_var.get()
            if hasattr(self, "status_filter_var")
            else "All"
        )
        role_val = (
            self.role_filter_var.get() if hasattr(self, "role_filter_var") else "All"
        )
        search_val = (
            self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        )

        # Set filters (None means no filter)
        self.current_status_filter = None if status_val == "All" else status_val
        self.current_role_filter = None if role_val == "All" else role_val
        self.current_search = search_val

        # Reset to first page
        self.current_page = 1

        # Reload
        self._refresh_users()

    def _clear_filters(self) -> None:
        """Clear all filters and reload."""
        if hasattr(self, "status_filter_var"):
            self.status_filter_var.set("All")
        if hasattr(self, "role_filter_var"):
            self.role_filter_var.set("All")
        if hasattr(self, "search_entry"):
            self.search_entry.delete(0, "end")

        self.current_status_filter = None
        self.current_role_filter = None
        self.current_search = ""
        self.current_page = 1

        self._refresh_users()

    def _prev_page(self) -> None:
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._refresh_users()

    def _next_page(self) -> None:
        """Go to next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._refresh_users()

    def _update_pagination_display(self) -> None:
        """Update pagination info display."""
        if not hasattr(self, "pagination_info") or self.pagination_info is None:
            return

        if self.total_users == 0:
            info_text = "No users found"
            page_text = "Page 0 of 0"
        else:
            start = (self.current_page - 1) * self.per_page + 1
            end = min(self.current_page * self.per_page, self.total_users)
            info_text = f"Showing {start}-{end} of {self.total_users} users"
            page_text = f"Page {self.current_page} of {self.total_pages}"

        self.pagination_info.configure(text=info_text)
        self.page_label.configure(text=page_text)

        # Enable/disable navigation buttons
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(
            state="normal" if self.current_page < self.total_pages else "disabled"
        )

    def show(self) -> None:
        """Display the User Management interface.

        Layout follows the same pattern as work_history.py and report_menu.py.
        """
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Root frame (same as work_history.py)
        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header with back button (same as work_history.py)
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

        # Main content area (same as work_history.py)
        main_frame = ctk.CTkFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        main_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        main_frame.grid_rowconfigure(4, weight=1)  # Table row expands
        main_frame.grid_columnconfigure(0, weight=1)

        # Page title (same as work_history.py)
        page_title = ctk.CTkLabel(
            main_frame,
            text="User Management",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        # Subtitle with Add User button
        subtitle_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        subtitle_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))

        subtitle_label = ctk.CTkLabel(
            subtitle_frame,
            text="Manage user accounts, roles, and access permissions.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.pack(side="left")

        # Add User button (right side)
        add_btn = ctk.CTkButton(
            subtitle_frame,
            text="+ Add User",
            command=self._show_add_dialog,
            width=120,
            height=32,
            font=("Segoe UI", 10, "bold"),
        )
        add_btn.pack(side="right")

        # Filter section (similar to work_history.py filter buttons)
        filter_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        filter_section.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))

        # Status filter
        status_label = ctk.CTkLabel(
            filter_section,
            text="Status:",
            font=("Segoe UI", 10, "bold"),
        )
        status_label.pack(side="left", padx=(0, 8))

        self.status_filter_var = ctk.StringVar(value="All")
        status_dropdown = ctk.CTkComboBox(
            filter_section,
            values=["All", "Active", "Inactive"],
            variable=self.status_filter_var,
            width=100,
            height=28,
            font=("Segoe UI", 10),
            state="readonly",
        )
        status_dropdown.pack(side="left", padx=(0, 16))

        # Role filter
        role_label = ctk.CTkLabel(
            filter_section,
            text="Role:",
            font=("Segoe UI", 10, "bold"),
        )
        role_label.pack(side="left", padx=(0, 8))

        self.role_filter_var = ctk.StringVar(value="All")
        role_dropdown = ctk.CTkComboBox(
            filter_section,
            values=["All"] + RoleRules.VALID_ROLES,
            variable=self.role_filter_var,
            width=100,
            height=28,
            font=("Segoe UI", 10),
            state="readonly",
        )
        role_dropdown.pack(side="left", padx=(0, 16))

        # Search box
        search_label = ctk.CTkLabel(
            filter_section,
            text="Search:",
            font=("Segoe UI", 10, "bold"),
        )
        search_label.pack(side="left", padx=(0, 8))

        self.search_entry = ctk.CTkEntry(
            filter_section,
            placeholder_text="Username or name...",
            width=180,
            height=28,
            font=("Segoe UI", 10),
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._apply_filters())

        # Filter buttons
        apply_btn = ctk.CTkButton(
            filter_section,
            text="Apply",
            command=self._apply_filters,
            width=70,
            height=28,
            font=("Segoe UI", 9),
        )
        apply_btn.pack(side="left", padx=(0, 4))

        clear_btn = ctk.CTkButton(
            filter_section,
            text="Clear",
            command=self._clear_filters,
            width=70,
            height=28,
            font=("Segoe UI", 9),
            fg_color=("gray20", "gray30"),
        )
        clear_btn.pack(side="left")

        # Table container (same as work_history.py)
        table_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        table_container.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 12))
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Table header with FIXED widths
        header_row = ctk.CTkFrame(
            table_container,
            corner_radius=8,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("gray90", "gray20"),
            height=50,
        )
        header_row.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        header_row.pack_propagate(False)

        # Configure header columns with FIXED widths (same as row columns)
        header_row.grid_columnconfigure(0, weight=0, minsize=60)  # No.
        header_row.grid_columnconfigure(1, weight=0, minsize=150)  # Username
        header_row.grid_columnconfigure(2, weight=1, minsize=180)  # Full Name
        header_row.grid_columnconfigure(3, weight=0, minsize=100)  # Role
        header_row.grid_columnconfigure(4, weight=0, minsize=100)  # Status
        header_row.grid_columnconfigure(5, weight=0, minsize=200)  # Actions

        headers = ["No.", "Username", "Full Name", "Role", "Status", "Actions"]
        for col, header_text in enumerate(headers):
            header_label = ctk.CTkLabel(
                header_row,
                text=header_text,
                font=("Segoe UI", 11, "bold"),
                anchor="center" if col in [0, 3, 4, 5] else "w",
            )
            header_label.grid(row=0, column=col, sticky="nsew", padx=8, pady=10)

        # Scrollable table body
        self.table_body = ctk.CTkScrollableFrame(
            table_container, fg_color="transparent"
        )
        self.table_body.grid(row=1, column=0, sticky="nsew")

        # Configure table body columns with FIXED widths (same as header)
        self.table_body.grid_columnconfigure(0, weight=0, minsize=60)  # No.
        self.table_body.grid_columnconfigure(1, weight=0, minsize=150)  # Username
        self.table_body.grid_columnconfigure(2, weight=1, minsize=180)  # Full Name
        self.table_body.grid_columnconfigure(3, weight=0, minsize=100)  # Role
        self.table_body.grid_columnconfigure(4, weight=0, minsize=100)  # Status
        self.table_body.grid_columnconfigure(5, weight=0, minsize=200)  # Actions

        # Pagination section
        pagination_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        pagination_frame.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 18))

        # Pagination info (left)
        self.pagination_info = ctk.CTkLabel(
            pagination_frame,
            text="Loading users...",
            font=("Segoe UI", 10),
            text_color=("gray40", "gray75"),
        )
        self.pagination_info.pack(side="left")

        # Navigation buttons (right)
        nav_frame = ctk.CTkFrame(pagination_frame, fg_color="transparent")
        nav_frame.pack(side="right")

        self.prev_btn = ctk.CTkButton(
            nav_frame,
            text="← Previous",
            command=self._prev_page,
            width=90,
            height=28,
            font=("Segoe UI", 9),
            fg_color=("gray20", "gray30"),
            state="disabled",
        )
        self.prev_btn.pack(side="left", padx=(0, 8))

        self.page_label = ctk.CTkLabel(
            nav_frame,
            text="Page 1 of 1",
            font=("Segoe UI", 10),
        )
        self.page_label.pack(side="left", padx=(0, 8))

        self.next_btn = ctk.CTkButton(
            nav_frame,
            text="Next →",
            command=self._next_page,
            width=90,
            height=28,
            font=("Segoe UI", 9),
            fg_color=("gray20", "gray30"),
            state="disabled",
        )
        self.next_btn.pack(side="left")

        # Load initial data
        self._refresh_users()


# =============================================================================
# USER FORM DIALOG (Add/Edit)
# =============================================================================


class UserFormDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing a user.

    Follows the same styling patterns as report_menu.py popup dialogs.
    """

    def __init__(
        self,
        parent,
        controller,
        mode: str = "add",
        user_data: Dict[str, Any] = None,
        on_save: Callable = None,
    ):
        super().__init__(parent)

        self.controller = controller
        self.mode = mode
        self.user_data = user_data or {}
        self.on_save = on_save

        # Window configuration
        title = (
            "Add New User"
            if mode == "add"
            else f"Edit User: {user_data.get('username', '')}"
        )
        self.title(title)
        self.geometry("450x620")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 550) // 2
        self.geometry(f"+{x}+{y}")

        self._create_form()

        # Focus first field after a short delay
        self.after(100, self._focus_first_field)

    def _focus_first_field(self) -> None:
        """Focus the first input field."""
        if self.mode == "add" and hasattr(self, "username_entry"):
            self.username_entry.focus()
        elif hasattr(self, "fullname_entry"):
            self.fullname_entry.focus()

    def _create_form(self) -> None:
        """Build the form UI."""
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=24)

        # Title (same style as report_menu.py popup)
        title_text = "Create New User" if self.mode == "add" else "Edit User Details"
        title = ctk.CTkLabel(
            container,
            text=title_text,
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(0, 20))

        # Form fields frame
        form_frame = ctk.CTkFrame(container, fg_color="transparent")
        form_frame.pack(fill="x", expand=True)

        # Username (only for add mode)
        if self.mode == "add":
            username_label = ctk.CTkLabel(
                form_frame,
                text="Username:",
                font=("Segoe UI", 11, "bold"),
                anchor="w",
            )
            username_label.pack(fill="x", pady=(0, 4))

            self.username_entry = ctk.CTkEntry(
                form_frame,
                height=36,
                font=("Segoe UI", 11),
                placeholder_text="Enter username",
            )
            self.username_entry.pack(fill="x", pady=(0, 16))

        # Full Name
        fullname_label = ctk.CTkLabel(
            form_frame,
            text="Full Name:",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        fullname_label.pack(fill="x", pady=(0, 4))

        self.fullname_entry = ctk.CTkEntry(
            form_frame,
            height=36,
            font=("Segoe UI", 11),
            placeholder_text="Enter full name",
        )
        self.fullname_entry.pack(fill="x", pady=(0, 16))

        # Pre-fill for edit mode
        if self.mode == "edit":
            self.fullname_entry.insert(0, self.user_data.get("full_name", ""))

        # Role dropdown
        role_label = ctk.CTkLabel(
            form_frame,
            text="Role:",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        role_label.pack(fill="x", pady=(0, 4))

        self.role_var = ctk.StringVar(
            value=self.user_data.get("role", RoleRules.DEFAULT_ROLE)
        )
        self.role_dropdown = ctk.CTkComboBox(
            form_frame,
            values=RoleRules.VALID_ROLES,
            variable=self.role_var,
            height=36,
            font=("Segoe UI", 11),
            state="readonly",
        )
        self.role_dropdown.pack(fill="x", pady=(0, 16))

        # Password section
        if self.mode == "add":
            # Required password fields for new user
            password_label = ctk.CTkLabel(
                form_frame,
                text="Password:",
                font=("Segoe UI", 11, "bold"),
                anchor="w",
            )
            password_label.pack(fill="x", pady=(0, 4))

            self.password_entry = ctk.CTkEntry(
                form_frame,
                height=36,
                font=("Segoe UI", 11),
                placeholder_text="Enter password",
                show="•",
            )
            self.password_entry.pack(fill="x", pady=(0, 16))

            confirm_label = ctk.CTkLabel(
                form_frame,
                text="Confirm Password:",
                font=("Segoe UI", 11, "bold"),
                anchor="w",
            )
            confirm_label.pack(fill="x", pady=(0, 4))

            self.confirm_entry = ctk.CTkEntry(
                form_frame,
                height=36,
                font=("Segoe UI", 11),
                placeholder_text="Confirm password",
                show="•",
            )
            self.confirm_entry.pack(fill="x", pady=(0, 16))
        else:
            # Optional password reset for edit mode
            self.reset_password_var = ctk.BooleanVar(value=False)
            reset_check = ctk.CTkCheckBox(
                form_frame,
                text="Reset Password",
                variable=self.reset_password_var,
                font=("Segoe UI", 11),
                command=self._toggle_password_fields,
            )
            reset_check.pack(anchor="w", pady=(8, 8))

            # Password fields container (hidden by default)
            self.password_frame = ctk.CTkFrame(form_frame, fg_color="transparent")

            password_label = ctk.CTkLabel(
                self.password_frame,
                text="New Password:",
                font=("Segoe UI", 11, "bold"),
                anchor="w",
            )
            password_label.pack(fill="x", pady=(0, 4))

            self.password_entry = ctk.CTkEntry(
                self.password_frame,
                height=36,
                font=("Segoe UI", 11),
                placeholder_text="Enter new password",
                show="•",
            )
            self.password_entry.pack(fill="x", pady=(0, 12))

            confirm_label = ctk.CTkLabel(
                self.password_frame,
                text="Confirm New Password:",
                font=("Segoe UI", 11, "bold"),
                anchor="w",
            )
            confirm_label.pack(fill="x", pady=(0, 4))

            self.confirm_entry = ctk.CTkEntry(
                self.password_frame,
                height=36,
                font=("Segoe UI", 11),
                placeholder_text="Confirm new password",
                show="•",
            )
            self.confirm_entry.pack(fill="x")

        # Buttons - FIXED SIZES
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(20, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            width=140,  # Increased width
            height=38,  # Increased height
            font=("Segoe UI", 11, "bold"),  # Larger font
            fg_color="transparent",
            text_color=("gray20", "gray90"),
            hover_color=("gray85", "gray30"),
            border_width=1,
            border_color=("gray60", "gray50"),
        )
        cancel_btn.pack(side="left")

        save_text = "Create User" if self.mode == "add" else "Save Changes"
        save_btn = ctk.CTkButton(
            btn_frame,
            text=save_text,
            command=self._save,
            width=160,  # Increased width
            height=38,  # Increased height
            font=("Segoe UI", 11, "bold"),  # Larger font
        )
        save_btn.pack(side="right")

    def _toggle_password_fields(self) -> None:
        """Show/hide password fields based on checkbox."""
        if self.reset_password_var.get():
            self.password_frame.pack(fill="x", pady=(8, 0))
        else:
            self.password_frame.pack_forget()

    def _save(self) -> None:
        """Validate and save the form."""
        # Get values
        full_name = self.fullname_entry.get().strip()
        role = self.role_var.get()

        # Validate full name
        error = get_fullname_validation_error(full_name)
        if error:
            messagebox.showwarning("Invalid Full Name", error)
            self.fullname_entry.focus()
            return

        if self.mode == "add":
            # Validate username
            username = self.username_entry.get().strip()
            error = get_username_validation_error(username)
            if error:
                messagebox.showwarning("Invalid Username", error)
                self.username_entry.focus()
                return

            # Validate password
            password = self.password_entry.get()
            error = get_password_validation_error(password)
            if error:
                messagebox.showwarning("Invalid Password", error)
                self.password_entry.focus()
                return

            # Check password match
            confirm = self.confirm_entry.get()
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match.")
                self.confirm_entry.delete(0, "end")
                self.confirm_entry.focus()
                return

            # Create user
            result = self.controller.create_new_user(
                username=username, full_name=full_name, password=password, role=role
            )
        else:
            # Edit mode
            new_password = None

            # Check if password reset is requested
            if self.reset_password_var.get():
                password = self.password_entry.get()
                error = get_password_validation_error(password)
                if error:
                    messagebox.showwarning("Invalid Password", error)
                    self.password_entry.focus()
                    return

                confirm = self.confirm_entry.get()
                if password != confirm:
                    messagebox.showerror("Error", "Passwords do not match.")
                    self.confirm_entry.delete(0, "end")
                    self.confirm_entry.focus()
                    return

                new_password = password

            # Update user
            result = self.controller.update_user(
                user_id=self.user_data["id"],
                full_name=full_name,
                role=role,
                new_password=new_password,
            )

        # Handle result
        if result.get("success"):
            messagebox.showinfo("Success", result["message"])
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", result.get("message", "Operation failed"))
