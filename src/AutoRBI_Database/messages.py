"""
User-friendly messages for AutoRBI application.

This module centralizes all user-facing messages to ensure consistency
and make it easy to update messaging across the application.
"""


class AuthMessages:
    """Messages related to authentication (login/logout)."""
    
    # Success messages
    LOGIN_SUCCESS = "Welcome back! Login successful."
    LOGOUT_SUCCESS = "You have been logged out successfully."
    
    # Authentication failure messages
    # NOTE: We use generic messages for security (don't reveal if username exists)
    INVALID_CREDENTIALS = "Invalid username or password. Please try again."
    
    # Account status messages
    ACCOUNT_INACTIVE = (
        "Your account is currently inactive. "
        "Please contact your administrator for assistance."
    )
    
    ACCOUNT_LOCKED = (
        "Your account has been locked due to multiple failed login attempts. "
        "Please contact support or try again later."
    )
    
    # System error messages
    SERVICE_UNAVAILABLE = (
        "Our service is temporarily unavailable. "
        "Please try again in a few moments."
    )
    
    DATABASE_ERROR = (
        "We're experiencing technical difficulties. "
        "Please try again later."
    )
    
    NETWORK_ERROR = (
        "Unable to connect to the server. "
        "Please check your internet connection and try again."
    )


class RegistrationMessages:
    """Messages related to user registration."""
    
    # Success messages
    REGISTRATION_SUCCESS = (
        "Registration successful! "
        "You can now login with your credentials."
    )
    
    # Validation error messages
    ALL_FIELDS_REQUIRED = "Please fill in all required fields."
    
    PASSWORDS_DO_NOT_MATCH = (
        "Passwords do not match. "
        "Please ensure both password fields are identical."
    )
    
    PASSWORD_TOO_SHORT = (
        "Password must be at least {min_length} characters long. "
        "Please choose a stronger password."
    )
    
    PASSWORD_TOO_WEAK = (
        "Password is too weak. Please include a mix of "
        "letters, numbers, and special characters."
    )
    
    USERNAME_TOO_SHORT = (
        "Username must be at least {min_length} characters long."
    )
    
    USERNAME_TOO_LONG = (
        "Username must be less than {max_length} characters."
    )
    
    USERNAME_INVALID_CHARS = (
        "Username can only contain letters, numbers, and underscores."
    )
    
    FULLNAME_REQUIRED = "Please enter your full name."
    
    # Duplicate/conflict messages
    USERNAME_EXISTS = (
        "This username is already taken. "
        "Please choose a different username."
    )
    
    # System error messages
    REGISTRATION_FAILED = (
        "Registration failed due to a technical issue. "
        "Please try again later."
    )


class ValidationMessages:
    """Messages for input validation."""
    
    FIELD_REQUIRED = "This field is required."
    FIELD_TOO_SHORT = "This field must be at least {min_length} characters."
    FIELD_TOO_LONG = "This field must be less than {max_length} characters."
    INVALID_FORMAT = "Invalid format. Please check your input."
    CONTAINS_WHITESPACE = "This field cannot contain spaces."
    INVALID_CHARACTERS = "This field contains invalid characters."


class SystemMessages:
    """General system messages."""
    
    UNEXPECTED_ERROR = (
        "An unexpected error occurred. "
        "Please try again or contact support if the problem persists."
    )
    
    LOADING = "Loading..."
    PROCESSING = "Processing your request..."
    PLEASE_WAIT = "Please wait..."
    
    # Support contact info
    CONTACT_SUPPORT = (
        "If this problem persists, please contact support at:\n"
        "Email: support@autorbi.com\n"
        "Phone: +1-XXX-XXX-XXXX"
    )


class ErrorTypes:
    """
    Standard error type constants for structured error responses.
    
    These help the UI layer determine how to display errors and
    what actions to offer the user.
    """
    
    # User-related errors (user can potentially fix)
    AUTHENTICATION = "authentication"      # Wrong credentials
    VALIDATION = "validation"             # Invalid input
    PERMISSION = "permission"             # Not authorized
    
    # Account-related errors (need admin/support intervention)
    ACCOUNT_STATUS = "account_status"     # Inactive, locked, etc.
    ACCOUNT_EXISTS = "account_exists"     # Username already taken
    
    # System-related errors (temporary issues)
    SYSTEM = "system"                     # Database, network, etc.
    DATABASE = "database"                 # Database-specific
    NETWORK = "network"                   # Network connectivity
    
    # Application errors (bugs)
    APPLICATION = "application"           # Unexpected error
    UNKNOWN = "unknown"                   # Unknown error type


def format_message(message: str, **kwargs) -> str:
    """
    Format a message template with provided values.
    
    Args:
        message: Message template with {placeholders}
        **kwargs: Values to fill in the placeholders
        
    Returns:
        Formatted message string
        
    Example:
        >>> format_message(RegistrationMessages.PASSWORD_TOO_SHORT, min_length=8)
        'Password must be at least 8 characters long. Please choose a stronger password.'
    """
    try:
        return message.format(**kwargs)
    except KeyError:
        # If placeholder not provided, return original message
        return message
