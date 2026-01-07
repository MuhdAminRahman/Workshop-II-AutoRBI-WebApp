# backend/auth_service.py
from typing import Dict, Any
from sqlalchemy.orm import Session
from AutoRBI_Database.logging_config import get_logger, auth_logger

from AutoRBI_Database.database.crud.user_crud import (
    login_user,
    register_engineer,
    get_user_by_username,
    get_user_by_id,
)


from AutoRBI_Database.exceptions import (
    UserNotFoundError,
    InvalidPasswordError,
    InactiveAccountError,
    AccountAlreadyExistsError,
    ValidationError,
    DatabaseError,
)

from AutoRBI_Database.messages import (
    AuthMessages,
    RegistrationMessages,
    ErrorTypes,
    format_message,
)

# Initialize logger for this module
logger = get_logger(__name__)


def authenticate_user(db: Session, username: str, password: str) -> Dict[str, Any]:
    """
    High-level authentication function that handles login.

    This function implements structured error responses with error types,
    allowing the UI to respond appropriately to different error scenarios.

    Concepts implemented:
    - 1. Custom Exceptions: Catches specific exceptions from CRUD layer
    - 3. Security: Returns generic messages for authentication failures
    - 4. Graceful Degradation: Converts database errors to friendly messages
    - 7. User-Friendly Messages: Uses message catalog for all responses
    - 8. Error Context: Includes error_type field in all responses

    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password

    Returns:
        Dictionary with structure:
        {
            "success": bool,
            "message": str,
            "user": User object or None,
            "error_type": str (only on failure)
        }

    Example Success Response:
        {
            "success": True,
            "message": "Welcome back! Login successful.",
            "user": <User object>
        }

    Example Failure Response:
        {
            "success": False,
            "message": "Invalid username or password. Please try again.",
            "user": None,
            "error_type": "authentication"
        }
    """
    # Log authentication attempt (using special auth logger for security auditing)
    auth_logger.info(f"Authentication attempt for username: {username}")

    try:
        # Call the CRUD layer login function
        # This may raise various exceptions which we'll catch below
        user = login_user(db, username, password)

        # Success! Log and return positive response
        auth_logger.info(f"Successful authentication: {username}")
        logger.info(f"User {username} authenticated successfully")

        return {"success": True, "message": AuthMessages.LOGIN_SUCCESS, "user": user}

    except (UserNotFoundError, InvalidPasswordError) as e:
        # SECURITY CONSIDERATION: Both username not found and invalid password
        # return the SAME generic message to prevent username enumeration attacks

        # Log the specific reason internally (for security team)
        auth_logger.warning(
            f"Authentication failed for '{username}': {type(e).__name__}"
        )
        logger.warning(f"Authentication failed: {username} - {type(e).__name__}")

        # Return generic message to user (don't reveal which part failed)
        return {
            "success": False,
            "message": AuthMessages.INVALID_CREDENTIALS,  # Generic message
            "user": None,
            "error_type": ErrorTypes.AUTHENTICATION,
            "retry_allowed": True,
        }

    except InactiveAccountError as e:
        # Account exists but is inactive
        # This is safe to be specific about since they proved they have credentials

        auth_logger.warning(f"Login attempt on inactive account: {username}")
        logger.warning(f"Inactive account login attempt: {username}")

        return {
            "success": False,
            "message": AuthMessages.ACCOUNT_INACTIVE,
            "user": None,
            "error_type": ErrorTypes.ACCOUNT_STATUS,
            "retry_allowed": False,  # User needs admin help
            "support_action": "contact_admin",
        }

    except ValidationError as e:
        # Input validation failed (empty fields, invalid format, etc.)

        auth_logger.warning(
            f"Validation error during authentication for '{username}': {e}"
        )
        logger.warning(f"Validation error: {username} - {e}")

        return {
            "success": False,
            "message": str(e),  # Show the specific validation error
            "user": None,
            "error_type": ErrorTypes.VALIDATION,
            "retry_allowed": True,
        }

    except DatabaseError as e:
        # Database connection or query failed
        # GRACEFUL DEGRADATION: Don't crash the app, return friendly error

        auth_logger.error(f"Database error during authentication for '{username}': {e}")
        logger.error(f"Database error during authentication: {e}", exc_info=True)

        return {
            "success": False,
            "message": AuthMessages.SERVICE_UNAVAILABLE,
            "user": None,
            "error_type": ErrorTypes.SYSTEM,
            "retry_allowed": True,
            "retry_delay": 5,  # Suggest waiting 5 seconds before retry
        }

    except Exception as e:
        # Unexpected error - catch-all for safety
        # This should rarely happen if all other exceptions are properly handled

        auth_logger.error(
            f"Unexpected error during authentication for '{username}': {e}",
            exc_info=True,
        )
        logger.error(f"Unexpected authentication error: {e}", exc_info=True)

        return {
            "success": False,
            "message": AuthMessages.SERVICE_UNAVAILABLE,
            "user": None,
            "error_type": ErrorTypes.APPLICATION,
            "retry_allowed": True,
        }


def register_user(
    db: Session, full_name: str, username: str, password: str
) -> Dict[str, Any]:
    """
    High-level registration function that handles new user creation.

    This function converts exceptions from the CRUD layer into structured
    responses with appropriate error types and user-friendly messages.

    Args:
        db: Database session
        full_name: User's full name
        username: Desired username
        password: Plain text password (will be hashed)

    Returns:
        Dictionary with structure:
        {
            "success": bool,
            "message": str,
            "user": User object or None (None for privacy - don't return user on registration),
            "error_type": str (only on failure)
        }

    Example Success Response:
        {
            "success": True,
            "message": "Registration successful! You can now login with your credentials.",
            "user": None
        }

    Example Failure Response:
        {
            "success": False,
            "message": "This username is already taken. Please choose a different username.",
            "user": None,
            "error_type": "account_exists"
        }
    """
    # Log registration attempt
    auth_logger.info(f"Registration attempt for username: {username}")
    logger.info(f"New user registration attempt: {username}")

    try:
        # Call the CRUD layer registration function
        user = register_engineer(db, username, full_name, password)

        # Success! Log and return positive response
        auth_logger.info(f"Successful registration: {username}")
        logger.info(f"New user registered successfully: {username}")

        return {
            "success": True,
            "message": RegistrationMessages.REGISTRATION_SUCCESS,
            "user": None,  # For security, don't return user object on registration
        }

    except ValidationError as e:
        # Input validation failed

        auth_logger.warning(
            f"Validation error during registration for '{username}': {e}"
        )
        logger.warning(f"Registration validation error: {username} - {e}")

        # Return the specific validation error message
        return {
            "success": False,
            "message": str(e),
            "user": None,
            "error_type": ErrorTypes.VALIDATION,
            "retry_allowed": True,
        }

    except AccountAlreadyExistsError as e:
        # Username already taken

        auth_logger.warning(f"Registration failed - username exists: {username}")
        logger.warning(f"Registration attempt with existing username: {username}")

        return {
            "success": False,
            "message": RegistrationMessages.USERNAME_EXISTS,
            "user": None,
            "error_type": ErrorTypes.ACCOUNT_EXISTS,
            "retry_allowed": True,
            "field": "username",  # Tell UI which field has the issue
        }

    except DatabaseError as e:
        # Database connection or query failed
        # GRACEFUL DEGRADATION: Don't crash the app

        auth_logger.error(f"Database error during registration for '{username}': {e}")
        logger.error(f"Database error during registration: {e}", exc_info=True)

        return {
            "success": False,
            "message": RegistrationMessages.REGISTRATION_FAILED,
            "user": None,
            "error_type": ErrorTypes.SYSTEM,
            "retry_allowed": True,
            "retry_delay": 5,
        }

    except Exception as e:
        # Unexpected error - catch-all for safety

        auth_logger.error(
            f"Unexpected error during registration for '{username}': {e}", exc_info=True
        )
        logger.error(f"Unexpected registration error: {e}", exc_info=True)

        return {
            "success": False,
            "message": RegistrationMessages.REGISTRATION_FAILED,
            "user": None,
            "error_type": ErrorTypes.APPLICATION,
            "retry_allowed": True,
        }


def validate_session(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Validate that a user session is still valid.

    This can be used to check if a user's session should still be active
    (account not deactivated, user still exists, etc.)

    Args:
        db: Database session
        user_id: ID of user to validate

    Returns:
        Dictionary with structure:
        {
            "valid": bool,
            "message": str,
            "user": User object or None
        }
    """

    logger.debug(f"Validating session for user ID: {user_id}")

    try:
        user = get_user_by_id(db, user_id)

        if not user:
            logger.warning(f"Session validation failed: User {user_id} not found")
            return {"valid": False, "message": "User not found", "user": None}

        if user.status != "Active":
            logger.warning(
                f"Session validation failed: User {user_id} is {user.status}"
            )
            return {
                "valid": False,
                "message": "Account is no longer active",
                "user": None,
            }

        logger.debug(f"Session validated for user ID: {user_id}")
        return {"valid": True, "message": "Session valid", "user": user}

    except DatabaseError as e:
        logger.error(
            f"Database error during session validation for user {user_id}: {e}",
            exc_info=True,
        )
        return {"valid": False, "message": "Unable to validate session", "user": None}

    except Exception as e:
        logger.error(
            f"Unexpected error during session validation for user {user_id}: {e}",
            exc_info=True,
        )
        return {"valid": False, "message": "Unable to validate session", "user": None}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_success_response(message: str, user=None, **kwargs) -> Dict[str, Any]:
    """
    Helper to create a standardized success response.

    Args:
        message: Success message
        user: User object (optional)
        **kwargs: Additional fields to include

    Returns:
        Success response dictionary
    """
    response = {"success": True, "message": message, "user": user}
    response.update(kwargs)
    return response


def create_error_response(
    message: str, error_type: str, retry_allowed: bool = True, **kwargs
) -> Dict[str, Any]:
    """
    Helper to create a standardized error response.

    Args:
        message: Error message for the user
        error_type: Type of error (from ErrorTypes constants)
        retry_allowed: Whether the user can retry the operation
        **kwargs: Additional fields to include

    Returns:
        Error response dictionary
    """
    response = {
        "success": False,
        "message": message,
        "user": None,
        "error_type": error_type,
        "retry_allowed": retry_allowed,
    }
    response.update(kwargs)
    return response
