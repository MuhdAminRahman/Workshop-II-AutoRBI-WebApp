"""User Profile view for AutoRBI application."""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import Callable

from AutoRBI_Database.validation_rules import (
    get_fullname_validation_error,
    get_email_validation_error,
    get_password_validation_error,
)


class ProfileView:
    """Handles the User Profile interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller

    def show(self) -> None:
        """Display the Profile interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Refresh profile data from database
        self.controller.refresh_profile()

        # Get current user data from controller
        user = self.controller.current_user

        # Extract user info with fallbacks
        full_name = user.get("full_name") or user.get("username") or "Unknown User"
        username = user.get("username") or "unknown"
        role = user.get("role") or "User"
        email = user.get("email") or "Not set"

        # Format member since date
        member_since = user.get("created_at")
        if member_since:
            if isinstance(member_since, datetime):
                member_since = member_since.strftime("%b %Y")
            elif isinstance(member_since, str):
                try:
                    dt = datetime.fromisoformat(member_since)
                    member_since = dt.strftime("%b %Y")
                except:
                    member_since = "N/A"
        else:
            member_since = "N/A"

        # Root frame
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
            text="← Back",
            command=self.controller.show_main_menu,
            width=120,
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
            text="User Profile",
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

        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(expand=True, fill="both", padx=24, pady=24)

        # Avatar/Profile section
        profile_section = ctk.CTkFrame(scroll, fg_color="transparent")
        profile_section.pack(fill="x", pady=(0, 24))

        # Avatar placeholder
        avatar_frame = ctk.CTkFrame(
            profile_section,
            width=120,
            height=120,
            corner_radius=60,
            fg_color=("gray80", "gray30"),
        )
        avatar_frame.pack(pady=(0, 16))

        initials = self._get_initials(full_name)

        avatar_label = ctk.CTkLabel(
            avatar_frame,
            text=initials,
            font=("Segoe UI", 36, "bold"),
            text_color=("gray40", "gray70"),
        )
        avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        # User info - Full name
        self.fullname_label = ctk.CTkLabel(
            profile_section,
            text=full_name,
            font=("Segoe UI", 20, "bold"),
        )
        self.fullname_label.pack(pady=(0, 4))

        # Role badge
        role_color = "#3498db" if role == "Admin" else "#27ae60"
        role_label = ctk.CTkLabel(
            profile_section,
            text=role,
            font=("Segoe UI", 12, "bold"),
            text_color=role_color,
        )
        role_label.pack()

        # Profile details
        details_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        details_frame.pack(fill="x", pady=(0, 24))

        section_title = ctk.CTkLabel(
            details_frame,
            text="Profile Information",
            font=("Segoe UI", 16, "bold"),
        )
        section_title.pack(anchor="w", pady=(0, 16))

        # Store labels for updating after edit
        self.field_labels = {}

        # Profile fields
        fields = [
            ("Username", username),
            ("Full Name", full_name),
            ("Email", email),
            ("Role", role),
            ("Member Since", member_since),
        ]

        for field_name, field_value in fields:
            field_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=(0, 12))

            label = ctk.CTkLabel(
                field_frame,
                text=f"{field_name}:",
                font=("Segoe UI", 11, "bold"),
                width=120,
                anchor="w",
            )
            label.pack(side="left", padx=(0, 12))

            value_label = ctk.CTkLabel(
                field_frame,
                text=field_value,
                font=("Segoe UI", 11),
                text_color=("gray40", "gray80"),
            )
            value_label.pack(side="left")

            # Store reference for updating
            self.field_labels[field_name] = value_label

        # Buttons frame
        buttons_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(20, 0))

        # Edit Profile button
        edit_btn = ctk.CTkButton(
            buttons_frame,
            text="Edit Profile",
            command=self._show_edit_dialog,
            width=150,
            height=40,
            font=("Segoe UI", 12, "bold"),
        )
        edit_btn.pack(side="left", padx=(0, 10))

        # Change Password button
        password_btn = ctk.CTkButton(
            buttons_frame,
            text="Change Password",
            command=self._show_password_dialog,
            width=150,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color=("gray20", "gray30"),
        )
        password_btn.pack(side="left")

    def _get_initials(self, name: str) -> str:
        """Get initials from full name."""
        if not name:
            return "?"

        parts = name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif len(parts) == 1:
            return parts[0][0].upper()
        return "?"

    def _show_edit_dialog(self) -> None:
        """Show edit profile dialog."""
        EditProfileDialog(
            parent=self.parent,
            controller=self.controller,
            on_save=self._refresh_display,
        )

    def _show_password_dialog(self) -> None:
        """Show change password dialog."""
        ChangePasswordDialog(parent=self.parent, controller=self.controller)

    def _refresh_display(self) -> None:
        """Refresh the profile display after edit."""
        # Simply reload the view
        self.show()


# =============================================================================
# EDIT PROFILE DIALOG
# =============================================================================


class EditProfileDialog(ctk.CTkToplevel):
    """Modal dialog for editing profile information."""

    def __init__(self, parent, controller, on_save: Callable = None):
        super().__init__(parent)

        self.controller = controller
        self.on_save = on_save

        # Get current user data
        self.user = controller.current_user

        # Window configuration
        self.title("Edit Profile")
        self.geometry("420x460")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 320) // 2
        self.geometry(f"+{x}+{y}")

        self._create_form()

        # Focus first field
        self.after(100, lambda: self.fullname_entry.focus())

    def _create_form(self) -> None:
        """Build the form UI."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=24)

        # Title
        title = ctk.CTkLabel(
            container,
            text="Edit Profile",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(0, 20))

        # Form frame
        form_frame = ctk.CTkFrame(container, fg_color="transparent")
        form_frame.pack(fill="x")

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
        )
        self.fullname_entry.pack(fill="x", pady=(0, 16))
        self.fullname_entry.insert(0, self.user.get("full_name", ""))

        # Email
        email_label = ctk.CTkLabel(
            form_frame,
            text="Email:",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        email_label.pack(fill="x", pady=(0, 4))

        self.email_entry = ctk.CTkEntry(
            form_frame,
            height=36,
            font=("Segoe UI", 11),
        )
        self.email_entry.pack(fill="x", pady=(0, 16))
        self.email_entry.insert(0, self.user.get("email", ""))

        # Info label
        info_label = ctk.CTkLabel(
            form_frame,
            text="Note: Username and Role cannot be changed.",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
        )
        info_label.pack(anchor="w")

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(20, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            width=100,
            height=36,
            font=("Segoe UI", 10, "bold"),
            fg_color="transparent",
            text_color=("gray20", "gray90"),
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Changes",
            command=self._save,
            width=120,
            height=36,
            font=("Segoe UI", 10, "bold"),
        )
        save_btn.pack(side="right")

    def _save(self) -> None:
        """Validate and save changes."""
        full_name = self.fullname_entry.get().strip()
        email = self.email_entry.get().strip()

        # Validate full name
        error = get_fullname_validation_error(full_name)
        if error:
            messagebox.showwarning("Invalid Full Name", error)
            self.fullname_entry.focus()
            return

        # Validate email
        error = get_email_validation_error(email)
        if error:
            messagebox.showwarning("Invalid Email", error)
            self.email_entry.focus()
            return

        # Check if anything changed
        if full_name == self.user.get("full_name") and email == self.user.get("email"):
            messagebox.showinfo("No Changes", "No changes were made.")
            self.destroy()
            return

        # Call controller to update
        result = self.controller.update_profile(full_name=full_name, email=email)

        if result.get("success"):
            messagebox.showinfo("Success", result["message"])
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", result.get("message", "Update failed"))


# =============================================================================
# CHANGE PASSWORD DIALOG
# =============================================================================


class ChangePasswordDialog(ctk.CTkToplevel):
    """Modal dialog for changing password."""

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        # Window configuration
        self.title("Change Password")
        self.geometry("420x460")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 380) // 2
        self.geometry(f"+{x}+{y}")

        self._create_form()

        # Focus first field
        self.after(100, lambda: self.current_entry.focus())

    def _create_form(self) -> None:
        """Build the form UI."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=24)

        # Title
        title = ctk.CTkLabel(
            container,
            text="Change Password",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(0, 20))

        # Form frame
        form_frame = ctk.CTkFrame(container, fg_color="transparent")
        form_frame.pack(fill="x")

        # Current Password
        current_label = ctk.CTkLabel(
            form_frame,
            text="Current Password:",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        current_label.pack(fill="x", pady=(0, 4))

        self.current_entry = ctk.CTkEntry(
            form_frame,
            height=36,
            font=("Segoe UI", 11),
            show="•",
        )
        self.current_entry.pack(fill="x", pady=(0, 16))

        # New Password
        new_label = ctk.CTkLabel(
            form_frame,
            text="New Password:",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        new_label.pack(fill="x", pady=(0, 4))

        self.new_entry = ctk.CTkEntry(
            form_frame,
            height=36,
            font=("Segoe UI", 11),
            show="•",
        )
        self.new_entry.pack(fill="x", pady=(0, 16))

        # Confirm New Password
        confirm_label = ctk.CTkLabel(
            form_frame,
            text="Confirm New Password:",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        confirm_label.pack(fill="x", pady=(0, 4))

        self.confirm_entry = ctk.CTkEntry(
            form_frame,
            height=36,
            font=("Segoe UI", 11),
            show="•",
        )
        self.confirm_entry.pack(fill="x", pady=(0, 16))

        # Password requirements hint
        hint_label = ctk.CTkLabel(
            form_frame,
            text="Password must be at least 6 characters.",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
        )
        hint_label.pack(anchor="w")

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(20, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            width=100,
            height=36,
            font=("Segoe UI", 10, "bold"),
            fg_color="transparent",
            text_color=("gray20", "gray90"),
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Change Password",
            command=self._save,
            width=140,
            height=36,
            font=("Segoe UI", 10, "bold"),
        )
        save_btn.pack(side="right")

    def _save(self) -> None:
        """Validate and save new password."""
        current_password = self.current_entry.get()
        new_password = self.new_entry.get()
        confirm_password = self.confirm_entry.get()

        # Validate current password is provided
        if not current_password:
            messagebox.showwarning("Required", "Please enter your current password.")
            self.current_entry.focus()
            return

        # Validate new password
        error = get_password_validation_error(new_password)
        if error:
            messagebox.showwarning("Invalid Password", error)
            self.new_entry.focus()
            return

        # Check passwords match
        if new_password != confirm_password:
            messagebox.showerror("Error", "New passwords do not match.")
            self.confirm_entry.delete(0, "end")
            self.confirm_entry.focus()
            return

        # Call controller to change password
        result = self.controller.change_password(
            current_password=current_password, new_password=new_password
        )

        if result.get("success"):
            messagebox.showinfo("Success", result["message"])
            self.destroy()
        else:
            error_type = result.get("error_type")
            if error_type == "wrong_password":
                messagebox.showerror("Error", "Current password is incorrect.")
                self.current_entry.delete(0, "end")
                self.current_entry.focus()
            else:
                messagebox.showerror(
                    "Error", result.get("message", "Password change failed")
                )
