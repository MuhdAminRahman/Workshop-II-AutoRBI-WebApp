"""Login view for AutoRBI application (CustomTkinter)."""

from tkinter import messagebox
import os
from typing import Optional

from PIL import Image
import customtkinter as ctk


# Import centralized validation rules - same rules used by backend
# This ensures UI validation matches backend validation exactly
from AutoRBI_Database.validation_rules import (
    UsernameRules,
    PasswordRules,
    get_username_validation_error,
    get_password_validation_error,
)


class LoginView:
    """Handles the login interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self._logo_image: Optional[ctk.CTkImage] = self._load_logo()

    def _load_logo(self) -> Optional[ctk.CTkImage]:
        """Load the iPETRO logo from disk if available."""
        try:
            base_dir = os.path.dirname(__file__)
            logo_path = os.path.join(base_dir, "ipetro.png")
            image = Image.open(logo_path)
            # Adjust size to suit the header
            return ctk.CTkImage(image, size=(160, 34))
        except Exception:
            # Fail gracefully if the image cannot be loaded
            return None

    def show(self) -> None:
        """Display the login interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Background container with gradient-like effect
        bg_frame = ctk.CTkFrame(
            self.parent,
            corner_radius=0,
            fg_color=("gray95", "gray10"),
        )
        bg_frame.pack(expand=True, fill="both")

        # Center container for glass card
        center_container = ctk.CTkFrame(bg_frame, fg_color="transparent")
        center_container.pack(expand=True, fill="both")
        center_container.grid_rowconfigure(0, weight=1)
        center_container.grid_columnconfigure(0, weight=1)

        # Glass morphism card - SQUARE shape with blur effect
        glass_card = ctk.CTkFrame(
            center_container,
            corner_radius=20,
            border_width=2,
            width=480,  # Square width
            height=480,  # Square height (same as width for perfect square)
            # Glass effect: light colors for light mode, darker semi-transparent for dark mode
            fg_color=("#F0F0F0", "#2B2B2B"),
            border_color=("#E0E0E0", "#404040"),
        )
        glass_card.grid(row=0, column=0, padx=80, pady=60, sticky="")
        # Prevent the card from resizing - maintain square shape
        glass_card.grid_propagate(False)
        glass_card.grid_rowconfigure(0, weight=1)
        glass_card.grid_columnconfigure(0, weight=1)

        # Content inside glass card
        content = ctk.CTkFrame(glass_card, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew", padx=50, pady=50)

        # Logo centered
        if self._logo_image is not None:
            logo_label = ctk.CTkLabel(
                content,
                text="",
                image=self._logo_image,
            )
            logo_label.pack(pady=(0, 12))

        subtitle_label = ctk.CTkLabel(
            content,
            text="Welcome back. Please sign in to continue.",
            font=("Segoe UI", 13),
            text_color=("gray40", "gray75"),
        )
        subtitle_label.pack(pady=(0, 32))

        # Fields container
        fields = ctk.CTkFrame(content, fg_color="transparent")
        fields.pack(fill="both", expand=True)

        # Username
        username_label = ctk.CTkLabel(
            fields,
            text="Username",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        username_label.pack(anchor="w", pady=(0, 8))

        username_entry = ctk.CTkEntry(
            fields,
            placeholder_text="Enter your username",
            font=("Segoe UI", 12),
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        username_entry.pack(fill="x", pady=(0, 20))
        username_entry.focus()

        # Password
        password_label = ctk.CTkLabel(
            fields,
            text="Password",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        password_label.pack(anchor="w", pady=(0, 8))

        password_entry = ctk.CTkEntry(
            fields,
            placeholder_text="Enter your password",
            font=("Segoe UI", 12),
            show="*",
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        password_entry.pack(fill="x", pady=(0, 24))

        # Login behaviour
        def handle_login() -> None:
            """
            Handle login button click with comprehensive error handling.

            This method implements:
            - 6. Input Validation: UI-level validation before backend call
            - 7. User-Friendly Messages: Context-aware error messages
            - 8. Error Context: Different handling based on error_type

            Flow:
            1. Validate inputs at UI level (quick feedback)
            2. Call backend authentication
            3. Handle response based on error_type
            4. Show appropriate messages and actions
            """
            # Get input values
            username = username_entry.get()
            password = password_entry.get()

            # ========================================================================
            # LAYER 1: UI-LEVEL VALIDATION (Quick feedback, no backend call needed)
            # Using centralized rules from validation_rules.py
            # ========================================================================

            # Validate username using centralized validation
            # get_username_validation_error returns error message or None if valid
            username_error = get_username_validation_error(username)
            if username_error:
                messagebox.showwarning("Invalid Username", username_error)
                username_entry.focus()
                username_entry.select_range(0, "end")
                return

            # Validate password using centralized validation
            password_error = get_password_validation_error(password)
            if password_error:
                messagebox.showwarning("Invalid Password", password_error)
                password_entry.focus()
                return

            # ========================================================================
            # LAYER 2: BACKEND AUTHENTICATION
            # ========================================================================

            try:
                # Clean inputs before sending to backend
                username_clean = username.strip()

                # Call backend authentication
                auth_result = self.controller.authenticate_user(
                    username_clean, password
                )

                # ====================================================================
                # LAYER 3: HANDLE RESPONSE BASED ON ERROR TYPE
                # ====================================================================

                if auth_result.get("success"):
                    # SUCCESS - Proceed to main menu

                    self.controller.available_works = self.controller.getAssignedWorks()

                    self.controller.current_work = (
                        self.controller.available_works[0]
                        if self.controller.available_works
                        else None
                    )

                    self.controller.show_main_menu()

                else:
                    # FAILURE - Handle based on error_type
                    error_type = auth_result.get("error_type", "unknown")
                    message = auth_result.get("message", "Login failed")

                    # 8. ERROR CONTEXT - Different handling for different error types

                    if error_type == "authentication":
                        # Wrong credentials - simple retry
                        # 7. USER-FRIENDLY MESSAGES
                        messagebox.showerror("Login Failed", message)

                        # Clear password field for security
                        password_entry.delete(0, "end")

                        # Focus on password field for retry
                        password_entry.focus()

                    elif error_type == "account_status":
                        # Account inactive/locked - needs admin intervention
                        # 7. USER-FRIENDLY MESSAGES - More detailed with action
                        messagebox.showerror(
                            "Account Issue",
                            f"{message}\n\n"
                            "Please contact your system administrator for assistance.",
                        )

                    elif error_type == "validation":
                        # Input validation error
                        messagebox.showwarning("Invalid Input", message)

                        # Focus on appropriate field
                        field = auth_result.get("field", "username")
                        if field == "username":
                            username_entry.focus()
                            username_entry.select_range(0, "end")
                        else:
                            password_entry.focus()

                    elif error_type == "system":
                        # System error (database, network, etc.)
                        # 7. USER-FRIENDLY MESSAGES - Explain it's temporary
                        retry_delay = auth_result.get("retry_delay", 0)

                        if retry_delay > 0:
                            # Suggest retry with delay
                            response = messagebox.askretrycancel(
                                "Service Unavailable",
                                f"{message}\n\n"
                                f"Would you like to retry?\n"
                                f"(Waiting {retry_delay} seconds is recommended)",
                            )

                            if response:  # User clicked Retry
                                # Could add a delay here if desired
                                # self.after(retry_delay * 1000, lambda: handle_login())
                                pass  # Or just let them retry immediately
                        else:
                            # No specific delay suggested
                            messagebox.showerror(
                                "Service Error",
                                f"{message}\n\n"
                                "Please try again in a few moments.\n"
                                "If this problem persists, contact support.",
                            )

                    else:
                        # Unknown error type - generic handling
                        messagebox.showerror(
                            "Login Error",
                            f"{message}\n\n"
                            "Please try again or contact support if this continues.",
                        )

            except Exception as e:
                # Catch-all for any unexpected UI-level errors
                # This should rarely happen if backend is properly handling errors
                messagebox.showerror(
                    "Unexpected Error",
                    "An unexpected error occurred.\n"
                    "Please restart the application or contact support.",
                )
                # Could log this error if you have UI-level logging
                print(f"UI Error in login: {e}")  # Basic logging

        # Primary button with glass effect
        login_btn = ctk.CTkButton(
            fields,
            text="Sign in",
            command=handle_login,
            height=46,
            font=("Segoe UI", 13, "bold"),
            corner_radius=12,
            border_width=1,
            border_color=("#6496FF", "#6496FF"),
        )
        login_btn.pack(fill="x", pady=(0, 12))

        # Secondary action
        register_btn = ctk.CTkButton(
            fields,
            text="Don't have an account? Create one",
            command=self.controller.show_registration,
            height=36,
            font=("Segoe UI", 11),
            fg_color="transparent",
            text_color=("gray40", "gray70"),
            hover_color=("#E8E8E8", "#404040"),
            border_width=0,
        )
        register_btn.pack(fill="x", pady=(0, 0))

        # Bind Enter key to login
        password_entry.bind("<Return>", lambda _event: handle_login())
