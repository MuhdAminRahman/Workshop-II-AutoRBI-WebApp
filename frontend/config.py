"""
Flask Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # Backend API (Deployed on Render)
    # To use LOCAL backend: Change to 'http://localhost:8000' (must have backend running locally)
    # To use DEPLOYED backend: Use 'https://workshop-ii-autorbi-webapp.onrender.com'
    BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'https://workshop-ii-autorbi-webapp.onrender.com')
    BACKEND_WS_URL = os.getenv('BACKEND_WS_URL', 'wss://workshop-ii-autorbi-webapp.onrender.com')
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # File Upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Pagination
    ITEMS_PER_PAGE = 10

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
