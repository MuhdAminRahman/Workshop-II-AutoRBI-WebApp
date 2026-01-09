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
    token = get_auth_token()
    api = BackendAPI(token)
    user_role = session.get('user', {}).get('role', 'Engineer')
    
    # Get works
    works_response = api.get_works(skip=0, limit=100)
    works = works_response.get('works', []) if isinstance(works_response, dict) else []
    
    if user_role == 'Admin':
        # Admin: Show system-wide statistics
        total_works = len(works)
        completed_works = sum(1 for w in works if w.get('status') == 'completed')
        in_progress_works = sum(1 for w in works if w.get('status') == 'in_progress')
        active_users = len(set(w.get('owner_id') for w in works if w.get('owner_id')))
        
        # Check for uploaded templates
        excel_template = None
        ppt_template = None
        if os.path.exists(os.path.join(TEMPLATES_DIR, 'master_template.xlsx')):
            excel_template = {'filename': 'master_template.xlsx'}
        if os.path.exists(os.path.join(TEMPLATES_DIR, 'master_template.pptx')):
            ppt_template = {'filename': 'master_template.pptx'}
        
        return render_template(
            'dashboard/admin.html',
            works=works,
            total_works=total_works,
            completed_works=completed_works,
            in_progress_works=in_progress_works,
            active_users=active_users,
            excel_template=excel_template,
            ppt_template=ppt_template,
            get_status_badge_class=get_status_badge_class
        )
    else:
        # Engineer: Show their own works analysis
        total_works = len(works)
        active_works = sum(1 for w in works if w.get('status') == 'active')
        completed_works = sum(1 for w in works if w.get('status') == 'completed')
        
        # Get total equipment from backend analytics API
        total_equipment = 0
        try:
            equipment_response = api.get_equipment_count(period='all_time')
            if equipment_response and 'total' in equipment_response:
                total_equipment = equipment_response['total']
        except:
            # If API fails, use 0
            total_equipment = 0
        
        # Calculate average health score based on data completeness
        avg_health_score = 0
        try:
            # Required fields for each component
            required_fields = ['fluid', 'material_spec', 'material_grade', 'insulation', 
                             'design_temp', 'design_pressure', 'operating_temp', 'operating_pressure']
            
            total_fields = 0
            filled_fields = 0
            
            # Get all components from all works to calculate completeness
            for work in works:
                work_id = work.get('id')
                if work_id:
                    try:
                        review_data = api.get_extraction_review(work_id)
                        if review_data and 'equipment' in review_data:
                            for equipment in review_data['equipment']:
                                components = equipment.get('components', [])
                                for component in components:
                                    total_fields += len(required_fields)
                                    # Count filled fields
                                    for field in required_fields:
                                        value = component.get(field)
                                        if value and str(value).strip() and str(value).strip().lower() != 'none':
                                            filled_fields += 1
                    except:
                        pass
            
            # Calculate percentage
            if total_fields > 0:
                avg_health_score = round((filled_fields / total_fields) * 100)
            else:
                avg_health_score = 75  # Default if no data
                
        except:
            avg_health_score = 75  # Default on error
        
        return render_template(
            'dashboard/index.html',
            works=works[:5],  # Show only 5 most recent
            total_works=total_works,
            active_works=active_works,
            completed_works=completed_works,
            total_equipment=total_equipment,
            avg_health_score=avg_health_score,
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
