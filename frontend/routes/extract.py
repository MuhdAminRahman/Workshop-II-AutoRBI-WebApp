"""
Extraction Routes
File upload and extraction progress
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from utils.auth_middleware import login_required, get_auth_token
from utils.api_client import BackendAPI
from utils.helpers import parse_error_message, allowed_file
from config import Config

extract_bp = Blueprint('extract', __name__)

@extract_bp.route('/')
@login_required
def index():
    """Extraction page"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get list of works for dropdown
    response = api.get_works()
    works = response.get('items', []) if 'items' in response else response if isinstance(response, list) else []
    
    return render_template('extract/index.html', works=works)

@extract_bp.route('/start', methods=['POST'])
@login_required
def start_extraction():
    """Start extraction process"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    work_id = request.form.get('work_id')
    
    if not work_id:
        flash('Please select a work project.', 'danger')
        return redirect(url_for('extract.index'))
    
    # Check if file is present
    if 'file' not in request.files:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('extract.index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('extract.index'))
    
    if not allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
        flash('Only PDF files are allowed.', 'danger')
        return redirect(url_for('extract.index'))
    
    # Upload file and start extraction
    response = api.start_extraction(int(work_id), file)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
        return redirect(url_for('extract.index'))
    
    extraction_id = response.get('extraction_id')
    
    flash('Extraction started successfully!', 'success')
    return redirect(url_for('extract.progress', extraction_id=extraction_id))

@extract_bp.route('/progress/<int:extraction_id>')
@login_required
def progress(extraction_id):
    """Show extraction progress"""
    token = get_auth_token()
    
    return render_template(
        'extract/progress.html',
        extraction_id=extraction_id,
        ws_url=Config.BACKEND_WS_URL
    )

@extract_bp.route('/status/<int:extraction_id>')
@login_required
def get_status(extraction_id):
    """Get extraction status (AJAX endpoint)"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    response = api.get_extraction_status(extraction_id)
    
    return jsonify(response)
