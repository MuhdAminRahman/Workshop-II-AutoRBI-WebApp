"""
Analytics Routes
Analytics dashboard and metrics
"""
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
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
    works = response.get('items', []) if 'items' in response else response if isinstance(response, list) else []
    
    return render_template('analytics/index.html', works=works)

@analytics_bp.route('/<int:work_id>')
@login_required
def view_analytics(work_id):
    """View analytics for a specific work"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get work details
    work_response = api.get_work(work_id)
    
    if 'error' in work_response:
        flash(parse_error_message(work_response), 'danger')
        return redirect(url_for('analytics.index'))
    
    # Get analytics data
    analytics_response = api.get_analytics(work_id)
    
    if 'error' in analytics_response:
        flash(parse_error_message(analytics_response), 'danger')
        analytics = {}
    else:
        analytics = analytics_response
    
    return render_template(
        'analytics/view.html',
        work=work_response,
        analytics=analytics
    )

@analytics_bp.route('/<int:work_id>/data')
@login_required
def get_analytics_data(work_id):
    """Get analytics data as JSON (for AJAX/charts)"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    response = api.get_analytics(work_id)
    
    return jsonify(response)
