import sys
import os


from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from passlib.context import CryptContext
from AutoRBI_Database.logging_config import get_logger
import re

from AutoRBI_Database.database.models import User

from AutoRBI_Database.exceptions import (
    UserNotFoundError,
    InvalidPasswordError,
    InactiveAccountError,
    AccountAlreadyExistsError,
    ValidationError,
    PasswordValidationError,
    UsernameValidationError,
    DatabaseError,
)

# Import centralized validation rules - SINGLE SOURCE OF TRUTH
# Both UI and CRUD use these same rules for consistency
from AutoRBI_Database.validation_rules import (
    UsernameRules,
    PasswordRules,
    FullNameRules,
    RoleRules,
    StatusRules,
)

from AutoRBI_Database.validation_rules import EmailRules, get_email_validation_error
from AutoRBI_Database.exceptions import (
    CurrentPasswordIncorrectError,
    EmailAlreadyInUseError,
)


# Initialize logger for this module
logger = get_logger(__name__)


# OLD:
# pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# NEW:
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using secure hashing algorithm.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    logger.debug("Hashing password")
    return pwd_context.hash(password)


def verify_password(plain_pw: str, hashed_pw: str) -> bool:
    """
    Verify a password against its hash using timing-safe comparison.

    Args:
        plain_pw: Plain text password to verify
        hashed_pw: Hashed password to compare against

    Returns:
        True if password matches, False otherwise

    Security Note:
        Uses constant-time comparison to prevent timing attacks.
    """
    logger.debug("Verifying password")
    try:
        return pwd_context.verify(plain_pw, hashed_pw)
    except Exception as e:
        logger.error(f"Password verification error: {e}", exc_info=True)
        return False


def normalize_user_status(value):
    """
    Normalize user status value to standard format.

    Args:
        value: Status value (can be various formats)

    Returns:
        Normalized status: "Active" or "Inactive"
        None if invalid format
    """
    if value is None:
        return None

    v = str(value).strip().lower()

    if v in ["active", "a", "enabled", "yes", "true", "1"]:
        return "Active"
    if v in ["inactive", "i", "disabled", "no", "false", "0"]:
        return "Inactive"

    return None


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def validate_username(username: str) -> None:
    """
    Validate username meets requirements.

    Uses centralized rules from validation_rules.py to ensure
    consistency between UI and backend validation.

    Args:
        username: Username to validate

    Raises:
        UsernameValidationError: If username is invalid
    """
    # Check if provided
    if not username:
        raise UsernameValidationError(UsernameRules.ERRORS["required"])

    username = username.strip()

    # Check for whitespace-only
    if not username:
        raise UsernameValidationError(UsernameRules.ERRORS["whitespace_only"])

    # Check minimum length - using centralized constant
    if len(username) < UsernameRules.MIN_LENGTH:
        raise UsernameValidationError(UsernameRules.ERRORS["too_short"])

    # Check maximum length - using centralized constant
    if len(username) > UsernameRules.MAX_LENGTH:
        raise UsernameValidationError(UsernameRules.ERRORS["too_long"])

    # Check for valid characters - using centralized pattern
    if not re.match(UsernameRules.PATTERN, username):
        raise UsernameValidationError(UsernameRules.ERRORS["invalid_chars"])

    logger.debug(f"Username validation passed: {username}")


def validate_password(password: str) -> None:
    """
    Validate password meets security requirements.

    Uses centralized rules from validation_rules.py to ensure
    consistency between UI and backend validation.

    Args:
        password: Password to validate

    Raises:
        PasswordValidationError: If password is invalid
    """
    # Check if provided
    if not password:
        raise PasswordValidationError(PasswordRules.ERRORS["required"])

    # Check minimum length - using centralized constant
    if len(password) < PasswordRules.MIN_LENGTH:
        raise PasswordValidationError(PasswordRules.ERRORS["too_short"])

    # Check maximum length - using centralized constant
    if len(password) > PasswordRules.MAX_LENGTH:
        raise PasswordValidationError(PasswordRules.ERRORS["too_long"])

    # Optional complexity checks (controlled by flags in PasswordRules)
    if PasswordRules.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        raise PasswordValidationError(PasswordRules.ERRORS["needs_digit"])

    if PasswordRules.REQUIRE_LETTER and not any(c.isalpha() for c in password):
        raise PasswordValidationError(PasswordRules.ERRORS["needs_letter"])

    logger.debug("Password validation passed")


def validate_full_name(full_name: str) -> None:
    """
    Validate full name meets requirements.

    Uses centralized rules from validation_rules.py to ensure
    consistency between UI and backend validation.

    Args:
        full_name: Full name to validate

    Raises:
        ValidationError: If full name is invalid
    """
    # Check if provided
    if not full_name or not full_name.strip():
        raise ValidationError(FullNameRules.ERRORS["required"])

    # Check minimum length - using centralized constant
    if len(full_name.strip()) < FullNameRules.MIN_LENGTH:
        raise ValidationError(FullNameRules.ERRORS["too_short"])

    # Check maximum length - using centralized constant
    if len(full_name) > FullNameRules.MAX_LENGTH:
        raise ValidationError(FullNameRules.ERRORS["too_long"])

    logger.debug("Full name validation passed")


# ============================================================================
# DATABASE QUERY FUNCTIONS
# ============================================================================


def get_user_by_id(db: Session, user_id: int):
    """
    Retrieve user by ID with error handling.

    Args:
        db: Database session
        user_id: User ID to search for

    Returns:
        User object or None if not found

    Raises:
        DatabaseError: If database operation fails
    """
    logger.debug(f"Fetching user by ID: {user_id}")

    try:
        user = db.query(User).filter(User.user_id == user_id).first()

        if user:
            logger.debug(f"User found: {user.username}")
        else:
            logger.debug(f"User not found with ID: {user_id}")

        return user

    except OperationalError as e:
        # 9. EXCEPTION CHAINING - Preserve original error
        logger.error(
            f"Database connection error while fetching user {user_id}: {e}",
            exc_info=True,
        )
        raise DatabaseError("Unable to connect to database") from e

    except SQLAlchemyError as e:
        # 9. EXCEPTION CHAINING
        logger.error(
            f"Database error while fetching user {user_id}: {e}", exc_info=True
        )
        raise DatabaseError("Database error occurred") from e


def get_user_by_username(db: Session, username: str):
    """
    Retrieve user by username with error handling.

    Args:
        db: Database session
        username: Username to search for

    Returns:
        User object or None if not found

    Raises:
        DatabaseError: If database operation fails
    """
    logger.debug(f"Fetching user by username: {username}")

    try:
        user = db.query(User).filter(User.username == username).first()

        if user:
            logger.debug(f"User found: {username}")
        else:
            logger.debug(f"User not found: {username}")

        return user

    except OperationalError as e:
        # 9. EXCEPTION CHAINING - Preserve original error
        logger.error(
            f"Database connection error while fetching user '{username}': {e}",
            exc_info=True,
        )
        raise DatabaseError("Unable to connect to database") from e

    except SQLAlchemyError as e:
        # 9. EXCEPTION CHAINING
        logger.error(
            f"Database error while fetching user '{username}': {e}", exc_info=True
        )
        raise DatabaseError("Database error occurred") from e


def get_all_users(db: Session):
    """
    Get all users with error handling.

    Args:
        db: Database session

    Returns:
        List of User objects

    Raises:
        DatabaseError: If database operation fails
    """
    logger.debug("Fetching all users")

    try:
        users = db.query(User).all()
        logger.info(f"Retrieved {len(users)} users")
        return users

    except OperationalError as e:
        logger.error(
            f"Database connection error while fetching all users: {e}", exc_info=True
        )
        raise DatabaseError("Unable to connect to database") from e

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching all users: {e}", exc_info=True)
        raise DatabaseError("Database error occurred") from e


def get_active_users(db: Session):
    """
    Get all active users with error handling.

    Args:
        db: Database session

    Returns:
        List of active User objects

    Raises:
        DatabaseError: If database operation fails
    """
    logger.debug("Fetching active users")

    try:
        users = db.query(User).filter(User.status == "Active").all()
        logger.info(f"Retrieved {len(users)} active users")
        return users

    except OperationalError as e:
        logger.error(
            f"Database connection error while fetching active users: {e}", exc_info=True
        )
        raise DatabaseError("Unable to connect to database") from e

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching active users: {e}", exc_info=True)
        raise DatabaseError("Database error occurred") from e


# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================


def login_user(db: Session, username: str, password: str):
    """
    Authenticate user credentials with comprehensive error handling.

    This function implements all 9 error handling concepts:
    1. Custom Exceptions - Raises specific exceptions for different failures
    2. Logging - Logs at each step (INFO, WARNING, ERROR)
    3. Security - Generic messages, no username enumeration
    4. Graceful Degradation - Database errors don't crash the app
    5. Resource Cleanup - Handled by caller (session management)
    6. Input Validation - Validates inputs before database queries
    7. User-Friendly Messages - Clear error messages
    8. Error Context - Different exceptions for different scenarios
    9. Exception Chaining - Preserves original errors with 'from e'

    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password to verify

    Returns:
        User object if authentication successful

    Raises:
        ValidationError: If inputs are invalid
        UserNotFoundError: If user doesn't exist (for internal use)
        InactiveAccountError: If account is not active
        InvalidPasswordError: If password is incorrect
        DatabaseError: If database operation fails

    Security Notes:
        - Uses timing-safe password comparison
        - Logs failures for security monitoring
        - Doesn't reveal if username exists (caller should handle)
    """
    # 2. LOGGING - Track authentication attempt
    logger.info(f"Login attempt for username: {username}")

    # 6. INPUT VALIDATION - Validate early (fail fast)
    try:
        validate_username(username)
        validate_password(password)
    except (UsernameValidationError, PasswordValidationError) as e:
        logger.warning(f"Login validation failed for '{username}': {e}")
        raise ValidationError(str(e)) from e

    # Clean the username
    username = username.strip()

    # Database query with error handling
    try:
        # 2. LOGGING - Log database operation
        logger.debug(f"Querying database for user: {username}")
        user = get_user_by_username(db, username)

    except DatabaseError as e:
        # 4. GRACEFUL DEGRADATION - Database error doesn't crash app
        # 9. EXCEPTION CHAINING - Already chained in get_user_by_username
        logger.error(f"Database error during login for '{username}'", exc_info=True)
        raise  # Re-raise the DatabaseError

    # Check if user exists
    if not user:
        # 3. SECURITY - Don't reveal user doesn't exist
        # 2. LOGGING - Log for security monitoring
        logger.warning(f"Login failed: User '{username}' not found")
        # Raise generic error - caller will convert to generic message
        raise InvalidPasswordError("Invalid credentials")

    # Check account status
    if user.status != "Active":
        # 2. LOGGING - Log security event
        logger.warning(
            f"Login attempt on inactive account: {username} (status: {user.status})"
        )
        # 1. CUSTOM EXCEPTIONS - Specific exception type
        raise InactiveAccountError(f"Account status is {user.status}")

    # Verify password
    # 2. LOGGING
    logger.debug(f"Verifying password for user: {username}")

    if not verify_password(password, user.password):
        # 3. SECURITY - Log failed attempt
        # 2. LOGGING
        logger.warning(f"Login failed: Invalid password for user '{username}'")
        # 1. CUSTOM EXCEPTIONS
        raise InvalidPasswordError("Invalid credentials")

    # Success!
    # 2. LOGGING - Log successful login
    logger.info(f"Successful login: {username}")

    return user


# ============================================================================
# REGISTRATION FUNCTIONS
# ============================================================================


def register_engineer(db: Session, username: str, full_name: str, password: str):
    """
    Register a new engineer user with comprehensive validation and error handling.

    Args:
        db: Database session
        username: Desired username
        full_name: User's full name
        password: Plain text password (will be hashed)

    Returns:
        Created User object

    Raises:
        ValidationError: If any input is invalid
        AccountAlreadyExistsError: If username already exists
        DatabaseError: If database operation fails
    """
    # 2. LOGGING
    logger.info(f"Registration attempt for username: {username}")

    # 6. INPUT VALIDATION - Validate all inputs early
    try:
        validate_username(username)
        validate_full_name(full_name)
        validate_password(password)
    except (UsernameValidationError, PasswordValidationError, ValidationError) as e:
        logger.warning(f"Registration validation failed for '{username}': {e}")
        raise ValidationError(str(e)) from e

    # Clean inputs
    username = username.strip()
    full_name = full_name.strip()

    # Check if username already exists
    try:
        logger.debug(f"Checking if username exists: {username}")
        existing_user = get_user_by_username(db, username)

        if existing_user:
            # 2. LOGGING
            logger.warning(f"Registration failed: Username '{username}' already exists")
            # 1. CUSTOM EXCEPTIONS
            raise AccountAlreadyExistsError(f"Username '{username}' is already taken")

    except DatabaseError as e:
        # 4. GRACEFUL DEGRADATION
        logger.error(
            f"Database error during registration check for '{username}'", exc_info=True
        )
        raise  # Re-raise DatabaseError

    # Hash the password
    logger.debug("Hashing password for new user")
    hashed_pw = hash_password(password)

    # Create user object
    user = User(
        username=username,
        full_name=full_name,
        password=hashed_pw,
        role="Engineer",
        status="Active",
    )

    # Save to database with error handling
    try:
        logger.debug(f"Saving new user to database: {username}")
        db.add(user)
        db.commit()
        db.refresh(user)

        # 2. LOGGING - Success
        logger.info(f"Successfully registered new user: {username}")

        return user

    except IntegrityError as e:
        # Username constraint violation (shouldn't happen due to our check, but just in case)
        db.rollback()
        logger.error(
            f"Integrity error during registration for '{username}': {e}", exc_info=True
        )
        # 9. EXCEPTION CHAINING
        raise AccountAlreadyExistsError(f"Username '{username}' already exists") from e

    except OperationalError as e:
        db.rollback()
        logger.error(
            f"Database connection error during registration for '{username}': {e}",
            exc_info=True,
        )
        # 9. EXCEPTION CHAINING
        raise DatabaseError("Unable to connect to database") from e

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Database error during registration for '{username}': {e}", exc_info=True
        )
        # 9. EXCEPTION CHAINING
        raise DatabaseError("Database error during registration") from e


def create_user(
    db: Session, username: str, full_name: str, password: str, role: str = "Engineer"
):
    """
    Create a new user (Admin or Engineer) with validation and error handling.

    Args:
        db: Database session
        username: Desired username
        full_name: User's full name
        password: Plain text password (will be hashed)
        role: User role (default: "Engineer")

    Returns:
        Created User object

    Raises:
        ValidationError: If any input is invalid
        AccountAlreadyExistsError: If username already exists
        DatabaseError: If database operation fails
    """
    # 2. LOGGING
    logger.info(f"Creating new user: {username} with role: {role}")

    # Validate role
    if role not in ["Engineer", "Admin"]:
        raise ValidationError(f"Invalid role: {role}. Must be 'Engineer' or 'Admin'")

    # 6. INPUT VALIDATION
    try:
        validate_username(username)
        validate_full_name(full_name)
        validate_password(password)
    except (UsernameValidationError, PasswordValidationError, ValidationError) as e:
        logger.warning(f"User creation validation failed for '{username}': {e}")
        raise ValidationError(str(e)) from e

    # Clean inputs
    username = username.strip()
    full_name = full_name.strip()

    # Check if username exists
    try:
        logger.debug(f"Checking if username exists: {username}")
        existing_user = get_user_by_username(db, username)

        if existing_user:
            logger.warning(
                f"User creation failed: Username '{username}' already exists"
            )
            raise AccountAlreadyExistsError(f"Username '{username}' is already taken")

    except DatabaseError as e:
        logger.error(
            f"Database error during user creation check for '{username}'", exc_info=True
        )
        raise

    # Hash password
    logger.debug("Hashing password for new user")
    hashed_pw = hash_password(password)

    # Create user
    user = User(
        username=username,
        full_name=full_name,
        password=hashed_pw,
        role=role,
        status="Active",
    )

    # Save to database
    try:
        logger.debug(f"Saving new user to database: {username}")
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"Successfully created user: {username} with role: {role}")

        return user

    except IntegrityError as e:
        db.rollback()
        logger.error(
            f"Integrity error during user creation for '{username}': {e}", exc_info=True
        )
        raise AccountAlreadyExistsError(f"Username '{username}' already exists") from e

    except OperationalError as e:
        db.rollback()
        logger.error(
            f"Database connection error during user creation for '{username}': {e}",
            exc_info=True,
        )
        raise DatabaseError("Unable to connect to database") from e

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Database error during user creation for '{username}': {e}", exc_info=True
        )
        raise DatabaseError("Database error during user creation") from e


# ============================================================================
# UPDATE FUNCTIONS
# ============================================================================


def admin_update_user(db: Session, user_id: int, updates: dict):
    """
    Admin updates a user with validation and error handling.

    Args:
        db: Database session
        user_id: ID of user to update
        updates: Dictionary of fields to update

    Returns:
        Updated User object or None if user not found

    Raises:
        ValidationError: If updates are invalid
        DatabaseError: If database operation fails
    """
    logger.info(f"Admin updating user ID: {user_id}")

    try:
        user = get_user_by_id(db, user_id)
    except DatabaseError as e:
        logger.error(
            f"Database error while fetching user {user_id} for update", exc_info=True
        )
        raise

    if not user:
        logger.warning(f"Admin update failed: User {user_id} not found")
        return None

    # Validate and apply updates
    try:
        if "full_name" in updates:
            validate_full_name(updates["full_name"])
            user.full_name = updates["full_name"].strip()
            logger.debug(f"Updated full_name for user {user_id}")

        if "username" in updates:
            validate_username(updates["username"])
            user.username = updates["username"].strip()
            logger.debug(f"Updated username for user {user_id}")

        if "role" in updates:
            if updates["role"] not in ["Engineer", "Admin"]:
                raise ValidationError(f"Invalid role: {updates['role']}")
            user.role = updates["role"]
            logger.debug(f"Updated role for user {user_id}")

        if "status" in updates:
            normalized = normalize_user_status(updates["status"])
            if normalized is None:
                raise ValidationError(f"Invalid user status: {updates['status']}")
            user.status = normalized
            logger.debug(f"Updated status for user {user_id}")

        if "password" in updates:
            validate_password(updates["password"])
            user.password = hash_password(updates["password"])
            logger.debug(f"Updated password for user {user_id}")

        # Commit changes
        db.commit()
        logger.info(f"Successfully updated user {user_id}")

        return user

    except ValidationError as e:
        db.rollback()
        logger.warning(f"Validation error during admin update for user {user_id}: {e}")
        raise

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Database error during admin update for user {user_id}: {e}", exc_info=True
        )
        raise DatabaseError("Database error during user update") from e


def engineer_update_self(db: Session, user_id: int, full_name=None, password=None):
    """
    Engineer updates their own profile with validation.

    Args:
        db: Database session
        user_id: ID of user updating their profile
        full_name: New full name (optional)
        password: New password (optional)

    Returns:
        Updated User object or None if user not found

    Raises:
        ValidationError: If updates are invalid
        DatabaseError: If database operation fails
    """
    logger.info(f"Engineer self-update for user ID: {user_id}")

    try:
        user = get_user_by_id(db, user_id)
    except DatabaseError as e:
        logger.error(
            f"Database error while fetching user {user_id} for self-update",
            exc_info=True,
        )
        raise

    if not user:
        logger.warning(f"Self-update failed: User {user_id} not found")
        return None

    try:
        if full_name:
            validate_full_name(full_name)
            user.full_name = full_name.strip()
            logger.debug(f"User {user_id} updated their full name")

        if password:
            validate_password(password)
            user.password = hash_password(password)
            logger.debug(f"User {user_id} updated their password")

        db.commit()
        logger.info(f"User {user_id} successfully updated their profile")

        return user

    except ValidationError as e:
        db.rollback()
        logger.warning(f"Validation error during self-update for user {user_id}: {e}")
        raise

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Database error during self-update for user {user_id}: {e}", exc_info=True
        )
        raise DatabaseError("Database error during profile update") from e


def deactivate_user(db: Session, user_id: int):
    """
    Soft delete (deactivate) a user with error handling.

    Args:
        db: Database session
        user_id: ID of user to deactivate

    Returns:
        Deactivated User object or None if user not found

    Raises:
        DatabaseError: If database operation fails
    """
    logger.info(f"Deactivating user ID: {user_id}")

    try:
        user = get_user_by_id(db, user_id)
    except DatabaseError as e:
        logger.error(
            f"Database error while fetching user {user_id} for deactivation",
            exc_info=True,
        )
        raise

    if not user:
        logger.warning(f"Deactivation failed: User {user_id} not found")
        return None

    try:
        user.status = "Inactive"
        db.commit()

        logger.info(f"Successfully deactivated user {user_id} ({user.username})")

        return user

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Database error during deactivation of user {user_id}: {e}", exc_info=True
        )
        raise DatabaseError("Database error during user deactivation") from e


# ============================================================================
# ADMIN CRUD FUNCTIONS
# ============================================================================


def get_all_users(
    db: Session,
    status_filter: str = None,
    role_filter: str = None,
    search_query: str = None,
    skip: int = 0,
    limit: int = 100,
) -> list:
    """
    Get all users with optional filtering.

    This is used by the Admin Module to display users in a table.

    Args:
        db: Database session
        status_filter: "Active" or "Inactive" (None = all)
        role_filter: "Admin" or "Engineer" (None = all)
        search_query: Search in username or full_name
        skip: Offset for pagination
        limit: Max results to return

    Returns:
        List of User objects
    """
    logger.debug(
        f"Fetching users: status={status_filter}, role={role_filter}, search={search_query}"
    )

    try:
        # Start with base query
        query = db.query(User)

        # Apply status filter
        if status_filter:
            if status_filter not in StatusRules.VALID_STATUSES:
                raise ValidationError(StatusRules.ERRORS["invalid"])
            query = query.filter(User.status == status_filter)

        # Apply role filter
        if role_filter:
            if role_filter not in RoleRules.VALID_ROLES:
                raise ValidationError(RoleRules.ERRORS["invalid"])
            query = query.filter(User.role == role_filter)

        # Apply search filter (case-insensitive)
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                (User.username.ilike(search_term)) | (User.full_name.ilike(search_term))
            )

        # Order by username and apply pagination
        users = query.order_by(User.username).offset(skip).limit(limit).all()

        logger.debug(f"Found {len(users)} users")
        return users

    except OperationalError as e:
        logger.error(f"Database error in get_all_users: {e}")
        raise DatabaseError("Unable to retrieve users") from e


def get_user_by_id(db: Session, user_id: int):
    """
    Get a single user by their ID.

    Args:
        db: Database session
        user_id: The user's ID

    Returns:
        User object

    Raises:
        UserNotFoundError: If no user with that ID exists
    """
    logger.debug(f"Fetching user by ID: {user_id}")

    try:
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            logger.warning(f"User not found with ID: {user_id}")
            raise UserNotFoundError(f"User with ID {user_id} not found")

        return user

    except OperationalError as e:
        logger.error(f"Database error in get_user_by_id: {e}")
        raise DatabaseError("Unable to retrieve user") from e


def update_user_details(
    db: Session, user_id: int, full_name: str = None, role: str = None
):
    """
    Update a user's details (admin action).

    Args:
        db: Database session
        user_id: ID of user to update
        full_name: New full name (None = don't change)
        role: New role (None = don't change)

    Returns:
        Updated User object
    """
    logger.info(f"Updating user ID {user_id}: full_name={full_name}, role={role}")

    # Get the user
    user = get_user_by_id(db, user_id)

    # Update full name if provided
    if full_name is not None:
        validate_full_name(full_name)
        user.full_name = full_name.strip()

    # Update role if provided
    if role is not None:
        if role not in RoleRules.VALID_ROLES:
            raise ValidationError(RoleRules.ERRORS["invalid"])
        user.role = role

    try:
        db.commit()
        db.refresh(user)
        logger.info(f"Successfully updated user: {user.username}")
        return user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error updating user: {e}")
        raise DatabaseError("Unable to update user") from e


def update_user_status(db: Session, user_id: int, new_status: str):
    """
    Activate or deactivate a user account (soft delete).

    Args:
        db: Database session
        user_id: ID of user to update
        new_status: "Active" or "Inactive"

    Returns:
        Updated User object
    """
    logger.info(f"Changing status for user ID {user_id} to {new_status}")

    # Validate status
    if new_status not in StatusRules.VALID_STATUSES:
        raise ValidationError(StatusRules.ERRORS["invalid"])

    # Get the user
    user = get_user_by_id(db, user_id)

    # Update status
    user.status = new_status

    try:
        db.commit()
        db.refresh(user)
        logger.info(f"Successfully changed status for {user.username} to {new_status}")
        return user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Error updating user status: {e}")
        raise DatabaseError("Unable to update user status") from e


def reset_user_password(db: Session, user_id: int, new_password: str):
    """
    Reset a user's password (admin action).

    Args:
        db: Database session
        user_id: ID of user
        new_password: New plain text password (will be hashed)

    Returns:
        Updated User object
    """
    logger.info(f"Resetting password for user ID {user_id}")

    # Validate new password
    validate_password(new_password)

    # Get the user
    user = get_user_by_id(db, user_id)

    # Hash and set new password
    user.password = hash_password(new_password)

    try:
        db.commit()
        db.refresh(user)
        logger.info(f"Successfully reset password for {user.username}")
        return user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Error resetting password: {e}")
        raise DatabaseError("Unable to reset password") from e


def create_user_by_admin(
    db: Session, username: str, full_name: str, password: str, role: str = "Engineer"
):
    """
    Admin creates a new user with specified role.

    Unlike register_engineer(), this allows role selection.

    Args:
        db: Database session
        username: New user's username
        full_name: New user's full name
        password: Plain text password (will be hashed)
        role: "Admin" or "Engineer" (default: "Engineer")

    Returns:
        Created User object
    """
    logger.info(f"Admin creating new user: {username} with role {role}")

    # Validate all inputs
    validate_username(username)
    validate_full_name(full_name)
    validate_password(password)

    if role not in RoleRules.VALID_ROLES:
        raise ValidationError(RoleRules.ERRORS["invalid"])

    # Check if username is already taken
    existing = get_user_by_username(db, username)
    if existing:
        raise AccountAlreadyExistsError(f"Username '{username}' is already taken")

    # Create the user
    user = User(
        username=username.strip(),
        full_name=full_name.strip(),
        password=hash_password(password),
        role=role,
        status="Active",
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Successfully created user: {username}")
        return user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise AccountAlreadyExistsError("Username is already taken") from e


def count_users(
    db: Session,
    status_filter: str = None,
    role_filter: str = None,
    search_query: str = None,
) -> int:
    """
    Count users matching filters (for pagination info).

    Args:
        db: Database session
        status_filter: "Active" or "Inactive" (None = all)
        role_filter: "Admin" or "Engineer" (None = all)
        search_query: Search in username or full_name

    Returns:
        Count of matching users
    """
    query = db.query(User)

    if status_filter:
        query = query.filter(User.status == status_filter)

    if role_filter:
        query = query.filter(User.role == role_filter)

    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            (User.username.ilike(search_term)) | (User.full_name.ilike(search_term))
        )

    return query.count()


def count_active_admins(db: Session) -> int:
    """
    Count how many active admin accounts exist.

    This is used to prevent deactivating/demoting the last admin.

    Args:
        db: Database session

    Returns:
        Count of active admins
    """
    return db.query(User).filter(User.role == "Admin", User.status == "Active").count()


def verify_current_password(db: Session, user_id: int, password: str) -> bool:
    """
    Verify that the provided password matches the user's current password.

    Args:
        db: Database session
        user_id: User's ID
        password: Plain text password to verify

    Returns:
        True if password matches, False otherwise
    """
    logger.debug(f"Verifying password for user ID: {user_id}")

    user = get_user_by_id(db, user_id)

    return verify_password(password, user.password)


def update_user_profile_data(
    db: Session, user_id: int, full_name: str = None, email: str = None
):
    """
    Update user's profile data (full_name and/or email).

    Args:
        db: Database session
        user_id: User's ID
        full_name: New full name (None = don't change)
        email: New email (None = don't change)

    Returns:
        Updated User object

    Raises:
        UserNotFoundError: If user doesn't exist
        ValidationError: If validation fails
        EmailAlreadyInUseError: If email is taken by another user
    """
    logger.info(f"Updating profile for user ID {user_id}")

    # Get the user
    user = get_user_by_id(db, user_id)

    # Update full name if provided
    if full_name is not None:
        validate_full_name(full_name)
        user.full_name = full_name.strip()

    # Update email if provided
    if email is not None:
        # Validate email format
        email_error = get_email_validation_error(email)
        if email_error:
            raise ValidationError(email_error)

        email = email.strip().lower()

        # Check if email is already used by another user
        existing_user = (
            db.query(User)
            .filter(
                User.email == email, User.user_id != user_id  # Exclude current user
            )
            .first()
        )

        if existing_user:
            raise EmailAlreadyInUseError(f"Email '{email}' is already in use")

        user.email = email

    try:
        db.commit()
        db.refresh(user)
        logger.info(f"Successfully updated profile for {user.username}")
        return user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Error updating profile: {e}")
        raise DatabaseError("Unable to update profile") from e


def change_user_password(
    db: Session, user_id: int, current_password: str, new_password: str
):
    """
    Change user's password after verifying current password.

    Args:
        db: Database session
        user_id: User's ID
        current_password: Current password for verification
        new_password: New password to set

    Returns:
        Updated User object

    Raises:
        UserNotFoundError: If user doesn't exist
        CurrentPasswordIncorrectError: If current password is wrong
        ValidationError: If new password doesn't meet requirements
    """
    logger.info(f"Changing password for user ID {user_id}")

    # Get the user
    user = get_user_by_id(db, user_id)

    # Verify current password
    if not verify_password(current_password, user.password):
        logger.warning(
            f"Password change failed - incorrect current password for user {user.username}"
        )
        raise CurrentPasswordIncorrectError()

    # Validate new password
    validate_password(new_password)

    # Check that new password is different from current
    if verify_password(new_password, user.password):
        raise ValidationError("New password must be different from current password")

    # Update password
    user.password = hash_password(new_password)

    try:
        db.commit()
        db.refresh(user)
        logger.info(f"Successfully changed password for {user.username}")
        return user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Error changing password: {e}")
        raise DatabaseError("Unable to change password") from e
