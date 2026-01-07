"""
Reports Routes
Reports management and Excel/PowerPoint downloads
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from io import BytesIO
from utils.auth_middleware import login_required, get_auth_token
from utils.api_client import BackendAPI
from utils.helpers import parse_error_message

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    """Reports list page"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get all works
    response = api.get_works()
    
    # Handle different response formats
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
        works = []
    elif 'works' in response:
        works = response['works']
    elif 'items' in response:
        works = response['items']
    elif isinstance(response, list):
        works = response
    else:
        works = []
    
    return render_template('reports/index.html', works=works)

@reports_bp.route('/<int:work_id>')
@login_required
def view_reports(work_id):
    """View reports for a specific work"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get work details
    work_response = api.get_work(work_id)
    
    if 'error' in work_response:
        flash(parse_error_message(work_response), 'danger')
        return redirect(url_for('reports.index'))
    
    # Extract work from response (it may be nested)
    work = work_response.get('work', work_response)
    
    # Get reports
    reports_response = api.get_reports(work_id)
    
    reports = reports_response if not 'error' in reports_response else {}
    
    return render_template(
        'reports/view.html',
        work=work,
        reports=reports
    )

@reports_bp.route('/<int:work_id>/excel/<int:version>/download')
@login_required
def download_excel(work_id, version):
    """Download Excel file"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    file_content = api.download_excel(work_id, version)
    
    if not file_content:
        flash('Failed to download Excel file.', 'danger')
        return redirect(url_for('reports.view_reports', work_id=work_id))
    
    return send_file(
        BytesIO(file_content),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'work_{work_id}_v{version}.xlsx'
    )

@reports_bp.route('/<int:work_id>/excel/<int:version>/edit')
@login_required
def edit_excel(work_id, version):
    """Edit Excel data"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get work details
    work_response = api.get_work(work_id)
    
    if 'error' in work_response:
        flash(parse_error_message(work_response), 'danger')
        return redirect(url_for('reports.view_reports', work_id=work_id))
    
    # Extract work from response
    work = work_response.get('work', work_response)
    
    return render_template(
        'reports/editor.html',
        work=work,
        version=version
    )

@reports_bp.route('/<int:work_id>/excel/<int:version>/update', methods=['POST'])
@login_required
def update_excel(work_id, version):
    """Update Excel data"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get JSON data from request
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    response = api.update_excel_data(work_id, version, data.get('components', []))
    
    if 'error' in response:
        return jsonify({'error': parse_error_message(response)}), 400
    
    return jsonify({'success': True, 'message': 'Data updated successfully'})

@reports_bp.route('/<int:work_id>/powerpoint/generate', methods=['POST'])
@login_required
def generate_powerpoint(work_id):
    """Generate PowerPoint report"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    response = api.generate_powerpoint(work_id)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
    else:
        flash('PowerPoint generated successfully!', 'success')
    
    return redirect(url_for('reports.view_reports', work_id=work_id))

@reports_bp.route('/<int:work_id>/powerpoint/<int:version>/download')
@login_required
def download_powerpoint(work_id, version):
    """Download PowerPoint file"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    file_content = api.download_powerpoint(work_id, version)
    
    if not file_content:
        flash('Failed to download PowerPoint file.', 'danger')
        return redirect(url_for('reports.view_reports', work_id=work_id))
    
    return send_file(
        BytesIO(file_content),
        mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
        as_attachment=True,
        download_name=f'work_{work_id}_v{version}.pptx'
    )
