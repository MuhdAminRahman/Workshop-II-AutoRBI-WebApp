"""Views package for AutoRBI interface."""

from .login import LoginView
from .registration import RegistrationView
from .main_menu import MainMenuView
from .new_work import NewWorkView
from .report_menu import ReportMenuView
from .work_history import WorkHistoryView
from .analytics import AnalyticsView
from .settings import SettingsView
from .profile import ProfileView
from .constants import Fonts, Colors, Sizes, Messages, TableColumns
from .page_builders import Page1Builder, Page2Builder
from .ui_updater import UIUpdateManager
from .user_management import UserManagementView


__all__ = [
    "LoginView",
    "RegistrationView",
    "MainMenuView",
    "NewWorkView",
    "ReportMenuView",
    "WorkHistoryView",
    "AnalyticsView",
    "SettingsView",
    "ProfileView",
    "Fonts",
    "Colors",
    "Sizes",
    "Messages",
    "TableColumns",
    "Page1Builder",
    "Page2Builder",
    "UIUpdateManager"
    "UserManagementView",
]

