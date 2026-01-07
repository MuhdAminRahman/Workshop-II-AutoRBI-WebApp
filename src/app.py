""" "Main application class for AutoRBI."""

from tkinter import messagebox
from typing import Dict

import customtkinter as ctk

import sys
import os

# Absolute path to the folder where *this* file (app.py) lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the AutoRBI_Database folder
DB_ROOT = os.path.join(BASE_DIR, "AutoRBI_Database")

# Add it to sys.path if it's not already there
if DB_ROOT not in sys.path:
    sys.path.append(DB_ROOT)

import styles

from AutoRBI_Database.database.session import SessionLocal
from AutoRBI_Database.services.work_service import get_assigned_works, get_work_details
from AutoRBI_Database.database.models.equipment import Equipment as DBEquipment
from AutoRBI_Database.database.models.correction_log import CorrectionLog

from UserInterface.views import (
    AnalyticsView,
    LoginView,
    MainMenuView,
    NewWorkView,
    RegistrationView,
    ReportMenuView,
    WorkHistoryView,
    SettingsView,
    ProfileView,
    UserManagementView,
)
from UserInterface.components import NotificationSystem, LoadingOverlay

from AutoRBI_Database.services.auth_service import (
    authenticate_user as auth_login,
    register_user as auth_register,
)

from AutoRBI_Database.exceptions import (
    InvalidPasswordError,
    InactiveAccountError,
    AccountAlreadyExistsError,
    ValidationError,
    DatabaseError,
)

from AutoRBI_Database.messages import AuthMessages, RegistrationMessages, ErrorTypes
from AutoRBI_Database.logging_config import get_logger
from AutoRBI_Database.services import admin_service
from AutoRBI_Database.services import profile_service

# Initialize logger
logger = get_logger(__name__)


class AutoRBIApp(ctk.CTk):
    """Main window coordinating all AutoRBI views (CustomTkinter)."""

    def __init__(self) -> None:
        super().__init__()

        # Global CustomTkinter look & feel
        styles.configure_styles()

        self.title("AutoRBI")
        self.geometry("1100x720")
        self.minsize(1000, 680)

        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x_pos = (self.winfo_screenwidth() // 2) - (width // 2)
        y_pos = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

        # Initialize notification system and loading overlay
        self.notification_system = NotificationSystem(self)
        self.loading_overlay = LoadingOverlay(self)

        # Current user info
        self.current_user = None
        self.available_works = None
        self.current_work = None

        # Initialize views
        self.login_view = LoginView(self, self)
        self.registration_view = RegistrationView(self, self)
        self.main_menu_view = MainMenuView(self, self)
        self.new_work_view = None
        self.report_menu_view = ReportMenuView(self, self)
        self.work_history_view = WorkHistoryView(self, self)
        self.analytics_view = None
        self.settings_view = SettingsView(self, self)
        self.profile_view = ProfileView(self, self)

        # Admin views
        self.user_management_view = UserManagementView(self, self)

        # TEMP current user info (your code had this stub)
        self.current_user = {
            "username": "John Doe",
            "role": "Engineer",
            "email": "john.doe@ipetro.com",
            "group": None,  # Employee group/department set after login
            # NOTE: In real login, you set "id" from DB user.user_id
            # This stub does NOT include id/user_id.
        }

        # Current work context in New Work view
        self.current_work = None  # Currently selected work assignment
        self.available_works = []  # Works assigned to employee's group

        # Show login screen initially
        self.show_login()

    # ========================================================================
    # AUTH METHODS
    # ========================================================================

    def authenticate_user(self, username: str, password: str) -> dict:
        """
        Authenticate user with proper resource cleanup and error handling.
        """
        logger.info(f"Controller: Authentication request for username: {username}")

        db = SessionLocal()
        try:
            result = auth_login(db, username, password)

            if result["success"]:
                user = result["user"]
                try:
                    self.current_user = {
                        "id": user.user_id,
                        "username": user.username,
                        "full_name": getattr(user, "full_name", None),
                        "role": getattr(user, "role", None),
                        "email": getattr(user, "email", None),
                        "created_at": getattr(user, "created_at", None),
                    }
                    logger.info(
                        f"Controller: User session created for: {user.username}"
                    )
                except AttributeError as e:
                    logger.error(
                        f"Controller: Error extracting user attributes: {e}",
                        exc_info=True,
                    )
                    return {
                        "success": False,
                        "message": "Error processing user data. Please try again.",
                        "user": None,
                        "error_type": "system",
                    }

            if result["success"]:
                logger.info(f"Controller: Authentication successful for: {username}")
            else:
                logger.info(f"Controller: Authentication failed for: {username}")

            return result

        except Exception as e:
            logger.error(
                f"Controller: Unexpected error during authentication: {e}",
                exc_info=True,
            )
            return {
                "success": False,
                "message": "An unexpected error occurred. Please try again.",
                "user": None,
                "error_type": "system",
            }
        finally:
            try:
                db.close()
                logger.debug("Controller: Database session closed")
            except Exception as e:
                logger.error(
                    f"Controller: Error closing database session: {e}",
                    exc_info=True,
                )

    def register_user(self, full_name: str, username: str, password: str) -> dict:
        """
        Register new user with proper resource cleanup and error handling.
        """
        logger.info(f"Controller: Registration request for username: {username}")

        db = SessionLocal()
        try:
            result = auth_register(db, full_name, username, password)

            if result["success"]:
                logger.info(f"Controller: Registration successful for: {username}")
            else:
                logger.info(
                    f"Controller: Registration failed for: {username} - "
                    f"{result.get('error_type', 'unknown')}"
                )
            return result

        except Exception as e:
            logger.error(
                f"Controller: Unexpected error during registration: {e}",
                exc_info=True,
            )
            return {
                "success": False,
                "message": (
                    "An unexpected error occurred during registration. "
                    "Please try again."
                ),
                "user": None,
                "error_type": "system",
            }
        finally:
            try:
                db.close()
                logger.debug("Controller: Database session closed")
            except Exception as e:
                logger.error(
                    f"Controller: Error closing database session: {e}",
                    exc_info=True,
                )

    # ========================================================================
    # ADMIN METHODS
    # ========================================================================

    def get_users_list(
        self,
        status_filter: str = None,
        role_filter: str = None,
        search_query: str = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        logger.info(f"Controller: Fetching users list (page {page})")

        db = SessionLocal()
        try:
            result = admin_service.get_users(
                db=db,
                current_user=self.current_user,
                status_filter=status_filter,
                role_filter=role_filter,
                search_query=search_query,
                page=page,
                per_page=per_page,
            )
            return result
        except Exception as e:
            logger.error(f"Controller: Error fetching users: {e}")
            return {
                "success": False,
                "message": "Unable to fetch users.",
                "error_type": "system",
            }
        finally:
            db.close()

    def toggle_user_status(self, user_id: int) -> dict:
        logger.info(f"Controller: Toggling status for user ID {user_id}")

        db = SessionLocal()
        try:
            result = admin_service.toggle_user_status(
                db=db, current_user=self.current_user, target_user_id=user_id
            )
            return result
        except Exception as e:
            logger.error(f"Controller: Error toggling user status: {e}")
            return {
                "success": False,
                "message": "Operation failed.",
                "error_type": "system",
            }
        finally:
            db.close()

    def update_user(
        self,
        user_id: int,
        full_name: str = None,
        role: str = None,
        new_password: str = None,
    ) -> dict:
        logger.info(f"Controller: Updating user ID {user_id}")

        db = SessionLocal()
        try:
            result = admin_service.modify_user(
                db=db,
                current_user=self.current_user,
                target_user_id=user_id,
                full_name=full_name,
                role=role,
                new_password=new_password,
            )
            return result
        except Exception as e:
            logger.error(f"Controller: Error updating user: {e}")
            return {
                "success": False,
                "message": "Operation failed.",
                "error_type": "system",
            }
        finally:
            db.close()

    def create_new_user(
        self, username: str, full_name: str, password: str, role: str = "Engineer"
    ) -> dict:
        logger.info(f"Controller: Creating new user '{username}'")

        db = SessionLocal()
        try:
            result = admin_service.add_user(
                db=db,
                current_user=self.current_user,
                username=username,
                full_name=full_name,
                password=password,
                role=role,
            )
            return result
        except Exception as e:
            logger.error(f"Controller: Error creating user: {e}")
            return {
                "success": False,
                "message": "Operation failed.",
                "error_type": "system",
            }
        finally:
            db.close()

    # ========================================================================
    # PROFILE METHODS
    # ========================================================================

    def update_profile(self, full_name: str = None, email: str = None) -> dict:
        logger.info(
            f"Controller: Updating profile for user ID {self.current_user.get('id')}"
        )

        db = SessionLocal()
        try:
            result = profile_service.update_profile(
                db=db,
                user_id=self.current_user.get("id"),
                full_name=full_name,
                email=email,
            )

            if result.get("success") and result.get("user"):
                user_data = result["user"]
                self.current_user["full_name"] = user_data.get("full_name")
                self.current_user["email"] = user_data.get("email")
                logger.info("Controller: Session data updated with new profile info")

            return result

        except Exception as e:
            logger.error(f"Controller: Error updating profile: {e}")
            return {
                "success": False,
                "message": "Unable to update profile.",
                "error_type": "system",
            }
        finally:
            db.close()

    def change_password(self, current_password: str, new_password: str) -> dict:
        logger.info(
            f"Controller: Changing password for user ID {self.current_user.get('id')}"
        )

        db = SessionLocal()
        try:
            result = profile_service.change_password(
                db=db,
                user_id=self.current_user.get("id"),
                current_password=current_password,
                new_password=new_password,
            )
            return result
        except Exception as e:
            logger.error(f"Controller: Error changing password: {e}")
            return {
                "success": False,
                "message": "Unable to change password.",
                "error_type": "system",
            }
        finally:
            db.close()

    def refresh_profile(self) -> dict:
        logger.info(
            f"Controller: Refreshing profile for user ID {self.current_user.get('id')}"
        )

        db = SessionLocal()
        try:
            result = profile_service.get_profile(
                db=db, user_id=self.current_user.get("id")
            )

            if result.get("success") and result.get("user"):
                user_data = result["user"]
                self.current_user["full_name"] = user_data.get("full_name")
                self.current_user["email"] = user_data.get("email")
                self.current_user["role"] = user_data.get("role")
                self.current_user["created_at"] = user_data.get("created_at")

            return result

        except Exception as e:
            logger.error(f"Controller: Error refreshing profile: {e}")
            return {
                "success": False,
                "message": "Unable to load profile.",
                "error_type": "system",
            }
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Navigation helpers
    # ------------------------------------------------------------------ #

    def show_login(self) -> None:
        """Display the login view."""
        self.login_view.show()

    def show_registration(self) -> None:
        """Display the registration view."""
        self.registration_view.show()

    def show_main_menu(self) -> None:
        """Display the main menu view."""
        self.main_menu_view.show()

    def show_new_work(self) -> None:
        """Display the New Work view."""
        self.available_works = self.getAssignedWorks()
        self.current_work = self.available_works[0] if self.available_works else None
        self.new_work_view = NewWorkView(self, self)
        self.new_work_view.show()

    def show_report_menu(self) -> None:
        """Display the Report Menu view."""
        self.available_works = self.getAssignedWorks()
        self.report_menu_view.show()

    def show_analytics(self) -> None:
        """Display the Analytics Dashboard view."""
        self.available_works = self.getAssignedWorks()
        self.current_work = self.available_works[0] if self.available_works else None
        self.analytics_view = AnalyticsView(self, self)
        self.analytics_view.show()

    def show_settings(self) -> None:
        """Display the Settings view."""
        self.settings_view.show()

    def show_profile(self) -> None:
        """Display the Profile view."""
        self.profile_view.show()

    def logout(self) -> None:
        """Prompt user for logout confirmation and return to login."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.notification_system.clear_all()
            self.show_login()

    def show_notification(
        self, message: str, notification_type: str = "info", duration: int = 5000
    ) -> None:
        """Show a notification."""
        self.notification_system.show_notification(message, notification_type, duration)

    def show_loading(self, message: str = "Loading...", show_progress: bool = False):
        """Show loading overlay."""
        self.loading_overlay.show(message, show_progress)

    def hide_loading(self) -> None:
        """Hide loading overlay."""
        self.loading_overlay.hide()

    def update_loading_progress(self, value: float, message: str = None) -> None:
        """Update loading progress (0.0 to 1.0)."""
        self.loading_overlay.update_progress(value, message)

    def show_user_management(self) -> None:
        """Display the User Management view (admin only)."""
        if self.current_user.get("role") != "Admin":
            messagebox.showerror(
                "Access Denied", "Only administrators can access User Management."
            )
            return
        self.user_management_view.show()

    # ------------------------------------------------------------------ #
    # New Work Methods
    # ------------------------------------------------------------------ #

    def getAssignedWorks(self) -> list[Dict[str, str]]:
        """Get list of works assigned to current user."""
        db = SessionLocal()
        try:
            user_id = self.current_user.get("id")
            works = get_assigned_works(db, user_id)

            work_details = []
            work_list = []

            for work in works:
                work_details.append(get_work_details(db, work.work_id))

            for work in work_details:
                work_list.append(
                    {"work_id": f"{work.work_id}", "work_name": f"{work.work_name}"}
                )

            return work_list
        finally:
            db.close()

    def getWorkDetails(self, work_id: int) -> Dict:
        """Get detailed information about a specific work."""
        db = SessionLocal()
        try:
            workdetails = get_work_details(db, work_id)
            if workdetails:
                return {
                    "work_id": workdetails.work_id,
                    "work_name": workdetails.work_name,
                    "description": workdetails.description,
                    "status": workdetails.status,
                    "created_at": workdetails.created_at,
                }
            return {}
        finally:
            db.close()

    def getWorkProgressStats(self, work_id: int) -> Dict[str, float | int]:
        """
        Get work progress statistics.

        Returns:
            Dictionary with:
                - total_equipment
                - extracted_equipment
                - corrected_equipment
                - completion_percentage
        """
        db = SessionLocal()
        try:
            total = db.query(DBEquipment).filter(DBEquipment.work_id == work_id).count()

            extracted = (
                db.query(DBEquipment)
                .filter(
                    DBEquipment.work_id == work_id,
                    DBEquipment.extracted_date.isnot(None),
                )
                .count()
            )

            corrected_equipment_ids = (
                db.query(CorrectionLog.equipment_id)
                .distinct()
                .join(DBEquipment)
                .filter(DBEquipment.work_id == work_id)
                .all()
            )
            corrected = len(corrected_equipment_ids)

            completion = (extracted / total * 100) if total > 0 else 0

            return {
                "total_equipment": total,
                "extracted_equipment": extracted,
                "corrected_equipment": corrected,
                "completion_percentage": round(completion, 1),
            }

        except Exception as e:
            print(f"Error getting work progress: {e}")
            return {
                "total_equipment": 0,
                "extracted_equipment": 0,
                "corrected_equipment": 0,
                "completion_percentage": 0.0,
            }
        finally:
            db.close()

    # ========================================================================
    # WORK HISTORY METHODS (moved INSIDE AutoRBIApp)
    # ========================================================================

    def show_work_history(self) -> None:
        """Display the work history view and load initial data."""
        logger.info(
            f"Showing work history for user: {self.current_user.get('username')}"
        )

        # Show the view first
        self.work_history_view.show()

        # Load initial data
        self.loading_overlay.show("Loading work history...")
        self.after(100, lambda: self._load_work_history_data(period="all", page=1))

    def _load_work_history_data(self, period: str = "all", page: int = 1) -> None:
        """Load work history data from backend."""
        db = SessionLocal()
        try:
            from AutoRBI_Database.services import work_history_service

            current_user_with_id = {
                "user_id": self.current_user.get("user_id")
                or self.current_user.get("id"),
                "username": self.current_user.get("username"),
                "role": self.current_user.get("role"),
            }

            result = work_history_service.get_work_history(
                db=db,
                current_user=current_user_with_id,
                period=period,
                page=page,
                per_page=20,
            )

            self.loading_overlay.hide()

            if result.get("success"):
                self.work_history_view.load_history(
                    history_items=result["data"],
                    total=result["pagination"]["total"],
                    total_pages=result["pagination"]["total_pages"],
                )
            else:
                self.notification_system.show_notification(
                    message=result.get("message", "Unknown error"),
                    notification_type="error",
                )

        except Exception as e:
            logger.error(f"Error loading work history: {e}", exc_info=True)
            self.loading_overlay.hide()
            self.notification_system.show_notification(
                message="Failed to load work history. Please try again.",
                notification_type="error",
            )
        finally:
            db.close()

    def apply_work_history_filter(self, period: str) -> None:
        """Apply time period filter to work history."""
        logger.info(f"Applying work history filter: {period}")

        self.work_history_view.current_filter = period
        self.work_history_view.current_page = 1

        self.loading_overlay.show(f"Filtering by {period}...")
        self.after(100, lambda: self._load_work_history_data(period=period, page=1))

    def change_history_page(self, page: int) -> None:
        """Navigate to different page in work history."""
        logger.info(f"Changing to work history page: {page}")

        self.work_history_view.current_page = page

        self.loading_overlay.show("Loading page...")
        self.after(
            100,
            lambda: self._load_work_history_data(
                period=self.work_history_view.current_filter,
                page=page,
            ),
        )

    def delete_work_history(self, history_id: int) -> None:
        """Delete a work history log entry (Admin only)."""

        # Check if user is Admin
        if self.current_user.get("role") != "Admin":
            self.notification_system.show_notification(
                message="Only administrators can delete work history logs.",
                notification_type="error",
            )
            return

        # Show confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this work history log?\n\n"
            "This action cannot be undone.",
            icon="warning",
        )

        if not confirm:
            return

        logger.info(f"Deleting work history ID: {history_id}")
        self.loading_overlay.show("Deleting work history...")

        db = SessionLocal()
        try:
            from AutoRBI_Database.services import work_history_service

            # Create a proper current_user dict with user_id
            current_user_with_id = {
                "user_id": self.current_user.get("user_id")
                or self.current_user.get("id"),
                "username": self.current_user.get("username"),
                "role": self.current_user.get("role"),
            }

            result = work_history_service.delete_work_history(
                db=db,
                current_user=current_user_with_id,
                history_id=history_id,
            )

            self.loading_overlay.hide()

            if result.get("success"):
                self.notification_system.show_notification(
                    message="Work history log deleted successfully",
                    notification_type="success",
                )

                # Reload current view
                self.after(
                    500,
                    lambda: self._load_work_history_data(
                        period=self.work_history_view.current_filter,
                        page=self.work_history_view.current_page,
                    ),
                )
            else:
                self.notification_system.show_notification(
                    message=result.get("message", "Unknown error"),
                    notification_type="error",
                )

        except Exception as e:
            logger.error(f"Error deleting work history: {e}", exc_info=True)
            self.loading_overlay.hide()
            self.notification_system.show_notification(
                message="Failed to delete work history. Please try again.",
                notification_type="error",
            )
        finally:
            db.close()


if __name__ == "__main__":
    app = AutoRBIApp()
    app.mainloop()
