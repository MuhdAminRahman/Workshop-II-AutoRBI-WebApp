"""
Centralized Validation Rules for AutoRBI Application.

=============================================================================
PURPOSE:
=============================================================================
This file is the SINGLE SOURCE OF TRUTH for all validation rules.
Both the UI layer and the backend (CRUD) layer import from here.

This ensures:
1. UI and backend always validate with the SAME rules
2. Changing a rule in one place applies everywhere
3. No confusion about what the actual requirements are

=============================================================================
HOW TO USE:
=============================================================================
In any file that needs validation rules:

    from AutoRBI_Database.validation_rules import UsernameRules, PasswordRules

Then use like:
    
    if len(username) < UsernameRules.MIN_LENGTH:
        # show error

=============================================================================
"""


class UsernameRules:
    """
    Validation rules for usernames.
    
    These rules define what makes a valid username in the system.
    Both UI (for quick feedback) and CRUD (for security) use these.
    """
    
    # Length constraints
    MIN_LENGTH = 3      # Minimum characters required
    MAX_LENGTH = 50     # Maximum characters allowed
    
    # Character pattern (regex)
    # This pattern means: only letters (a-z, A-Z), numbers (0-9), and underscore (_)
    PATTERN = r"^[a-zA-Z0-9_]+$"
    
    # Human-readable description of allowed characters
    # Used in error messages shown to user
    ALLOWED_CHARACTERS = "letters, numbers, and underscores"
    
    # Error messages - centralized so they're consistent everywhere
    ERRORS = {
        "required": "Username is required.",
        "too_short": f"Username must be at least {MIN_LENGTH} characters long.",
        "too_long": f"Username must be less than {MAX_LENGTH} characters.",
        "invalid_chars": f"Username can only contain {ALLOWED_CHARACTERS}.",
        "whitespace_only": "Username cannot be empty or contain only spaces.",
    }


class PasswordRules:
    """
    Validation rules for passwords.
    
    Security requirements for user passwords.
    """
    
    # Length constraints
    MIN_LENGTH = 6      # Minimum characters (OWASP recommends 8+, but 6 for usability)
    MAX_LENGTH = 128    # Maximum to prevent DoS attacks with very long passwords
    
    # Optional complexity requirements (set to True to enforce)
    REQUIRE_DIGIT = False       # Must contain at least one number
    REQUIRE_LETTER = False      # Must contain at least one letter
    REQUIRE_UPPERCASE = False   # Must contain uppercase letter
    REQUIRE_LOWERCASE = False   # Must contain lowercase letter
    REQUIRE_SPECIAL = False     # Must contain special character
    
    # Error messages
    ERRORS = {
        "required": "Password is required.",
        "too_short": f"Password must be at least {MIN_LENGTH} characters long.",
        "too_long": f"Password must be less than {MAX_LENGTH} characters.",
        "needs_digit": "Password must contain at least one number.",
        "needs_letter": "Password must contain at least one letter.",
        "mismatch": "Passwords do not match.",
    }


class FullNameRules:
    """
    Validation rules for full names.
    """
    
    # Length constraints
    MIN_LENGTH = 2      # At least 2 characters (e.g., "Li")
    MAX_LENGTH = 100    # Reasonable max for full names
    
    # Error messages
    ERRORS = {
        "required": "Full name is required.",
        "too_short": f"Full name must be at least {MIN_LENGTH} characters long.",
        "too_long": f"Full name must be less than {MAX_LENGTH} characters.",
    }
    


import re

class EmailRules:
    """
    Validation rules for email addresses.
    """
    
    # Email regex pattern
    PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    MAX_LENGTH = 255
    
    # Error messages
    ERRORS = {
        "required": "Email address is required.",
        "invalid_format": "Please enter a valid email address.",
        "too_long": f"Email must be less than {MAX_LENGTH} characters.",
    }


def get_email_validation_error(email: str) -> str | None:
    """
    Validate email address.
    
    Args:
        email: The email to validate
        
    Returns:
        Error message string if invalid, None if valid
    """
    if not email or not email.strip():
        return EmailRules.ERRORS["required"]
    
    email = email.strip()
    
    if len(email) > EmailRules.MAX_LENGTH:
        return EmailRules.ERRORS["too_long"]
    
    if not re.match(EmailRules.PATTERN, email):
        return EmailRules.ERRORS["invalid_format"]
    
    return None
    
    
    
    
class RoleRules:
    """
    Validation rules for user roles.
    """
    
    # Valid role values
    VALID_ROLES = ["Admin", "Engineer"]
    DEFAULT_ROLE = "Engineer"
    
    # Error messages
    ERRORS = {
        "required": "Role is required.",
        "invalid": f"Role must be one of: {', '.join(VALID_ROLES)}",
    }


class StatusRules:
    """
    Validation rules for user status.
    """
    
    # Valid status values
    VALID_STATUSES = ["Active", "Inactive"]
    DEFAULT_STATUS = "Active"
    
    # Error messages
    ERRORS = {
        "required": "Status is required.",
        "invalid": f"Status must be one of: {', '.join(VALID_STATUSES)}",
    }


def get_role_validation_error(role: str) -> str | None:
    """
    Validate role value.
    
    Args:
        role: The role to validate
        
    Returns:
        Error message string if invalid, None if valid
    """
    if not role:
        return RoleRules.ERRORS["required"]
    
    if role not in RoleRules.VALID_ROLES:
        return RoleRules.ERRORS["invalid"]
    
    return None


def get_status_validation_error(status: str) -> str | None:
    """
    Validate status value.
    
    Args:
        status: The status to validate
        
    Returns:
        Error message string if invalid, None if valid
    """
    if not status:
        return StatusRules.ERRORS["required"]
    
    if status not in StatusRules.VALID_STATUSES:
        return StatusRules.ERRORS["invalid"]
    
    return None


# =============================================================================
# VALIDATION HELPER FUNCTIONS
# =============================================================================
# These functions can be used by both UI and CRUD for consistent validation

import re


def is_valid_username_format(username: str) -> bool:
    """
    Check if username matches the allowed pattern.
    
    Args:
        username: The username to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not username:
        return False
    return bool(re.match(UsernameRules.PATTERN, username))


def get_username_validation_error(username: str) -> str | None:
    """
    Validate username and return error message if invalid.
    
    This function checks ALL username rules and returns the first error found.
    Returns None if username is valid.
    
    Args:
        username: The username to validate
        
    Returns:
        Error message string if invalid, None if valid
        
    Example:
        error = get_username_validation_error("ab")
        if error:
            show_error(error)  # "Username must be at least 3 characters long."
    """
    # Check if provided
    if not username:
        return UsernameRules.ERRORS["required"]
    
    # Strip and check again (whitespace only)
    username_clean = username.strip()
    if not username_clean:
        return UsernameRules.ERRORS["whitespace_only"]
    
    # Check minimum length
    if len(username_clean) < UsernameRules.MIN_LENGTH:
        return UsernameRules.ERRORS["too_short"]
    
    # Check maximum length
    if len(username_clean) > UsernameRules.MAX_LENGTH:
        return UsernameRules.ERRORS["too_long"]
    
    # Check character pattern
    if not re.match(UsernameRules.PATTERN, username_clean):
        return UsernameRules.ERRORS["invalid_chars"]
    
    # All checks passed
    return None


def get_password_validation_error(password: str) -> str | None:
    """
    Validate password and return error message if invalid.
    
    Args:
        password: The password to validate
        
    Returns:
        Error message string if invalid, None if valid
    """
    # Check if provided
    if not password:
        return PasswordRules.ERRORS["required"]
    
    # Check minimum length
    if len(password) < PasswordRules.MIN_LENGTH:
        return PasswordRules.ERRORS["too_short"]
    
    # Check maximum length
    if len(password) > PasswordRules.MAX_LENGTH:
        return PasswordRules.ERRORS["too_long"]
    
    # Optional complexity checks
    if PasswordRules.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        return PasswordRules.ERRORS["needs_digit"]
    
    if PasswordRules.REQUIRE_LETTER and not any(c.isalpha() for c in password):
        return PasswordRules.ERRORS["needs_letter"]
    
    # All checks passed
    return None


def get_fullname_validation_error(full_name: str) -> str | None:
    """
    Validate full name and return error message if invalid.
    
    Args:
        full_name: The full name to validate
        
    Returns:
        Error message string if invalid, None if valid
    """
    # Check if provided
    if not full_name:
        return FullNameRules.ERRORS["required"]
    
    # Strip and check again
    name_clean = full_name.strip()
    if not name_clean:
        return FullNameRules.ERRORS["required"]
    
    # Check minimum length
    if len(name_clean) < FullNameRules.MIN_LENGTH:
        return FullNameRules.ERRORS["too_short"]
    
    # Check maximum length
    if len(name_clean) > FullNameRules.MAX_LENGTH:
        return FullNameRules.ERRORS["too_long"]
    
    # All checks passed
    return None
