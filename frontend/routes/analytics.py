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
    current_user = session.get('user', {})
    user_id = current_user.get('id')
    is_admin = current_user.get('role') == 'Admin'
    
    # Get all works
    response = api.get_works()
    all_works = response.get('works', []) if 'works' in response else response if isinstance(response, list) else []
    
    # Filter works by user if not admin
    if not is_admin:
        works = [w for w in all_works if w.get('user_id') == user_id]
    else:
        works = all_works
    
    # Get analytics metrics with appropriate grouping
    if is_admin:
        # Admins see all data
        extraction_stats = api.get_extraction_analytics(period='all_time')
        works_status = api.get_works_status(period='all_time')
        equipment_count = api.get_equipment_count(period='all_time')
        components_count = api.get_components_count(period='all_time')
    else:
        # Engineers: request grouped data and filter by their work IDs
        user_work_ids = set([w['id'] for w in works])
        
        # If user has no works, return zero counts
        if not user_work_ids:
            extraction_stats = {'data': [{'count': 0}], 'total': 0}
            works_status = {'data': [], 'total': 0}
            equipment_count = {'data': [{'count': 0}], 'total': 0}
            components_count = {'data': [{'count': 0}], 'total': 0}
        else:
            # Request grouped data from backend
            extraction_stats = api.get_extraction_analytics(period='all_time', group_by='work_id')
            works_status = api.get_works_status(period='all_time', group_by='user_id')
            equipment_count = api.get_equipment_count(period='all_time')  # Already grouped by work_id
            components_count = api.get_components_count(period='all_time')
            
            # Filter extraction stats by user's work IDs
            total_extractions = 0
            if 'data' in extraction_stats and isinstance(extraction_stats['data'], list):
                for item in extraction_stats['data']:
                    if item.get('work_id') in user_work_ids:
                        total_extractions += item.get('count', 0)
            
            extraction_stats = {
                'data': [{'count': total_extractions}],
                'total': total_extractions,
                'metric': 'extraction_status',
                'period': 'all_time'
            }
            
            # Filter works status (count from filtered works list)
            status_counts = {}
            for work in works:
                status = work.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            works_status = {
                'data': [{'status': k, 'count': v} for k, v in status_counts.items()],
                'total': len(works)
            }
            
            # Filter equipment by user's work IDs
            total_equipment = 0
            if 'data' in equipment_count and isinstance(equipment_count['data'], list):
                for item in equipment_count['data']:
                    if item.get('work_id') in user_work_ids:
                        total_equipment += item.get('count', 0)
            
            equipment_count = {'data': [{'count': total_equipment}], 'total': total_equipment}
            
            # Count components from user's works only
            total_components = 0
            for work_id in user_work_ids:
                work_detail = api.get_work(work_id)
                if isinstance(work_detail, dict):
                    equipment_list = work_detail.get('equipment', [])
                    for eq in (equipment_list if isinstance(equipment_list, list) else []):
                        components = eq.get('components', [])
                        total_components += len(components) if isinstance(components, list) else 0
            
            components_count = {'data': [{'count': total_components}], 'total': total_components}
    
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
