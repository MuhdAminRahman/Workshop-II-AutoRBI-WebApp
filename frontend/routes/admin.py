"""
Admin Routes
User management, system administration
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from utils.auth_middleware import login_required, admin_required, get_auth_token
from utils.api_client import BackendAPI
from utils.helpers import parse_error_message

admin_bp = Blueprint('admin', __name__)


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@admin_bp.route('/users')
@admin_required
def list_users():
    """List all users (Admin only)"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get all users
    response = api.get_users(skip=0, limit=1000)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
        users = []
        total = 0
    else:
        users = response.get('users', [])
        total = response.get('total', len(users))
    
    return render_template(
        'admin/users.html',
        users=users,
        total=total
    )


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    """Create new user"""
    if request.method == 'GET':
        return render_template('admin/user_form.html', user=None, action='create')
    
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get form data
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    role = request.form.get('role', 'engineer')
    
    # Validate
    if not all([username, email, password, full_name]):
        flash('All fields are required', 'danger')
        return redirect(url_for('admin.create_user'))
    
    # Create user
    response = api.create_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name,
        role=role
    )
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
        return redirect(url_for('admin.create_user'))
    
    flash(f'User {username} created successfully!', 'success')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit user"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    if request.method == 'GET':
        # Get user details
        response = api.get_user(user_id)
        if 'error' in response:
            flash(parse_error_message(response), 'danger')
            return redirect(url_for('admin.list_users'))
        
        return render_template('admin/user_form.html', user=response, action='edit')
    
    # Update user
    username = request.form.get('username')
    email = request.form.get('email')
    full_name = request.form.get('full_name')
    role = request.form.get('role')
    is_active = request.form.get('is_active') == 'on'
    
    response = api.update_user(
        user_id=user_id,
        username=username,
        email=email,
        full_name=full_name,
        role=role,
        is_active=is_active
    )
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
        return redirect(url_for('admin.edit_user', user_id=user_id))
    
    flash('User updated successfully!', 'success')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete user"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    response = api.delete_user(user_id)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
    else:
        flash('User deleted successfully!', 'success')
    
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/<int:user_id>')
@admin_required
def view_user(user_id):
    """View user details"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get user details
    user_response = api.get_user(user_id)
    if 'error' in user_response:
        flash(parse_error_message(user_response), 'danger')
        return redirect(url_for('admin.list_users'))
    
    # Get user's works
    works_response = api.get_works(skip=0, limit=1000)
    all_works = works_response.get('works', []) if 'error' not in works_response else []
    
    # Filter works assigned to this user
    user_works = [w for w in all_works if w.get('user_id') == user_id]
    
    return render_template(
        'admin/user_detail.html',
        user=user_response,
        works=user_works
    )


# ============================================================================
# SYSTEM DASHBOARD (Admin Overview)
# ============================================================================

@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    """Admin system dashboard"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get all works
    works_response = api.get_works(skip=0, limit=1000)
    works = works_response.get('works', []) if 'error' not in works_response else []
    
    # Get all users
    users_response = api.get_users(skip=0, limit=1000)
    users = users_response.get('users', []) if 'error' not in users_response else []
    
    # Calculate statistics
    total_works = len(works)
    active_works = sum(1 for w in works if w.get('status') == 'active')
    completed_works = sum(1 for w in works if w.get('status') == 'completed')
    total_users = len(users)
    active_users = sum(1 for u in users if u.get('is_active', True))
    
    # Group works by user
    works_by_user = {}
    for work in works:
        user_id = work.get('user_id')
        if user_id:
            if user_id not in works_by_user:
                works_by_user[user_id] = []
            works_by_user[user_id].append(work)
    
    # Get recent activity
    history_response = api.get_work_history(days=7)
    recent_activities = []
    if 'error' not in history_response:
        if isinstance(history_response, list):
            recent_activities = history_response[:10]
        else:
            recent_activities = history_response.get('activities', [])[:10]
    
    return render_template(
        'admin/dashboard.html',
        total_works=total_works,
        active_works=active_works,
        completed_works=completed_works,
        total_users=total_users,
        active_users=active_users,
        works=works,
        users=users,
        works_by_user=works_by_user,
        recent_activities=recent_activities
    )
