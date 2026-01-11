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
    
    # Get all generated reports
    reports_response = api.get_work_reports(work_id)
    reports = reports_response.get('reports', []) if 'error' not in reports_response else []
    
    # Separate Excel and PowerPoint reports
    excel_reports = [r for r in reports if r.get('file_type') == 'excel']
    ppt_reports = [r for r in reports if r.get('file_type') == 'powerpoint']
    
    # Check if templates are uploaded
    has_excel_template = work.get('excel_masterfile_url') is not None
    has_ppt_template = work.get('ppt_template_url') is not None
    
    return render_template(
        'reports/view.html',
        work=work,
        excel_reports=excel_reports,
        ppt_reports=ppt_reports,
        has_excel_template=has_excel_template,
        has_ppt_template=has_ppt_template
    )

@reports_bp.route('/<int:work_id>/powerpoint/generate', methods=['POST'])
@login_required
def generate_powerpoint(work_id):
    """Generate PowerPoint report"""
    from flask import session
    token = get_auth_token()
    api = BackendAPI(token)
    current_user = session.get('user', {})
    user_id = current_user.get('id')
    
    response = api.generate_ppt_report(work_id)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
    else:
        version = response.get('version', 'new')
        flash(f'PowerPoint report version {version} generated successfully!', 'success')
        
        # Log activity
        try:
            if user_id:
                api.log_activity(
                    user_id=user_id,
                    entity_type='file',
                    entity_id=response.get('file_id', 0),
                    action='created',
                    data={
                        'work_id': work_id,
                        'file_type': 'powerpoint',
                        'version': version,
                        'report_type': 'PowerPoint Report'
                    }
                )
        except Exception as e:
            print(f"Failed to log activity: {e}")
    
    return redirect(url_for('reports.view_reports', work_id=work_id))

@reports_bp.route('/<int:work_id>/excel/generate', methods=['POST'])
@login_required
def generate_excel_report(work_id):
    """Generate Excel report"""
    from flask import session
    token = get_auth_token()
    api = BackendAPI(token)
    current_user = session.get('user', {})
    user_id = current_user.get('id')
    
    response = api.generate_excel_report(work_id)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
    else:
        version = response.get('version', 'new')
        flash(f'Excel report version {version} generated successfully!', 'success')
        
        # Log activity
        try:
            if user_id:
                api.log_activity(
                    user_id=user_id,
                    entity_type='file',
                    entity_id=response.get('file_id', 0),
                    action='created',
                    data={
                        'work_id': work_id,
                        'file_type': 'excel',
                        'version': version,
                        'report_type': 'Excel Report'
                    }
                )
        except Exception as e:
            print(f"Failed to log activity: {e}")
    
    return redirect(url_for('reports.view_reports', work_id=work_id))

@reports_bp.route('/<int:work_id>/templates/excel/upload', methods=['POST'])
@login_required
def upload_excel_template(work_id):
    """Upload Excel template for work"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Check if file was uploaded
    if 'file' not in request.files:
        flash('No file uploaded', 'danger')
        return redirect(url_for('reports.view_reports', work_id=work_id))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('reports.view_reports', work_id=work_id))
    
    # Validate Excel file
    if not file.filename.lower().endswith('.xlsx'):
        flash('Only Excel files (.xlsx) are allowed', 'danger')
        return redirect(url_for('reports.view_reports', work_id=work_id))
    
    # Upload to backend
    response = api.upload_excel_template(work_id, file)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
    else:
        flash('Excel template uploaded successfully!', 'success')
    
    return redirect(url_for('reports.view_reports', work_id=work_id))

@reports_bp.route('/<int:work_id>/templates/powerpoint/upload', methods=['POST'])
@login_required
def upload_powerpoint_template(work_id):
    """Upload PowerPoint template for work"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Check if file was uploaded
    if 'file' not in request.files:
        flash('No file uploaded', 'danger')
        return redirect(url_for('reports.view_reports', work_id=work_id))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('reports.view_reports', work_id=work_id))
    
    # Validate PowerPoint file
    if not file.filename.lower().endswith('.pptx'):
        flash('Only PowerPoint files (.pptx) are allowed', 'danger')
        return redirect(url_for('reports.view_reports', work_id=work_id))
    
    # Upload to backend
    response = api.upload_powerpoint_template(work_id, file)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
    else:
        flash('PowerPoint template uploaded successfully!', 'success')
    
    return redirect(url_for('reports.view_reports', work_id=work_id))

@reports_bp.route('/<int:work_id>/reports/<int:file_id>/download')
@login_required
def download_report(work_id, file_id):
    """Download report file"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # First, get the file metadata to determine type
    reports_response = api.get_work_reports(work_id)
    
    file_type = None
    version = None
    
    if 'reports' in reports_response:
        for report in reports_response['reports']:
            if report.get('file_id') == file_id:
                file_type = report.get('file_type')
                version = report.get('version', file_id)
                break
    
    # Download the file
    file_content = api.download_report_file(work_id, file_id)
    
    if not file_content:
        flash('Failed to download report.', 'danger')
        return redirect(url_for('reports.view_reports', work_id=work_id))
    
    # Determine filename and mimetype based on file type
    if file_type == 'powerpoint':
        filename = f'work_{work_id}_presentation_v{version}.pptx'
        mimetype = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    else:  # Default to excel
        filename = f'work_{work_id}_report_v{version}.xlsx'
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    return send_file(
        BytesIO(file_content),
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )
