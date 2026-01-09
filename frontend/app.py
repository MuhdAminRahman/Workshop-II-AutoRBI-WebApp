"""
AutoRBI Web App - Flask Frontend
Main application entry point
"""
from flask import Flask, render_template, session
from flask_socketio import SocketIO
from config import Config
import os

# Import blueprints
from routes.main import main_bp
from routes.auth import auth_bp
from routes.works import works_bp
from routes.extract import extract_bp
from routes.reports import reports_bp
from routes.analytics import analytics_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize SocketIO for WebSocket support
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(works_bp, url_prefix='/works')
    app.register_blueprint(extract_bp, url_prefix='/extract')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('base.html'), 500
    
    # Template filters
    @app.template_filter('datetime')
    def format_datetime(value):
        """Format datetime for display"""
        if value is None:
            return ""
        # If value is already a string, return it as is
        if isinstance(value, str):
            # Try to parse and reformat if needed
            try:
                from datetime import datetime
                # Backend returns ISO format like "2024-01-06T12:30:45"
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M')
            except:
                # If parsing fails, return original string
                return value
        # If it's a datetime object, format it
        return value.strftime('%Y-%m-%d %H:%M')
    
    @app.template_filter('filesize')
    def format_filesize(size):
        """Format file size in bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @app.template_filter('status_badge')
    def get_status_badge_class(status):
        """Get Bootstrap badge class based on status"""
        status_map = {
            'active': 'success',
            'completed': 'primary',
            'pending': 'warning',
            'in_progress': 'info',
            'failed': 'danger',
            'cancelled': 'secondary'
        }
        return status_map.get(status, 'secondary')
    
    return app, socketio

# Create app instance for production (gunicorn)
app, socketio = create_app()

if __name__ == '__main__':
    # Development server
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
