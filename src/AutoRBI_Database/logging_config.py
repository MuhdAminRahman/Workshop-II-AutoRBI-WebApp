"""
Logging configuration for AutoRBI application.

This module sets up application-wide logging with both file and console output.
Different modules can get their own loggers while sharing the same configuration.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


# Determine the logs directory
# This assumes the structure: AutoRBI/src/AutoRBI_Database/logging_config.py
# Logs will be stored in: AutoRBI/logs/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Create logs directory if it doesn't exist
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)


# Log file paths
APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")
AUTH_LOG_FILE = os.path.join(LOGS_DIR, "auth.log")
ERROR_LOG_FILE = os.path.join(LOGS_DIR, "errors.log")


# Log format - includes timestamp, logger name, level, and message
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level=logging.INFO):
    """
    Set up application-wide logging configuration.
    
    This creates handlers for:
    - Console output (INFO and above)
    - General application log file (INFO and above)
    - Error log file (ERROR and above)
    
    Args:
        log_level: Minimum level to log (default: logging.INFO)
    """
    
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Console handler - shows INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # App log file handler - all logs INFO and above
    # Rotating file handler - max 10MB per file, keep 5 backup files
    app_file_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    app_file_handler.setLevel(logging.INFO)
    app_file_handler.setFormatter(formatter)
    
    # Error log file handler - only ERROR and CRITICAL
    error_file_handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file_handler)
    root_logger.addHandler(error_file_handler)
    
    # Log startup message
    root_logger.info("=" * 80)
    root_logger.info(f"AutoRBI Application Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    root_logger.info(f"Log Level: {logging.getLevelName(log_level)}")
    root_logger.info(f"Logs Directory: {LOGS_DIR}")
    root_logger.info("=" * 80)


def get_logger(name):
    """
    Get a logger for a specific module.
    
    Args:
        name: Name for the logger (typically __name__ of the module)
        
    Returns:
        Logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("This is an info message")
        >>> logger.error("This is an error message")
    """
    return logging.getLogger(name)


def setup_auth_logger():
    """
    Set up a separate logger specifically for authentication events.
    
    This creates a dedicated log file for authentication-related events
    (login attempts, registrations, etc.) for security auditing.
    
    Returns:
        Logger instance for authentication
    """
    
    logger = logging.getLogger("auth")
    logger.setLevel(logging.INFO)
    
    # Prevent propagation to root logger (we want auth logs separate)
    logger.propagate = False
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Auth file handler
    auth_file_handler = RotatingFileHandler(
        AUTH_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,  # Keep more backups for security logs
        encoding='utf-8'
    )
    auth_file_handler.setLevel(logging.INFO)
    auth_file_handler.setFormatter(formatter)
    
    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(auth_file_handler)
    logger.addHandler(console_handler)
    
    # Log startup
    logger.info("=" * 80)
    logger.info("Authentication Logger Initialized")
    logger.info(f"Auth Log File: {AUTH_LOG_FILE}")
    logger.info("=" * 80)
    
    return logger


# Initialize logging when module is imported
# You can change log_level to logging.DEBUG for more detailed logs during development
setup_logging(log_level=logging.INFO)

# Create the auth logger
auth_logger = setup_auth_logger()


# Usage examples (for documentation):
"""
USAGE EXAMPLES:

1. In any module, import and use the logger:

    from AutoRBI_Database.logging_config import get_logger
    
    logger = get_logger(__name__)
    
    logger.debug("Detailed debug information")
    logger.info("General information")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical error!")

2. For authentication events, use the auth logger:

    from AutoRBI_Database.logging_config import auth_logger
    
    auth_logger.info(f"Login attempt for user: {username}")
    auth_logger.warning(f"Failed login attempt: {username}")
    auth_logger.error(f"Account locked: {username}")

3. Log exceptions with full traceback:

    try:
        risky_operation()
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        # exc_info=True includes the full stack trace

LOG LEVELS (when to use each):

- DEBUG: Detailed information for diagnosing problems (variable values, function calls)
  Example: "Fetching user 'john' from database"
  
- INFO: General informational messages about normal operation
  Example: "User 'john' logged in successfully"
  
- WARNING: Something unexpected happened but the app can continue
  Example: "Login attempt on inactive account"
  
- ERROR: Something failed but the app can continue
  Example: "Failed to connect to database"
  
- CRITICAL: Serious error, app might crash
  Example: "Database connection pool exhausted"
"""
