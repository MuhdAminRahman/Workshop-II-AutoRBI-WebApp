"""
Custom exceptions for AutoRBI authentication system.

This module defines a hierarchy of exceptions used throughout the application
to handle different types of errors in a clear and structured way.
"""


class AuthenticationError(Exception):
    """
    Base exception for all authentication-related errors.

    Use this as a catch-all when you want to handle any authentication
    issue without caring about the specific type.
    """

    pass


class UserNotFoundError(AuthenticationError):
    """
    Raised when a user doesn't exist in the database.

    Example:
        User tries to login with username that doesn't exist.
    """

    pass


class InvalidPasswordError(AuthenticationError):
    """
    Raised when the provided password doesn't match the stored hash.

    Example:
        User enters wrong password during login.
    """

    pass


class InactiveAccountError(AuthenticationError):
    """
    Raised when trying to authenticate with an inactive/disabled account.

    Example:
        User account has been deactivated by an admin.
    """

    pass


class AccountAlreadyExistsError(AuthenticationError):
    """
    Raised when trying to register with a username that already exists.

    Example:
        New user tries to register with an existing username.
    """

    pass


class ValidationError(Exception):
    """
    Base exception for input validation errors.

    Raised when user input doesn't meet requirements (empty fields,
    wrong format, too short password, etc.)
    """

    pass


class PasswordValidationError(ValidationError):
    """
    Raised when password doesn't meet strength requirements.

    Example:
        Password is too short, or doesn't contain required characters.
    """

    pass


class UsernameValidationError(ValidationError):
    """
    Raised when username doesn't meet requirements.

    Example:
        Username is too short, contains invalid characters, etc.
    """

    pass


class DatabaseError(Exception):
    """
    Raised when database operations fail.

    This is a system-level error indicating problems with database
    connectivity, queries, or transactions.

    Example:
        Database server is down, connection timeout, query error.
    """

    pass


class SystemError(Exception):
    """
    Raised for unexpected system-level errors.

    Use this for errors that aren't specifically covered by other
    exception types but prevent normal operation.
    """

    pass


# ============================================================================
# ADMIN MODULE EXCEPTIONS
# ============================================================================


class AdminError(Exception):
    """Base class for admin-related errors."""

    pass


class UnauthorizedAccessError(AdminError):
    """User doesn't have permission for this action."""

    def __init__(
        self, message: str = "You don't have permission to perform this action"
    ):
        self.message = message
        super().__init__(self.message)


class CannotModifySelfError(AdminError):
    """Admin cannot modify their own account in certain ways."""

    def __init__(
        self, message: str = "You cannot perform this action on your own account"
    ):
        self.message = message
        super().__init__(self.message)


class LastAdminError(AdminError):
    """Cannot remove/deactivate the last admin account."""

    def __init__(self, message: str = "Cannot modify the last administrator account"):
        self.message = message
        super().__init__(self.message)

# Add after existing exceptions

class ProfileError(Exception):
    """Base class for profile-related errors."""
    pass


class CurrentPasswordIncorrectError(ProfileError):
    """The provided current password is incorrect."""
    
    def __init__(self, message: str = "Current password is incorrect"):
        self.message = message
        super().__init__(self.message)


class EmailAlreadyInUseError(ProfileError):
    """The email address is already used by another account."""
    
    def __init__(self, message: str = "This email is already in use"):
        self.message = message
        super().__init__(self.message)