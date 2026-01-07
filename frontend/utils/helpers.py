"""
Helper Functions
Utility functions for the application
"""
from datetime import datetime
from typing import Optional

def format_datetime(dt: datetime, format: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format datetime to string"""
    if dt is None:
        return ''
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    return dt.strftime(format)

def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable"""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"

def get_status_badge_class(status: str) -> str:
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

def calculate_progress_percentage(processed: int, total: int) -> int:
    """Calculate progress percentage"""
    if total == 0:
        return 0
    return int((processed / total) * 100)

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def parse_error_message(error_response: dict) -> str:
    """Parse error message from API response"""
    if isinstance(error_response, dict):
        if 'detail' in error_response:
            return str(error_response['detail'])
        elif 'error' in error_response:
            return str(error_response['error'])
        elif 'message' in error_response:
            return str(error_response['message'])
    return 'An unexpected error occurred'
