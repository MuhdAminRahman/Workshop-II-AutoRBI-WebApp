"""
Admin Routes
User management, system administration
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import logging
from utils.auth_middleware import login_required, admin_required, get_auth_token
from utils.api_client import BackendAPI
from utils.helpers import parse_error_message

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)


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
    
    # Capitalize role to match backend expectations (Engineer, Admin, Viewer)
    role = role.capitalize()
    
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
    is_active_form = request.form.get('is_active') == 'on'
    
    # First, update user details (excluding is_active)
    response = api.update_user(
        user_id=user_id,
        username=username,
        email=email,
        full_name=full_name,
        role=role
    )
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
        return redirect(url_for('admin.edit_user', user_id=user_id))
    
    # Get current user status to compare with form value
    current_user = api.get_user(user_id)
    current_is_active = current_user.get('is_active', True)
    
    # Handle status change using dedicated endpoints
    if is_active_form and not current_is_active:
        # User should be active but is currently inactive -> reactivate
        status_response = api.reactivate_user(user_id)
        if 'error' in status_response:
            flash(f"User updated but failed to reactivate: {parse_error_message(status_response)}", 'warning')
    elif not is_active_form and current_is_active:
        # User should be inactive but is currently active -> deactivate
        status_response = api.deactivate_user(user_id)
        if 'error' in status_response:
            flash(f"User updated but failed to deactivate: {parse_error_message(status_response)}", 'warning')
    
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
    
    # Get user details using /api/users/{user_id}
    user_response = api.get_user(user_id)
    
    if 'error' in user_response:
        flash(parse_error_message(user_response), 'danger')
        return redirect(url_for('admin.list_users'))
    
    # Get user's works using /api/admin/users/{user_id}/works
    works_response = api.admin_get_user_works(user_id, skip=0, limit=500)
    user_works = works_response.get('works', []) if isinstance(works_response, dict) and 'error' not in works_response else []
    
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
    
    # Get all works (prefer admin endpoint; fallback to public all_users flag)
    works_response = api.admin_get_all_works(skip=0, limit=1000)
    works = []
    if isinstance(works_response, dict) and 'error' not in works_response:
        works = works_response.get('works', [])
    else:
        # Fallback to public works endpoint with all_users=True
        fallback = api.get_works(skip=0, limit=1000, all_users=True)
        if isinstance(fallback, dict) and 'error' not in fallback:
            works = fallback.get('works', [])
        else:
            # Surface errors to the UI for debugging
            err = None
            if isinstance(works_response, dict) and 'error' in works_response:
                err = works_response.get('error')
            elif isinstance(fallback, dict) and 'error' in fallback:
                err = fallback.get('error')
            if err:
                flash(f'Error fetching works: {err}', 'warning')
            works = []
    
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


@admin_bp.route('/analytics')
@admin_required
def admin_analytics():
    """Admin analytics showing all engineers' works, equipment, and components"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    all_works = []
    all_equipment = []
    all_users = []
    
    try:
        # Get all works for all engineers
        print("🔍 Fetching admin works...")
        print(f"   Token present: {bool(token)}")
        print(f"   Token preview: {token[:20]}..." if token else "   No token")
        
        works_response = api._get('/api/admin/works?skip=0&limit=500')
        print(f"📊 Works response keys: {works_response.keys() if isinstance(works_response, dict) else 'not a dict'}")
        print(f"📊 Full response: {works_response}")
        
        # Check for errors first
        if isinstance(works_response, dict) and 'error' in works_response:
            error_msg = works_response.get('error')
            print(f"❌ Error from backend: {error_msg}")
            flash(f'Error fetching works: {error_msg}', 'danger')
        elif isinstance(works_response, dict):
            if 'works' in works_response:
                all_works = works_response.get('works', [])
            else:
                # If no 'works' key and no error, the whole thing might be a list
                all_works = works_response
        elif isinstance(works_response, list):
            all_works = works_response
        
        print(f"✅ Got {len(all_works)} works")
    except Exception as e:
        print(f"⚠️ Error fetching works: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error fetching works: {str(e)}', 'warning')
    
    try:
        # Get equipment for each work
        print("🔍 Fetching equipment for each work...")
        all_equipment = []
        for work in all_works:
            if not isinstance(work, dict):
                continue
            work_id = work.get('id')
            try:
                work_equipment = api._get(f'/api/equipments/work/{work_id}')
                if isinstance(work_equipment, list):
                    all_equipment.extend(work_equipment)
                    print(f"  ✅ Got {len(work_equipment)} equipment for work {work_id}")
                else:
                    print(f"  ⚠️ Unexpected response format for work {work_id}: {work_equipment}")
            except Exception as we:
                print(f"  ⚠️ Error fetching equipment for work {work_id}: {we}")
        
        print(f"✅ Got total {len(all_equipment)} equipment items")
    except Exception as e:
        print(f"⚠️ Error fetching equipment: {e}")
        flash(f'Error fetching equipment: {str(e)}', 'warning')
    
    try:
        # Get collaborators for each work
        print("🔍 Fetching collaborators for each work...")
        for work in all_works:
            if not isinstance(work, dict):
                continue
            work_id = work.get('id')
            try:
                collab_response = api._get(f'/api/works/{work_id}/collaborators')
                if isinstance(collab_response, dict) and 'collaborators' in collab_response:
                    collaborators = collab_response.get('collaborators', [])
                    # Find all engineers (editor role)
                    engineers = [c for c in collaborators if c.get('role') == 'editor']
                    if engineers:
                        work['assigned_engineers'] = [e.get('full_name') or e.get('email') for e in engineers]
                    else:
                        work['assigned_engineers'] = []
                else:
                    work['assigned_engineers'] = []
            except Exception as ce:
                print(f"  ⚠️ Error fetching collaborators for work {work_id}: {ce}")
                work['assigned_engineers'] = []
        
        print(f"✅ Collaborators fetched for all works")
    except Exception as e:
        print(f"⚠️ Error fetching collaborators: {e}")
    
    try:
        # Get all users
        print("🔍 Fetching all users...")
        users_response = api.get_users(skip=0, limit=1000)
        if isinstance(users_response, dict):
            all_users = users_response.get('users', []) if 'users' in users_response else []
        elif isinstance(users_response, list):
            all_users = users_response
        print(f"✅ Got {len(all_users)} users")
    except Exception as e:
        print(f"⚠️ Error fetching users: {e}")
    
    # Prepare analytics data
    analytics_data = {
        'total_works': len(all_works),
        'total_equipment': len(all_equipment),
        'total_components': sum(len(eq.get('components', [])) for eq in all_equipment if isinstance(eq, dict)),
        'extracted_equipment': sum(1 for eq in all_equipment if isinstance(eq, dict) and eq.get('extracted_date')),
        'pending_equipment': sum(1 for eq in all_equipment if isinstance(eq, dict) and not eq.get('extracted_date')),
        'completed_works': sum(1 for work in all_works if isinstance(work, dict) and work.get('status') == 'completed'),
        'active_works': sum(1 for work in all_works if isinstance(work, dict) and work.get('status') == 'active'),
    }
    
    print(f"📈 Analytics: {analytics_data}")
    
    # Group works by user/engineer
    works_by_engineer = {}
    for work in all_works:
        if not isinstance(work, dict):
            continue
            
        engineer_id = work.get('owner_id', 'unknown')
        engineer_name = work.get('owner_username', 'Unknown')
        
        if engineer_id not in works_by_engineer:
            works_by_engineer[engineer_id] = {
                'name': engineer_name,
                'works': [],
                'total_works': 0,
                'total_equipment': 0,
                'extracted_equipment': 0,
                'pending_equipment': 0,
            }
        
        works_by_engineer[engineer_id]['works'].append(work)
        works_by_engineer[engineer_id]['total_works'] += 1
        
        # Count equipment for this work
        work_id = work.get('id')
        work_equipment = [eq for eq in all_equipment if isinstance(eq, dict) and eq.get('work_id') == work_id]
        works_by_engineer[engineer_id]['total_equipment'] += len(work_equipment)
        works_by_engineer[engineer_id]['extracted_equipment'] += sum(1 for eq in work_equipment if eq.get('extracted_date'))
        works_by_engineer[engineer_id]['pending_equipment'] += sum(1 for eq in work_equipment if not eq.get('extracted_date'))
    
    return render_template(
        'admin/analytics.html',
        analytics_data=analytics_data,
        all_works=all_works,
        all_equipment=all_equipment,
        all_users=all_users,
        works_by_engineer=works_by_engineer
    )


# ============================================================================
# REPORTS (ADMIN VIEW ONLY)
# ============================================================================

@admin_bp.route('/reports')
@admin_required
def admin_reports():
    """View all reports (Admin only)"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    all_works = []
    
    try:
        # Get all works for all engineers
        print("🔍 Fetching admin works for reports...")
        works_response = api._get('/api/admin/works?skip=0&limit=500')
        
        if isinstance(works_response, dict):
            if 'works' in works_response:
                all_works = works_response.get('works', [])
            elif 'error' not in works_response:
                all_works = works_response
        elif isinstance(works_response, list):
            all_works = works_response
        
        # Add collaborators (engineers) info to each work
        for work in all_works:
            try:
                collab_response = api._get(f'/api/works/{work.get("id")}/collaborators')
                if isinstance(collab_response, dict) and 'collaborators' in collab_response:
                    collaborators = collab_response.get('collaborators', [])
                    # Find all engineers (editor role)
                    engineers = [c for c in collaborators if c.get('role') == 'editor']
                    if engineers:
                        # Store engineers as list for template to display as separate badges
                        work['assigned_engineers'] = [e.get('full_name') or e.get('email') for e in engineers]
                    else:
                        work['assigned_engineers'] = []
                else:
                    work['assigned_engineers'] = []
            except Exception as e:
                print(f"⚠️ Error fetching collaborators for work {work.get('id')}: {e}")
                work['assigned_engineers'] = []
        
        print(f"✅ Got {len(all_works)} works for reports")
    except Exception as e:
        print(f"⚠️ Error fetching works: {e}")
        flash(f'Error fetching works: {str(e)}', 'warning')
    
    return render_template(
        'admin/reports.html',
        all_works=all_works
    )


@admin_bp.route('/reports/<int:work_id>')
@admin_required
def admin_view_report(work_id):
    """View report for specific work (Admin only)"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Get all works and find the one matching work_id
    works_response = api._get('/api/admin/works?skip=0&limit=500')
    
    work = None
    if isinstance(works_response, dict) and 'works' in works_response:
        works = works_response.get('works', [])
    elif isinstance(works_response, list):
        works = works_response
    else:
        works = []
    
    # Find the specific work by ID
    for w in works:
        if w.get('id') == work_id:
            work = w
            break
    
    if not work:
        flash('Work not found', 'danger')
        return redirect(url_for('admin.admin_reports'))
    
    # Get generated reports for this work - use correct endpoint
    reports_response = api._get(f'/api/reports/{work_id}/reports')
    
    if isinstance(reports_response, dict) and 'reports' in reports_response:
        reports = reports_response.get('reports', [])
    elif isinstance(reports_response, list):
        reports = reports_response
    else:
        reports = []
    
    print(f"📊 Reports response: {reports_response}")
    print(f"✅ Got {len(reports)} reports")
    print(f"💼 Work object: {work}")
    print(f"💼 Work name: {work.get('name')}")
    
    return render_template(
        'admin/view_report.html',
        work=work,
        reports=reports,
        work_id=work_id
    )

