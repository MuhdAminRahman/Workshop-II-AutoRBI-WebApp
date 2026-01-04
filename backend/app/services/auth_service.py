"""
Authentication Service
Password hashing, JWT token generation, user validation
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from bcrypt import hashpw, gensalt, checkpw
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole
from app.schemas.user import UserLoginRequest, UserRegisterRequest

logger = logging.getLogger(__name__)

# ============================================================================
# PASSWORD HASHING
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password (safe to store in database)
    
    Example:
        hashed = hash_password("MyPassword123")
        # Returns: $2b$12$abcdef... (long string)
    """
    salt = gensalt(rounds=12)  # 12 rounds is good balance of security/speed
    hashed = hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password from user
        hashed_password: Hashed password from database
    
    Returns:
        True if passwords match, False otherwise
    
    Example:
        if verify_password("MyPassword123", user.password_hash):
            print("Login successful")
    """
    return checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User ID to encode in token
        expires_delta: Custom expiration time (default: 24 hours)
    
    Returns:
        JWT token string
    
    Example:
        token = create_access_token(user_id=1)
        # Returns: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    

    # Payload is what goes in the token
    to_encode = {
        "sub": str(user_id),  # "sub" (subject) is standard JWT claim for user ID
        "exp": expire,   # "exp" is standard claim for expiration
    }
    
    # Sign the token with secret key
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    logger.debug(f"Created token for user {user_id}, expires at {expire}")
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[int]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        User ID if valid, None if invalid/expired
    
    Example:
        user_id = decode_access_token("eyJhbGci...")
        if user_id:
            print(f"Token belongs to user {user_id}")
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        
        if user_id is None:
            return None
        
        return user_id
    
    except JWTError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None


# ============================================================================
# USER REGISTRATION
# ============================================================================


def register_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    full_name: str
) -> tuple[Optional[User], Optional[str]]:
    """
    Register a new user.
    
    Args:
        db: Database session
        username: Unique username
        email: User email
        password: Plain text password
        full_name: User's full name
    
    Returns:
        (User object, error message)
        If successful: (user, None)
        If failed: (None, error_message)
    
    Example:
        user, error = register_user(
            db=db,
            username="john",
            email="john@example.com",
            password="SecurePass123",
            full_name="John Doe"
        )
        if error:
            print(f"Registration failed: {error}")
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return None, "Username already exists"
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        return None, "Email already registered"
    
    # Hash password
    hashed_password = hash_password(password)
    
    # Create new user
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        full_name=full_name,
        role=UserRole.ENGINEER,  # Default role
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"✅ User registered: {username}")
        return new_user, None
    
    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed: {str(e)}")
        return None, "Registration failed. Please try again."


# ============================================================================
# USER LOGIN
# ============================================================================


def authenticate_user(
    db: Session,
    username: str,
    password: str
) -> tuple[Optional[User], Optional[str]]:
    """
    Authenticate a user by username and password.
    
    Args:
        db: Database session
        username: Username
        password: Plain text password
    
    Returns:
        (User object, error message)
        If successful: (user, None)
        If failed: (None, error_message)
    
    Example:
        user, error = authenticate_user(db=db, username="john", password="SecurePass123")
        if user:
            print(f"Login successful: {user.full_name}")
        else:
            print(f"Login failed: {error}")
    """
    # Find user by username
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        logger.warning(f"❌ Login failed: User '{username}' not found")
        return None, "Invalid username or password"
    
    # Verify password
    if not verify_password(password, user.password_hash):
        logger.warning(f"❌ Login failed: Wrong password for user '{username}'")
        return None, "Invalid username or password"
    
    logger.info(f"✅ User logged in: {username}")
    return user, None


# ============================================================================
# GET USER FROM TOKEN
# ============================================================================


def get_user_from_token(db: Session, token: str) -> Optional[User]:
    """
    Get user object from JWT token.
    
    Args:
        db: Database session
        token: JWT token string
    
    Returns:
        User object if valid, None if invalid
    
    Example:
        user = get_user_from_token(db=db, token="eyJhbGci...")
        if user:
            print(f"Token belongs to {user.full_name}")
    """
    user_id = decode_access_token(token)
    
    if user_id is None:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    
    return user


# ============================================================================
# SUMMARY OF FUNCTIONS
# ============================================================================

"""
FLOW DIAGRAM:

REGISTRATION:
1. User provides: username, email, password, full_name
2. register_user() is called
3. Check if username/email exists
4. Hash password with bcrypt
5. Create user in database
6. Return user object

LOGIN:
1. User provides: username, password
2. authenticate_user() is called
3. Find user by username
4. Verify password with bcrypt
5. Return user object
6. generate token: create_access_token(user.id)
7. Return token to client

SUBSEQUENT REQUESTS:
1. Client sends token in Authorization header
2. Decode token with decode_access_token()
3. Get user from database
4. Proceed with request
"""