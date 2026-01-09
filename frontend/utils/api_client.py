"""
Backend API Client
Wrapper for all FastAPI backend communication
"""
import requests
from typing import Optional, Dict, Any, List
from config import Config

class BackendAPI:
    """Backend API wrapper class"""
    
    def __init__(self, token: Optional[str] = None):
        self.base_url = Config.BACKEND_API_URL
        self.token = token
        self.headers = {}
        
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make GET request"""
        try:
            response = requests.get(
                f'{self.base_url}{endpoint}',
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Try to extract error message from response
            try:
                error_data = e.response.json()
                error_msg = error_data.get('detail', str(e))
                if isinstance(error_msg, list):
                    error_msg = ', '.join([err.get('msg', str(err)) for err in error_msg])
                return {'error': error_msg}
            except:
                return {'error': str(e)}
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    def _post(self, endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict:
        """Make POST request"""
        try:
            print(f"POST {self.base_url}{endpoint}")
            print(f"Data: {data}")
            print(f"Files: {files.keys() if files else None}")
            
            # When uploading files, don't set Content-Type header (let requests handle it)
            headers = self.headers.copy() if not files else {'Authorization': self.headers.get('Authorization')}
            
            response = requests.post(
                f'{self.base_url}{endpoint}',
                headers=headers,
                json=data if not files and data else None,
                files=files if files else None,
                data=data if files and data else None
            )
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Try to extract error message from response
            try:
                error_data = e.response.json()
                print(f"Error data: {error_data}")
                error_msg = error_data.get('detail', str(e))
                if isinstance(error_msg, list):
                    error_msg = ', '.join([err.get('msg', str(err)) for err in error_msg])
                return {'error': error_msg}
            except Exception as ex:
                print(f"Exception parsing error: {ex}")
                return {'error': str(e)}
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")
            return {'error': str(e)}
    
    def _put(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make PUT request"""
        try:
            response = requests.put(
                f'{self.base_url}{endpoint}',
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Try to extract error message from response
            try:
                error_data = e.response.json()
                error_msg = error_data.get('detail', str(e))
                if isinstance(error_msg, list):
                    error_msg = ', '.join([err.get('msg', str(err)) for err in error_msg])
                return {'error': error_msg}
            except:
                return {'error': str(e)}
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    def _delete(self, endpoint: str) -> Dict:
        """Make DELETE request"""
        try:
            response = requests.delete(
                f'{self.base_url}{endpoint}',
                headers=self.headers
            )
            response.raise_for_status()
            return {'success': True}
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    # Authentication endpoints
    def register(self, username: str, email: str, password: str, full_name: str, role: str) -> Dict:
        """Register a new user"""
        data = {
            'username': username,
            'email': email,
            'password': password,
            'full_name': full_name,
            'role': role
        }
        return self._post('/api/auth/register', data=data)
    
    def login(self, username: str, password: str) -> Dict:
        """Login user and get JWT token"""
        # Backend expects JSON data for login
        data = {
            'username': username,
            'password': password
        }
        return self._post('/api/auth/login', data=data)
    
    def logout(self) -> Dict:
        """Logout user"""
        return self._post('/api/auth/logout')
    
    # Works endpoints
    def get_works(self, skip: int = 0, limit: int = 100) -> Dict:
        """Get list of works"""
        return self._get('/api/works', params={'skip': skip, 'limit': limit})
    
    def create_work(self, name: str, description: str = '') -> Dict:
        """Create a new work"""
        data = {
            'name': name,
            'description': description
        }
        return self._post('/api/works', data=data)
    
    def get_work(self, work_id: int) -> Dict:
        """Get work details"""
        return self._get(f'/api/works/{work_id}')
    
    def update_work(self, work_id: int, name: str, description: str = '', status: str = 'active') -> Dict:
        """Update work"""
        data = {
            'name': name,
            'description': description,
            'status': status
        }
        return self._put(f'/api/works/{work_id}', data=data)
    
    def delete_work(self, work_id: int) -> Dict:
        """Delete work"""
        return self._delete(f'/api/works/{work_id}')
    
    # Extraction endpoints
    def start_extraction(self, work_id: int, file) -> Dict:
        """Start extraction process"""
        # Read file content and prepare for upload
        file.seek(0)  # Reset file pointer to beginning
        files = {
            'file': (file.filename, file.read(), file.content_type or 'application/pdf')
        }
        return self._post(f'/api/works/{work_id}/extraction/start', files=files)
    
    def get_extraction_status(self, extraction_id: int) -> Dict:
        """Get extraction status"""
        return self._get(f'/api/extractions/{extraction_id}/status')
    
    # Reports endpoints
    def get_reports(self, work_id: int) -> Dict:
        """Get work reports"""
        return self._get(f'/api/works/{work_id}/reports')
    
    def download_excel(self, work_id: int, version: int) -> bytes:
        """Download Excel file"""
        try:
            response = requests.get(
                f'{self.base_url}/api/works/{work_id}/excel/{version}/download',
                headers=self.headers
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            return None
    
    def update_excel_data(self, work_id: int, version: int, data: List[Dict]) -> Dict:
        """Update Excel data"""
        return self._put(f'/api/works/{work_id}/excel/{version}/data', data={'components': data})
    
    def generate_powerpoint(self, work_id: int) -> Dict:
        """Generate PowerPoint report"""
        return self._post(f'/api/works/{work_id}/generate-powerpoint')
    
    def download_powerpoint(self, work_id: int, version: int) -> bytes:
        """Download PowerPoint file"""
        try:
            response = requests.get(
                f'{self.base_url}/api/works/{work_id}/powerpoint/{version}/download',
                headers=self.headers
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            return None
    
    # Analytics endpoints
    def get_analytics(self, work_id: int) -> Dict:
        """Get work analytics"""
        return self._get(f'/api/works/{work_id}/analytics')
    
    # Component bulk update
    def update_components_bulk(self, work_id: int, changes: Dict) -> Dict:
        """Update multiple components at once
        
        Args:
            work_id: Work ID
            changes: Dict of {component_id: {field: value, ...}}
        """
        return self._post(f'/api/works/{work_id}/components/bulk-update', data={'changes': changes})
    
    # Work history endpoint
    def get_work_history(self, days: int = 7, limit: int = 100) -> Dict:
        """Get work activity history for recent days"""
        return self._get('/api/history/period', params={'days': days, 'limit': limit})
    
    # Equipment endpoints
    def get_equipment_list(self, work_id: int) -> Dict:
        """Get all equipment for a work"""
        return self._get(f'/api/equipments/work/{work_id}')
    
    def get_equipment_detail(self, equipment_id: int) -> Dict:
        """Get equipment details with components"""
        return self._get(f'/api/equipments/{equipment_id}')
    
    # Reports - Template Upload
    def upload_excel_template(self, work_id: int, file) -> Dict:
        """Upload Excel masterfile template for work"""
        file.seek(0)
        files = {
            'file': (file.filename, file.read(), file.content_type or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        return self._post(f'/api/reports/{work_id}/templates/excel', files=files)
    
    def upload_powerpoint_template(self, work_id: int, file) -> Dict:
        """Upload PowerPoint template for work"""
        file.seek(0)
        files = {
            'file': (file.filename, file.read(), file.content_type or 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
        }
        return self._post(f'/api/reports/{work_id}/templates/powerpoint', files=files)
    
    # Reports - Generation
    def generate_excel_report(self, work_id: int) -> Dict:
        """Generate Excel report from extracted data"""
        return self._post(f'/api/reports/{work_id}/reports/generate-excel')
    
    def generate_ppt_report(self, work_id: int) -> Dict:
        """Generate PowerPoint report from extracted data"""
        return self._post(f'/api/reports/{work_id}/reports/generate-powerpoint')
    
    # Reports - List and Download
    def get_work_reports(self, work_id: int) -> Dict:
        """Get all generated reports for a work"""
        return self._get(f'/api/reports/{work_id}/reports')
    
    def download_report(self, work_id: int, file_id: int) -> Dict:
        """Get download URL for a specific report"""
        return self._get(f'/api/reports/{work_id}/reports/{file_id}/download')
    
    def download_report_file(self, work_id: int, file_id: int) -> bytes:
        """Download a report file directly"""
        try:
            # First get the download URL
            url_response = self._get(f'/api/reports/{work_id}/reports/{file_id}/download')
            if 'error' in url_response or 'file_url' not in url_response:
                return None
            
            # Download from Cloudinary URL
            response = requests.get(url_response['file_url'])
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException:
            return None
    
    # Analytics - Using actual backend endpoints
    def get_extraction_analytics(self, period: str = 'last_30_days') -> Dict:
        """Get extraction status metrics for analytics dashboard"""
        return self._get('/api/analytics/extractions/status', params={'period': period})
    
    def get_works_status(self, period: str = 'last_30_days') -> Dict:
        """Get works status metrics"""
        return self._get('/api/analytics/works/status', params={'period': period})
    
    def get_equipment_count(self, period: str = 'last_30_days') -> Dict:
        """Get equipment count metrics"""
        return self._get('/api/analytics/equipment/count', params={'period': period})
    
    def get_components_count(self, period: str = 'last_30_days') -> Dict:
        """Get components count metrics"""
        return self._get('/api/analytics/components/count', params={'period': period})
    
    # Extraction status (individual)
    def get_extraction_status(self, extraction_id: int) -> Dict:
        """Get individual extraction progress and status"""
        return self._get(f'/api/extractions/{extraction_id}/status')
    
    # History - Activity logs (using actual backend endpoints)
    def get_work_history(self, days: int = 7) -> Dict:
        """Get work activity history for recent days"""
        return self._get('/api/history/period', params={'days': days})
    
    def get_work_activities(self, work_id: int) -> Dict:
        """Get activity logs for a specific work"""
        return self._get(f'/api/history/work/{work_id}')
