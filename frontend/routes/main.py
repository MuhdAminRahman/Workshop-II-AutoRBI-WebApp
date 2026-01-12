"""
Main Routes
Landing page and dashboard
"""
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from utils.auth_middleware import login_required, get_auth_token
from utils.api_client import BackendAPI
from utils.helpers import get_status_badge_class, parse_error_message
import os

main_bp = Blueprint('main', __name__)

# Template storage (in production, use database or cloud storage)
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates_uploads')
os.makedirs(TEMPLATES_DIR, exist_ok=True)

@main_bp.route('/')
def index():
    """Redirect to login or dashboard"""
    # Redirect to dashboard if already logged in
    if 'token' in session:
        return redirect(url_for('main.dashboard'))
    # Otherwise redirect to login
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - different view for admin and users"""
    from datetime import datetime
    
    user_role = session.get('user', {}).get('role', 'Engineer')
    
    # Redirect admins to admin panel
    if user_role == 'Admin':
        return redirect(url_for('admin.admin_dashboard'))
    
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get works assigned to the engineer (backend filters by collaborators)
    works_response = api.get_works(skip=0, limit=100)
    works = works_response.get('works', []) if isinstance(works_response, dict) else []
    
    # Engineer dashboard - works already filtered by backend to only show their assigned works
    total_works = len(works)
    active_works = sum(1 for w in works if w.get('status') == 'active')
    completed_works = sum(1 for w in works if w.get('status') == 'completed')
    
    # Get total equipment from all works and calculate health score
    total_equipment = 0
    total_extracted_equipment = 0
    
    # Critical fields for RBI data readiness
    critical_fields = ['fluid', 'material_spec', 'design_temp', 'design_pressure']
    
    all_components = []
    
    try:
        # Get equipment and components from each work
        for work in works:
            work_id = work.get('id')
            if work_id:
                try:
                    work_detail = api.get_work(work_id)
                    equipment_list = work_detail.get('equipment', [])
                    
                    # Add equipment count to work object for display
                    work['equipment_count'] = len(equipment_list)
                    
                    for equipment in equipment_list:
                        total_equipment += 1
                        # Check if equipment has been extracted (has components)
                        components = equipment.get('components', [])
                        if components:
                            total_extracted_equipment += 1
                            all_components.extend(components)
                except:
                    work['equipment_count'] = 0
                    continue
    except:
        pass
    
    # Calculate health score based on extraction rate and completeness
    extraction_rate = (total_extracted_equipment / total_equipment * 100) if total_equipment > 0 else 0
    
    # Calculate completeness rate for critical fields
    filled_critical = 0
    if all_components:
        for component in all_components:
            for field in critical_fields:
                value = component.get(field)
                if value and str(value).strip() and str(value).strip().lower() not in ['none', 'n/a', '']:
                    filled_critical += 1
    
    total_critical_fields = len(all_components) * len(critical_fields)
    completeness_rate = (filled_critical / total_critical_fields * 100) if total_critical_fields > 0 else 0
    
    # Health score: 40% extraction + 40% completeness + 20% quality (assume high quality)
    # Quality score set to 20 (full marks, no corrections assumed)
    avg_health_score = round((extraction_rate * 0.4) + (completeness_rate * 0.4) + 20, 1)
    
    return render_template(
        'dashboard/index.html',
        works=works[:5] if works else [],  # Show only 5 most recent
        total_works=total_works,
        active_works=active_works,
        completed_works=completed_works,
        total_equipment=total_equipment,
        avg_health_score=avg_health_score,
        now=datetime.now(),
        get_status_badge_class=get_status_badge_class
    )

@main_bp.route('/admin/upload-template', methods=['POST'])
@login_required
def upload_template():
    """Upload master templates (Excel and PowerPoint)"""
    user_role = session.get('user', {}).get('role', 'Engineer')
    
    # Only admin can upload templates
    if user_role != 'Admin':
        flash('Only administrators can upload templates.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    excel_file = request.files.get('excel_file')
    ppt_file = request.files.get('ppt_file')
    
    uploaded = False
    
    # Handle Excel template
    if excel_file and excel_file.filename:
        if excel_file.filename.lower().endswith(('.xlsx', '.xls')):
            excel_path = os.path.join(TEMPLATES_DIR, 'master_template.xlsx')
            excel_file.save(excel_path)
            flash('Excel template uploaded successfully!', 'success')
            uploaded = True
        else:
            flash('Excel file must be .xlsx or .xls format.', 'danger')
    
    # Handle PowerPoint template
    if ppt_file and ppt_file.filename:
        if ppt_file.filename.lower().endswith(('.pptx', '.ppt')):
            ppt_path = os.path.join(TEMPLATES_DIR, 'master_template.pptx')
            ppt_file.save(ppt_path)
            flash('PowerPoint template uploaded successfully!', 'success')
            uploaded = True
        else:
            flash('PowerPoint file must be .pptx or .ppt format.', 'danger')
    
    if not uploaded:
        flash('No valid templates were uploaded.', 'warning')
    
    return redirect(url_for('main.dashboard'))

@main_bp.route('/admin/templates/download/<template_type>')
@login_required
def download_template(template_type):
    """Download master template"""
    user_role = session.get('user', {}).get('role', 'Engineer')
    
    # Only admin can download templates
    if user_role != 'Admin':
        flash('Only administrators can access templates.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if template_type == 'excel':
        filename = 'master_template.xlsx'
    elif template_type == 'ppt':
        filename = 'master_template.pptx'
    else:
        flash('Invalid template type.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    filepath = os.path.join(TEMPLATES_DIR, filename)
    
    if not os.path.exists(filepath):
        flash(f'{template_type.upper()} template not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    from flask import send_file
    return send_file(filepath, as_attachment=True, download_name=filename)
