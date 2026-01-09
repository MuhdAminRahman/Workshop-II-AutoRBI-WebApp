"""
Analytics Routes
Analytics dashboard and metrics
"""
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
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
    
    # Get all works
    response = api.get_works()
    works = response.get('works', []) if 'works' in response else response if isinstance(response, list) else []
    
    # Get analytics metrics (use all_time for totals)
    extraction_stats = api.get_extraction_analytics(period='all_time')
    works_status = api.get_works_status(period='all_time')
    equipment_count = api.get_equipment_count(period='all_time')
    components_count = api.get_components_count(period='all_time')
    
    return render_template(
        'analytics/index.html', 
        works=works,
        extraction_stats=extraction_stats,
        works_status=works_status,
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
    completed_equipment = sum(1 for eq in equipment if eq.get('status') == 'completed')
    
    analytics = {
        'total_equipment': total_equipment,
        'completed_equipment': completed_equipment,
        'completion_rate': round((completed_equipment / total_equipment * 100) if total_equipment > 0 else 0, 1),
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
