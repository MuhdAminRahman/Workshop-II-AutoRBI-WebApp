"""
Analytics Routes
Analytics dashboard and metrics
"""
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request, session
from utils.auth_middleware import login_required, get_auth_token
from utils.api_client import BackendAPI
from utils.helpers import parse_error_message

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
@login_required
def index():
    """Analytics overview page"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get works assigned to user
    works_response = api.get_works(skip=0, limit=100)
    works = works_response.get('works', []) if isinstance(works_response, dict) else []
    
    # Initialize counters
    total_works = len(works)
    total_extractions = 0
    total_equipment = 0
    total_components = 0
    
    # For each work, calculate metrics
    for work in works:
        work_id = work.get('id')
        if work_id:
            try:
                work_detail = api.get_work(work_id)
                equipment_list = work_detail.get('equipment', [])
                
                for equipment in equipment_list:
                    total_equipment += 1
                    # Count extractions (equipment with components = extracted)
                    components = equipment.get('components', [])
                    if components:
                        total_extractions += 1
                    total_components += len(components) if isinstance(components, list) else 0
            except:
                continue
    
    # Prepare stats for template
    extraction_stats = {'total': total_extractions}
    equipment_count = {'total': total_equipment}
    components_count = {'total': total_components}
    
    return render_template(
        'analytics/index.html', 
        works=works,
        total_works=total_works,
        extraction_stats=extraction_stats,
        equipment_count=equipment_count,
        components_count=components_count
    )

@analytics_bp.route('/<int:work_id>')
@login_required
def view_analytics(work_id):
    """View analytics for a specific work"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get work details with equipment
    work_response = api.get_work(work_id)
    
    if 'error' in work_response:
        flash(parse_error_message(work_response), 'danger')
        return redirect(url_for('analytics.index'))
    
    work = work_response.get('work', work_response)
    equipment = work_response.get('equipment', [])
    
    # Calculate simple stats from work data
    total_equipment = len(equipment)
    
    # If work status is completed, mark all equipment as completed
    if work.get('status') == 'completed':
        completed_equipment = total_equipment
        completion_rate = 100.0 if total_equipment > 0 else 0
    else:
        completed_equipment = sum(1 for eq in equipment if eq.get('status') == 'completed')
        completion_rate = round((completed_equipment / total_equipment * 100) if total_equipment > 0 else 0, 1)
    
    analytics = {
        'total_equipment': total_equipment,
        'completed_equipment': completed_equipment,
        'completion_rate': completion_rate,
        'equipment': equipment
    }
    
    return render_template(
        'analytics/view.html',
        work=work,
        analytics=analytics
    )

@analytics_bp.route('/trends')
@login_required
def get_trends():
    """Get analytics trends data as JSON"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    period = request.args.get('period', 'week')
    
    response = api.get_analytics_trends(period=period)
    
    return jsonify(response)
