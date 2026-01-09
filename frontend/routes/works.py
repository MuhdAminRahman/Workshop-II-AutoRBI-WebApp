"""
Works Routes
CRUD operations for works
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from utils.auth_middleware import login_required, get_auth_token
from utils.api_client import BackendAPI
from utils.helpers import parse_error_message, get_status_badge_class

works_bp = Blueprint('works', __name__)

@works_bp.route('/')
@login_required
def list_works():
    """List all works"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    skip = (page - 1) * per_page
    
    # Get works from API
    response = api.get_works(skip=skip, limit=per_page)
    
    print(f"Works API response: {response}")
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
        works = []
    else:
        # Backend returns {'works': [...], 'total': N}
        works = response.get('works', []) if isinstance(response, dict) else []
        print(f"Extracted works: {works}")
    
    return render_template(
        'works/list.html',
        works=works,
        page=page,
        per_page=per_page,
        get_status_badge_class=get_status_badge_class
    )

@works_bp.route('/create', methods=['POST'])
@login_required
def create_work():
    """Create new work"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    if not name:
        flash('Work name is required.', 'danger')
        return redirect(url_for('works.list_works'))
    
    response = api.create_work(name, description)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
    else:
        flash('Work created successfully!', 'success')
    
    return redirect(url_for('works.list_works'))

@works_bp.route('/<int:work_id>')
@login_required
def view_work(work_id):
    """View work details - redirects to extraction page"""
    # Redirect to extraction page (the core function)
    return redirect(url_for('works.extract_page', work_id=work_id))

@works_bp.route('/<int:work_id>/extract')
@login_required
def extract_page(work_id):
    """Extraction page for work"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    response = api.get_work(work_id)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
        return redirect(url_for('works.list_works'))
    
    # Backend returns {'work': {...}, 'equipment': [], 'files': []}
    work = response.get('work', {})
    equipment = response.get('equipment', [])
    files = response.get('files', [])
    
    return render_template(
        'works/extract.html',
        work=work,
        equipment=equipment,
        files=files,
        get_status_badge_class=get_status_badge_class
    )

@works_bp.route('/<int:work_id>/extraction/start', methods=['POST'])
@login_required
def start_extraction(work_id):
    """Start extraction by uploading PDF"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate PDF
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    # Upload to backend
    response = api.start_extraction(work_id, file)
    
    if 'error' in response:
        return jsonify({'error': parse_error_message(response)}), 400
    
    # Return extraction ID as JSON
    return jsonify({
        'extraction_id': response.get('extraction_id'),
        'work_id': work_id,
        'status': response.get('status', 'pending'),
        'message': response.get('message', 'Extraction started')
    }), 200

@works_bp.route('/<int:work_id>/masterfile-status', methods=['GET'])
@login_required
def get_masterfile_status(work_id):
    """Get masterfile status for a work"""
    import os
    from config import Config
    
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get work details
    response = api.get_work(work_id)
    
    if 'error' in response:
        return jsonify({
            'has_masterfile': False,
            'error': parse_error_message(response)
        }), 200
    
    work = response
    
    # Check multiple sources for masterfile:
    # 1. Check backend database
    has_masterfile_db = work.get('has_masterfile', False)
    
    # 2. Check local templates_uploads folder (uploaded by admin)
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates_uploads')
    master_template_path = os.path.join(templates_dir, 'master_template.xlsx')
    has_local_template = os.path.exists(master_template_path)
    
    # 3. Check work-specific output folder (for work-specific masterfile)
    work_name = work.get('name', f'work_{work_id}')
    work_excel_path = os.path.join(
        Config.OUTPUT_FILES_DIR if hasattr(Config, 'OUTPUT_FILES_DIR') else 'src/output_files',
        work_name,
        'excel',
        'default',
        'masterfile.xlsx'
    )
    has_work_template = os.path.exists(work_excel_path)
    
    # Masterfile is available if ANY of these exist
    has_masterfile = has_masterfile_db or has_local_template or has_work_template
    
    # Determine which masterfile to report
    filename = 'masterfile.xlsx'
    source = 'Admin'
    
    if has_local_template:
        filename = 'master_template.xlsx'
        source = 'Admin (Global Template)'
    elif has_work_template:
        filename = 'masterfile.xlsx'
        source = f'Admin (Work: {work_name})'
    elif has_masterfile_db:
        filename = work.get('masterfile_name', 'masterfile.xlsx')
        source = work.get('masterfile_uploaded_by', 'Admin')
    
    return jsonify({
        'has_masterfile': has_masterfile,
        'filename': filename,
        'uploaded_by': source,
        'uploaded_at': work.get('masterfile_uploaded_at'),
        'sources': {
            'database': has_masterfile_db,
            'global_template': has_local_template,
            'work_specific': has_work_template
        }
    }), 200

@works_bp.route('/<int:work_id>/extraction/<int:extraction_id>/progress')
@login_required
def extraction_progress(work_id, extraction_id):
    """Show extraction progress"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get work info
    work_response = api.get_work(work_id)
    if 'error' in work_response:
        flash(parse_error_message(work_response), 'danger')
        return redirect(url_for('works.list_works'))
    
    work = work_response.get('work', {})
    
    # Get extraction status
    status_response = api.get_extraction_status(extraction_id)
    extraction_status = status_response if 'error' not in status_response else {}
    
    return render_template(
        'works/progress.html',
        work=work,
        extraction_id=extraction_id,
        extraction=extraction_status
    )

@works_bp.route('/extraction/<int:extraction_id>/status')
@login_required
def get_extraction_status_api(extraction_id):
    """API endpoint for polling extraction status"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    response = api.get_extraction_status(extraction_id)
    return jsonify(response)

@works_bp.route('/<int:work_id>/equipment/<int:equipment_id>')
@login_required
def view_equipment(work_id, equipment_id):
    """View equipment details with components and navigation"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get work details with all equipment
    work_response = api.get_work(work_id)
    if 'error' in work_response:
        flash(parse_error_message(work_response), 'danger')
        return redirect(url_for('works.list_works'))
    
    work = work_response.get('work', {})
    equipment_list = work_response.get('equipment', [])
    
    # Find current equipment
    current_equipment = None
    current_index = 0
    for idx, eq in enumerate(equipment_list):
        if eq['id'] == equipment_id:
            current_equipment = eq
            current_index = idx + 1
            break
    
    if not current_equipment:
        flash('Equipment not found.', 'danger')
        return redirect(url_for('works.extract_page', work_id=work_id))
    
    # Get previous and next equipment
    prev_equipment = equipment_list[current_index - 2] if current_index > 1 else None
    next_equipment = equipment_list[current_index] if current_index < len(equipment_list) else None
    
    return render_template(
        'works/equipment_detail.html',
        work=work,
        equipment=current_equipment,
        prev_equipment=prev_equipment,
        next_equipment=next_equipment,
        current_index=current_index,
        total_equipment=len(equipment_list)
    )

@works_bp.route('/<int:work_id>/edit', methods=['POST'])
@login_required
def edit_work(work_id):
    """Edit work"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    status = request.form.get('status', 'active')
    
    if not name:
        flash('Work name is required.', 'danger')
        return redirect(url_for('works.view_work', work_id=work_id))
    
    response = api.update_work(work_id, name, description, status)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
    else:
        flash('Work updated successfully!', 'success')
    
    return redirect(url_for('works.view_work', work_id=work_id))

@works_bp.route('/<int:work_id>/delete', methods=['POST'])
@login_required
def delete_work(work_id):
    """Delete work"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    response = api.delete_work(work_id)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
    else:
        flash('Work deleted successfully!', 'success')
    
    return redirect(url_for('works.list_works'))

@works_bp.route('/<int:work_id>/review', methods=['GET'])
@login_required
def review_data(work_id):
    """Review extracted data in table format"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get work details with equipment and files
    work_response = api.get_work(work_id)
    if 'error' in work_response:
        flash(parse_error_message(work_response), 'danger')
        return redirect(url_for('works.list_works'))
    
    # Extract work and equipment from the response
    work = work_response.get('work', work_response)
    equipment_list = work_response.get('equipment', [])
    
    return render_template(
        'works/review_data.html',
        work=work,
        equipment_list=equipment_list
    )

@works_bp.route('/<int:work_id>/components/bulk-save', methods=['POST'])
@login_required
def save_components_bulk(work_id):
    """Save multiple component changes at once"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    try:
        data = request.get_json()
        changes = data.get('changes', {})
        
        if not changes:
            return jsonify({'success': False, 'error': 'No changes to save'}), 400
        
        # Send bulk update to backend
        response = api.update_components_bulk(work_id, changes)
        
        if 'error' in response:
            return jsonify({
                'success': False,
                'error': parse_error_message(response)
            }), 400
        
        return jsonify({
            'success': True,
            'updated_count': response.get('updated_count', len(changes)),
            'message': 'Changes saved successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@works_bp.route('/history')
@login_required
def work_history():
    """View work history and activity logs"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get filter parameters
    days = request.args.get('days', 7, type=int)
    work_id = request.args.get('work_id', None, type=int)
    
    # Get activity history from API
    try:
        if work_id:
            # Get activities for specific work
            response = api.get_work_activities(work_id=work_id)
        else:
            # Get all activities for period
            response = api.get_work_history(days=days)
        
        if 'error' in response:
            flash(parse_error_message(response), 'danger')
            activities = []
            total = 0
        elif isinstance(response, list):
            # Backend returns list directly
            activities = response
            total = len(activities)
        else:
            activities = response.get('activities', response.get('items', []))
            total = response.get('total', len(activities))
    except Exception as e:
        flash(f'Error fetching work history: {str(e)}', 'danger')
        activities = []
        total = 0
    
    # Get list of all works for filtering dropdown
    works_response = api.get_works()
    works = works_response.get('works', []) if isinstance(works_response, dict) else []
    
    return render_template(
        'works/history.html',
        activities=activities,
        days=days,
        total=total,
        selected_work_id=work_id,
        works=works
    )
