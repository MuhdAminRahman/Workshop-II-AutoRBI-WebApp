"""
Works Routes
CRUD operations for works
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from utils.auth_middleware import login_required, get_auth_token
from utils.api_client import BackendAPI
from utils.helpers import parse_error_message, get_status_badge_class
from config import Config

works_bp = Blueprint('works', __name__)

@works_bp.route('/')
@login_required
def list_works():
    """List all works"""
    token = get_auth_token()
    api = BackendAPI(token)
    current_user = session.get('user', {})
    user_id = current_user.get('id')
    user_role = current_user.get('role')
    is_admin = user_role == 'Admin' or user_role == 'admin'
    
    # Debug logging
    print(f"🔍 Current user: {current_user}")
    print(f"🔍 User role: '{user_role}' (type: {type(user_role)})")
    print(f"🔍 Is admin: {is_admin}")
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)  # Increased for admin
    skip = (page - 1) * per_page
    
    # Get works from API using appropriate endpoint
    if is_admin:
        # Admin uses admin endpoint to get ALL works
        response = api.admin_get_all_works(skip=skip, limit=per_page)
        print(f"🔍 Using admin endpoint: /api/admin/works")
    else:
        # Engineers use regular endpoint (filtered by backend)
        response = api.get_works(skip=skip, limit=per_page)
        print(f"🔍 Using engineer endpoint: /api/works")
    
    print(f"🔍 Works API response: {response}")
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
        works = []
    else:
        # Backend returns {'works': [...], 'total': N}
        works = response.get('works', []) if isinstance(response, dict) else []
        print(f"🔍 Total works returned: {len(works)}")
        
        # Note: Collaborators endpoint is currently failing on deployed backend
        # For now, engineers can see their assigned works in their own view
        # Admin can view team details on the work detail page
        
        if works:
            print(f"🔍 First work data: {works[0]}")
    
    return render_template(
        'works/list.html',
        works=works,
        page=page,
        per_page=per_page,
        is_admin=is_admin,
        get_status_badge_class=get_status_badge_class
    )

@works_bp.route('/assign', methods=['POST'])
@login_required
def assign_work():
    """Admin: Create and assign work to engineer"""
    token = get_auth_token()
    api = BackendAPI(token)
    current_user = session.get('user', {})
    admin_id = current_user.get('id')
    is_admin = current_user.get('role') == 'Admin'
    
    if not is_admin:
        flash('Only administrators can assign works.', 'danger')
        return redirect(url_for('works.list_works'))
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    user_ids = request.form.getlist('user_id')  # Changed to getlist for multiple selections
    
    if not name or not user_ids:
        flash('Work name and at least one engineer assignment are required.', 'danger')
        return redirect(url_for('works.list_works'))
    
    try:
        user_ids = [int(uid) for uid in user_ids]
    except ValueError:
        flash('Invalid engineer selection.', 'danger')
        return redirect(url_for('works.list_works'))
    
    # Step 1: Create the work (admin becomes initial owner)
    create_response = api.create_work(name, description)
    
    if 'error' in create_response or 'detail' in create_response:
        error_msg = create_response.get('detail') or create_response.get('error', 'Failed to create work')
        flash(f'Error creating work: {error_msg}', 'danger')
        return redirect(url_for('works.list_works'))
    
    work_id = create_response.get('id')
    if not work_id:
        flash('Error: Could not get work ID from created work', 'danger')
        return redirect(url_for('works.list_works'))
    
    print(f"🔍 Assigning work {work_id} to engineers: {user_ids} (type: {type(user_ids)})")
    
    # Step 2: Add admin as owner first (so they can manage collaborators)
    admin_email = current_user.get('email')
    if admin_email:
        try:
            print(f"🔍 Adding admin {admin_email} as owner of work {work_id}")
            owner_response = api.add_collaborator(work_id, admin_email, role='owner')
            print(f"🔍 Admin owner response: {owner_response}")
        except Exception as e:
            print(f"⚠️ Could not add admin as owner (might already be owner): {e}")
    
    # Step 3: Get engineer details and add them as collaborators
    users_response = api.get_users(skip=0, limit=1000)
    if 'error' in users_response:
        flash(f'Work created but could not load user data: {users_response.get("error")}', 'warning')
        return redirect(url_for('works.list_works'))
    
    all_users = users_response.get('users', [])
    user_emails = {user['id']: user['email'] for user in all_users}
    print(f"🔍 User emails map: {user_emails}")
    
    # Add each engineer as collaborator
    assigned_count = 0
    failed_assignments = []
    
    for user_id in user_ids:
        email = user_emails.get(user_id)
        print(f"🔍 Attempting to add user_id={user_id}, email={email}")
        if not email:
            failed_assignments.append(f"User ID {user_id}")
            print(f"❌ No email found for user_id={user_id}")
            continue
        
        print(f"🔍 Calling add_collaborator(work_id={work_id}, email={email}, role='editor')")
        collab_response = api.add_collaborator(work_id, email, role='editor')
        print(f"🔍 Collaborator response: {collab_response}")
        
        if 'error' in collab_response or 'detail' in collab_response:
            error_msg = collab_response.get('detail') or collab_response.get('error', 'Unknown error')
            failed_assignments.append(f"{email}: {error_msg}")
            print(f"❌ Failed to add {email}: {error_msg}")
        else:
            assigned_count += 1
            print(f"✅ Successfully added {email} as collaborator")
    
    # Show appropriate message
    if assigned_count == len(user_ids):
        flash(f'Work "{name}" successfully created and assigned to {assigned_count} engineer(s)!', 'success')
    elif assigned_count > 0:
        flash(f'Work "{name}" created. Assigned to {assigned_count}/{len(user_ids)} engineers. Failed: {"; ".join(failed_assignments)}', 'warning')
    else:
        flash(f'Work "{name}" created but assignment failed: {"; ".join(failed_assignments)}', 'warning')
    
    # Log activity
    try:
        if work_id and admin_id:
            api.log_activity(
                user_id=admin_id,
                entity_type='work',
                entity_id=work_id,
                action='created',  # Changed from 'assigned' to 'created' (valid enum)
                data={
                    'name': name,
                    'description': description,
                    'assigned_to_users': user_ids
                }
            )
    except Exception as e:
        print(f"Failed to log activity: {e}")
    
    return redirect(url_for('works.list_works'))

@works_bp.route('/api/engineers')
@login_required
def get_engineers():
    """API endpoint to get list of engineers"""
    token = get_auth_token()
    api = BackendAPI(token)
    current_user = session.get('user', {})
    is_admin = current_user.get('role') == 'Admin'
    
    if not is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    response = api.get_users(skip=0, limit=1000)
    
    if 'error' in response:
        return jsonify({'error': parse_error_message(response)}), 400
    
    users = response.get('users', [])
    # Filter to only engineers
    engineers = [u for u in users if u.get('role') == 'Engineer']
    
    return jsonify({'users': engineers})

@works_bp.route('/api/collaborators/<int:work_id>')
@login_required
def get_work_collaborators_api(work_id):
    """API endpoint to get collaborators for a work (avoids CORS issues)"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    collab_response = api.get_work_collaborators(work_id)
    
    if 'error' in collab_response:
        # Return empty collaborators instead of error
        return jsonify({'collaborators': []})
    
    return jsonify(collab_response)

@works_bp.route('/api/status/<int:work_id>', methods=['PUT'])
@login_required
def update_work_status(work_id):
    """API endpoint to update work status (avoids CORS issues)"""
    token = get_auth_token()
    api = BackendAPI(token)
    current_user = session.get('user', {})
    
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({'error': 'Status is required'}), 400
    
    # Call admin endpoint to update status (doesn't require name parameter)
    import json
    import requests
    
    backend_url = 'https://workshop-ii-autorbi-webapp.onrender.com/api/admin/works/{}'.format(work_id)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.put(
            backend_url,
            headers=headers,
            json={'status': status}
        )
        
        if response.status_code in [200, 204]:
            # Log the activity
            api.log_activity(
                user_id=current_user.get('id'),
                entity_type='work',
                entity_id=work_id,
                action='status_changed',
                data={'status': status}
            )
            return jsonify(response.json()), 200
        else:
            return jsonify({'error': response.json().get('detail', 'Failed to update work')}), response.status_code
    except Exception as e:
        print(f'❌ Error updating work status: {e}')
        return jsonify({'error': str(e)}), 500

@works_bp.route('/<int:work_id>/team')
@login_required
def view_team(work_id):
    """View team members for a work"""
    token = get_auth_token()
    api = BackendAPI(token)
    current_user = session.get('user', {})
    
    # Get work details
    work_response = api.get_work(work_id)
    if 'error' in work_response or 'detail' in work_response:
        flash('Work not found', 'danger')
        return redirect(url_for('works.list_works'))
    
    # Extract the nested work dict from the response
    if 'work' in work_response:
        work = work_response['work']
    else:
        work = work_response
    
    # Add work_id to work dict if not present
    if 'id' not in work:
        work['id'] = work_id
    
    # Try to get collaborators - the work response often has empty list
    # so we should always try the dedicated endpoint
    collaborators = []
    
    # Always try to fetch from dedicated collaborators endpoint
    collab_response = api.get_work_collaborators(work_id)
    print(f"🔍 Collaborators endpoint response: {collab_response}")
    
    if 'error' not in collab_response:
        if 'collaborators' in collab_response:
            collaborators = collab_response.get('collaborators', [])
            print(f"✅ Fetched {len(collaborators)} collaborators from endpoint")
        elif isinstance(collab_response, list):
            # Response might be a list directly
            collaborators = collab_response
            print(f"✅ Got collaborators as direct list: {len(collaborators)}")
    else:
        print(f"⚠️ Collaborators endpoint error: {collab_response.get('error')}")
        # Fall back to work_response collaborators if available
        if 'collaborators' in work_response:
            collaborators = work_response['collaborators']
            print(f"📋 Using {len(collaborators)} collaborators from work response")
    
    print(f"🔍 Extracted work data: {work}")
    print(f"🔍 Final collaborators count: {len(collaborators)}")
    # Server-side debug: show extractions and computed latestExtractionId for troubleshooting
    try:
        extractions = work.get('extractions') if isinstance(work, dict) else None
        print(f"🔍 work.extractions: {extractions}")
        latest_extraction_id = None
        if isinstance(extractions, list) and len(extractions):
            latest = extractions[-1]
            latest_extraction_id = latest.get('id') or latest.get('extraction_id') or latest.get('extractionId')
        print(f"🔍 latestExtractionId (computed on server): {latest_extraction_id}")
    except Exception as e:
        print(f"⚠️ Error while computing extraction debug info: {e}")
        # Check activity logs for extraction completion as a fallback
        try:
            activities_resp = api.get_work_activities(work_id)
            if not activities_resp or 'error' in activities_resp:
                print(f"🔍 No activities found or error: {activities_resp}")
            else:
                activities = activities_resp.get('activities') if isinstance(activities_resp, dict) else activities_resp
                print(f"🔍 Found {len(activities) if activities else 0} activities for work {work_id}")
                if activities:
                    # Build set of collaborator user ids for this work (if available)
                    collaborator_ids = set()
                    try:
                        for c in collaborators:
                            if isinstance(c, dict):
                                uid = c.get('user_id') or c.get('id') or c.get('userId')
                                if uid:
                                    collaborator_ids.add(int(uid))
                    except Exception:
                        collaborator_ids = set()

                    for act in activities:
                        if not isinstance(act, dict):
                            continue
                        et = act.get('entity_type')
                        action = act.get('action')
                        actor_id = act.get('user_id') or act.get('performed_by') or act.get('actor_id') or act.get('userId')
                        data = act.get('data')

                        # Prefer activities performed by collaborators (engineers) when available
                        actor_is_collab = False
                        try:
                            if actor_id and int(actor_id) in collaborator_ids:
                                actor_is_collab = True
                        except Exception:
                            actor_is_collab = False

                        # We're interested in extraction-related activities
                        if et and str(et).lower() == 'extraction':
                            status = None
                            if isinstance(data, dict):
                                status = data.get('status') or data.get('extraction_status') or data.get('status_message')
                            # If action suggests completion, or data.status indicates completed, mark extraction done
                            if (action and str(action).lower() in ['created','completed','status_changed','finished']) or (status and str(status).lower() in ['completed','done','success']):
                                # If there are collaborators, prefer activities by them; otherwise accept any
                                if collaborator_ids:
                                    if actor_is_collab:
                                        work['extraction_status'] = 'completed'
                                        print(f"🔍 Marking work {work_id} extraction_status=completed from activity by collaborator {actor_id}")
                                        break
                                    else:
                                        # not by collaborator, continue search
                                        continue
                                else:
                                    work['extraction_status'] = 'completed'
                                    print(f"🔍 Marking work {work_id} extraction_status=completed from activity (no collaborators constraint)")
                                    break
        except Exception as e:
            print(f"⚠️ Error while fetching activities: {e}")
    
    # Fetch equipment list for extraction tracking
    equipments = []
    equipment_codes = [
        'V-001',
        'V-002',
        'V-003',
        'V-004',
        'V-005',
        'V-006',
        'H-001',
        'H-002',
        'H-003',
        'H-004'
    ]
    
    try:
        print(f"🔍 Fetching equipment list from: /api/equipments/work/{work_id}")
        equipments_resp = api._get(f'/api/equipments/work/{work_id}')
        print(f"🔍 Equipment API response: {equipments_resp}")
        
        # Create a dict of extracted equipment by equipment_number
        extracted_dict = {}
        if equipments_resp and isinstance(equipments_resp, list):
            for eq in equipments_resp:
                if isinstance(eq, dict):
                    eq_num = eq.get('equipment_number', '')
                    extracted_dict[eq_num] = eq
                    print(f"🔍 Mapped {eq_num}: extracted_date={eq.get('extracted_date')}")
        
        # Build the final equipment list with all 10 items
        equipments = []
        for code in equipment_codes:
            if code in extracted_dict:
                # Equipment found in API response
                eq = extracted_dict[code]
                equipments.append(eq)
                print(f"✅ Found equipment: {code}, extracted={eq.get('extracted_date') is not None}")
            else:
                # Equipment not found, create pending entry
                equipments.append({
                    'equipment_number': code,
                    'extracted_date': None,
                    'id': None
                })
                print(f"⏳ Added pending equipment: {code}")
        
        extracted_count = sum(1 for eq in equipments if eq.get('extracted_date'))
        print(f"✅ Total equipment list: {extracted_count}/10 extracted")
    except Exception as e:
        print(f"⚠️ Exception while fetching equipment data: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback: create empty equipment records for all 10
        equipments = [
            {'equipment_number': name, 'extracted_date': None, 'id': None}
            for name in equipment_names
        ]
    
    return render_template(
        'works/team.html',
        work=work,
        collaborators=collaborators,
        auth_token=get_auth_token(),
        backend_api_url=Config.BACKEND_API_URL,
        equipments=equipments
    )

@works_bp.route('/<int:work_id>/extraction-status', methods=['GET'])
@login_required
def get_extraction_status(work_id):
    """AJAX endpoint to get equipment extraction status for polling"""
    token = get_auth_token()
    api = BackendAPI(token)
    
    # Define the 10 expected equipment (short codes as stored in DB)
    equipment_codes = [
        'V-001',
        'V-002',
        'V-003',
        'V-004',
        'V-005',
        'V-006',
        'H-001',
        'H-002',
        'H-003',
        'H-004'
    ]
    
    try:
        # Fetch equipment for this work
        print(f"🔍 Fetching equipment from: /api/equipments/work/{work_id}")
        equipment_list = api._get(f'/api/equipments/work/{work_id}')
        print(f"🔍 Equipment API response count: {len(equipment_list) if isinstance(equipment_list, list) else 'not a list'}")
        
        # Create a dict of extracted equipment by equipment_number
        extracted_dict = {}
        if equipment_list and isinstance(equipment_list, list):
            for eq in equipment_list:
                if isinstance(eq, dict):
                    eq_num = eq.get('equipment_number', '')
                    extracted_dict[eq_num] = eq
                    print(f"🔍 Found equipment in API response: {eq_num}, extracted_date={eq.get('extracted_date')}")
        
        # Build the full equipment list with all 10 items
        full_equipment_list = []
        for code in equipment_codes:
            if code in extracted_dict:
                eq = extracted_dict[code]
                full_equipment_list.append(eq)
                print(f"✅ Matched {code}: extracted_date={eq.get('extracted_date')}")
            else:
                full_equipment_list.append({
                    'equipment_number': code,
                    'extracted_date': None,
                    'id': None
                })
                print(f"⏳ No match for {code}, adding as pending")
        
        # Count how many have extracted_date set
        extracted_count = sum(1 for eq in full_equipment_list if isinstance(eq, dict) and eq.get('extracted_date'))
        total_count = 10  # Always 10
        all_extracted = extracted_count == total_count
        
        print(f"✅ Equipment extraction: {extracted_count}/{total_count} extracted")
        
        return jsonify({
            'total_equipments': total_count,
            'extracted_count': extracted_count,
            'all_extracted': all_extracted,
            'error': None
        })
    except Exception as e:
        print(f"⚠️ Equipment status error: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback: return with 0/10 equipment
        return jsonify({
            'total_equipments': 10,
            'extracted_count': 0,
            'all_extracted': False,
            'error': str(e)
        })

@works_bp.route('/create', methods=['POST'])
@login_required
def create_work():
    """Create new work (DEPRECATED - engineers cannot create works)"""
    flash('Engineers cannot create works. Contact your administrator.', 'warning')
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

    # Get backend WebSocket URL
    backend_url = Config.BACKEND_API_URL  # e.g., https://workshop-ii-autorbi-webapp.onrender.com
    backend_ws_url = backend_url.replace('https://', 'wss://').replace('http://', 'ws://')
    
    return render_template(
        'works/extract.html',
        work=work,
        equipment=equipment,
        files=files,
        get_status_badge_class=get_status_badge_class,
        auth_token=token,
        backend_ws_url=backend_ws_url
    )

@works_bp.route('/<int:work_id>/extraction/start', methods=['POST'])
@login_required
def start_extraction(work_id):
    """Start extraction by uploading PDF"""
    token = get_auth_token()
    api = BackendAPI(token)
    current_user = session.get('user', {})
    user_id = current_user.get('id')
    
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
    
    # Log activity for file upload
    try:
        if user_id:
            api.log_activity(
                user_id=user_id,
                entity_type='file',
                entity_id=response.get('file_id', 0),
                action='created',
                data={
                    'filename': file.filename,
                    'work_id': work_id,
                    'extraction_id': response.get('extraction_id')
                }
            )
    except Exception as e:
        print(f"Failed to log file upload activity: {e}")
    
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


@works_bp.route('/api/activities/<int:work_id>')
@login_required
def get_work_activities_api(work_id):
    """Frontend proxy to fetch work activity logs from backend

    If the work-specific endpoint fails (permissions or server error), fall back to
    fetching recent activity across the site and filter for items referencing
    this work (by data.work_id, entity_id, or message content).
    """
    token = get_auth_token()
    api = BackendAPI(token)

    response = api.get_work_activities(work_id)
    if 'error' in response:
        # Log and attempt fallback to recent activity period
        print(f"Work activities proxy: primary fetch failed for work {work_id}: {response.get('error')}")
        try:
            recent = api.get_work_history(days=30)
            if 'error' in recent:
                print(f"Work activities proxy: fallback also failed: {recent.get('error')}")
                return jsonify({'error': response.get('error')}), 400
            # Filter recent activities for references to this work
            acts = recent.get('activities', []) if isinstance(recent, dict) else recent or []
            filtered = []
            for a in acts:
                try:
                    d = a.get('data') or {}
                    if a.get('entity_type') == 'work' and int(a.get('entity_id') or 0) == int(work_id):
                        filtered.append(a)
                        continue
                    # data contains work_id
                    if isinstance(d, dict) and int(d.get('work_id') or d.get('workId') or 0) == int(work_id):
                        filtered.append(a)
                        continue
                    # message or description contain '#<work_id>' or 'work <id>'
                    txt = (a.get('message') or a.get('description') or '')
                    if txt and (f"#{work_id}" in txt or f"work {work_id}" in txt.lower()):
                        filtered.append(a)
                except Exception as e:
                    print('Error filtering activity', e)
            return jsonify({'activities': filtered, 'fallback': True})
        except Exception as e:
            print(f"Work activities proxy: fallback threw exception: {e}")
            return jsonify({'error': response.get('error')}), 400

    return jsonify(response)

@works_bp.route('/extraction/log-completion', methods=['POST'])
@login_required
def log_extraction_completion():
    """Log extraction completion activity and mark equipment as extracted"""
    try:
        data = request.get_json()
        work_id = data.get('work_id')
        extraction_id = data.get('extraction_id')
        equipment_count = data.get('equipment_count', 0)
        
        token = get_auth_token()
        api = BackendAPI(token)
        current_user = session.get('user', {})
        user_id = current_user.get('id')
        
        print(f"🔍 Logging extraction completion: work_id={work_id}, extraction_id={extraction_id}")
        
        # Get the extraction details to find out which file was uploaded
        try:
            extraction_resp = api._get(f'/api/extractions/{extraction_id}')
            print(f"🔍 Extraction details: {extraction_resp}")
            
            if extraction_resp and isinstance(extraction_resp, dict):
                filename = extraction_resp.get('filename') or extraction_resp.get('file_name', '')
                print(f"🔍 Extracted filename: {filename}")
                
                if filename:
                    # Parse equipment code from filename (e.g., "MLK PMT 10103 - V-003.pdf" -> "V-003")
                    # Remove extension first
                    base_name = filename.replace('.pdf', '').replace('.PDF', '').strip()
                    print(f"🔍 Base name: {base_name}")
                    
                    # Extract the equipment code (V-001 to V-006, H-001 to H-004)
                    # Try to find pattern like "V-###" or "H-###"
                    equipment_code = None
                    import re
                    match = re.search(r'([VH]-\d{3})', base_name)
                    if match:
                        equipment_code = match.group(1)
                    
                    print(f"🔍 Extracted equipment code: {equipment_code}")
                    
                    if equipment_code:
                        # Mark this equipment as extracted by finding it and updating extracted_date
                        try:
                            # Fetch all equipment for this work
                            equipment_list = api._get(f'/api/equipments/work/{work_id}')
                            print(f"🔍 Equipment list count: {len(equipment_list) if isinstance(equipment_list, list) else 'not a list'}")
                            
                            if equipment_list and isinstance(equipment_list, list):
                                for eq in equipment_list:
                                    if isinstance(eq, dict):
                                        eq_num = eq.get('equipment_number', '').strip()
                                        print(f"🔍 Comparing: '{equipment_code}' with '{eq_num}'")
                                        if eq_num.lower() == equipment_code.lower():
                                            # Found matching equipment, update its extracted_date
                                            eq_id = eq.get('id')
                                            print(f"✅ Found equipment to mark: {eq_num} (ID: {eq_id})")
                                            
                                            # Update the equipment with extracted_date
                                            if eq_id:
                                                update_resp = api._put(
                                                    f'/api/equipments/{eq_id}',
                                                    {
                                                        'equipment_number': eq_num,
                                                        'extracted_date': None  # Will be set to current timestamp by backend
                                                    }
                                                )
                                                print(f"✅ Equipment update response: {update_resp}")
                                            break
                                else:
                                    print(f"⚠️ No matching equipment found for code: {equipment_code}")
                        except Exception as e:
                            print(f"⚠️ Error updating equipment: {str(e)}")
                            import traceback
                            traceback.print_exc()
        except Exception as e:
            print(f"⚠️ Error fetching extraction details: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Log the activity
        if user_id:
            api.log_activity(
                user_id=user_id,
                entity_type='extraction',
                entity_id=extraction_id,
                action='completed',
                data={
                    'work_id': work_id,
                    'extraction_id': extraction_id,
                    'equipment_count': equipment_count,
                    'status': 'completed'
                }
            )
        
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"⚠️ Failed to log extraction completion: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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
    current_user = session.get('user', {})
    user_id = current_user.get('id')
    
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
        
        # Log activity
        try:
            if user_id:
                api.log_activity(
                    user_id=user_id,
                    entity_type='work',
                    entity_id=work_id,
                    action='updated',
                    data={'name': name, 'description': description, 'status': status}
                )
        except Exception as e:
            print(f"Failed to log activity: {e}")
    
    return redirect(url_for('works.view_work', work_id=work_id))

@works_bp.route('/<int:work_id>/delete', methods=['POST'])
@login_required
def delete_work(work_id):
    """Delete work"""
    token = get_auth_token()
    api = BackendAPI(token)
    current_user = session.get('user', {})
    user_id = current_user.get('id')
    
    # Get work name before deleting
    work_response = api.get_work(work_id)
    work_name = work_response.get('work', {}).get('name', 'Unknown') if not 'error' in work_response else 'Unknown'
    
    response = api.delete_work(work_id)
    
    if 'error' in response:
        flash(parse_error_message(response), 'danger')
    else:
        flash('Work deleted successfully!', 'success')
        
        # Log activity
        try:
            if user_id:
                api.log_activity(
                    user_id=user_id,
                    entity_type='work',
                    entity_id=work_id,
                    action='deleted',
                    data={'name': work_name}
                )
        except Exception as e:
            print(f"Failed to log activity: {e}")
    
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
        
        # After successful save, mark extraction as completed
        # Get the latest extraction for this work
        try:
            latest_extraction_resp = api._get(f'/api/works/{work_id}/extraction/latest')
            if 'extraction_id' in latest_extraction_resp:
                extraction_id = latest_extraction_resp['extraction_id']
                # Mark extraction as completed by calling a new endpoint
                completion_resp = api._put(
                    f'/api/extractions/{extraction_id}/mark-completed',
                    data={'status': 'completed'}
                )
                print(f"✅ Marked extraction {extraction_id} as completed after saving data")
        except Exception as e:
            print(f"⚠️ Could not mark extraction as completed: {e}")
            # Don't fail the save operation if this fails
        
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
    current_user = session.get('user', {})
    user_id = current_user.get('id')
    is_admin = current_user.get('role') == 'Admin'
    
    # Get filter parameters
    days = request.args.get('days', 7, type=int)
    work_id = request.args.get('work_id', None, type=int)
    filter_username = request.args.get('username', None)  # Add username filter
    page = request.args.get('page', 1, type=int)
    per_page = 15  # Activities per page
    
    # Get activity history from API
    activities = []
    total = 0
    
    try:
        if work_id:
            # Try to get activities for specific work
            # Note: This endpoint may fail on some databases due to JSON queries
            # If it fails, we'll fallback to filtering all activities
            response = api.get_work_activities(work_id=work_id)
            print(f"Work activities response: {response}")
            
            # Check if the work-specific endpoint failed
            if 'error' in response and 'Internal server error' in str(response.get('error', '')):
                print(f"Work-specific endpoint failed, using fallback approach")
                
                # Fallback: Get all activities and filter by work_id in frontend
                all_response = api.get_work_history(days=365)  # Get more days for better results
                
                if isinstance(all_response, list):
                    # Filter activities related to this work
                    activities = [
                        a for a in all_response 
                        if (a.get('entity_type') == 'work' and a.get('entity_id') == work_id) or
                           (a.get('data', {}).get('work_id') == work_id)
                    ]
                    total = len(activities)
                    print(f"Filtered {total} activities for work {work_id}")
                else:
                    flash('Could not retrieve work activities', 'danger')
            elif 'error' in response:
                error_msg = parse_error_message(response)
                flash(f'API Error: {error_msg}', 'danger')
                print(f"API error: {error_msg}")
            elif isinstance(response, dict):
                # Backend returns WorkHistoryResponse for /work/{work_id} endpoint
                activities = response.get('activities', [])
                total = response.get('total_activities', len(activities))
                print(f"Got {total} activities from dict")
        else:
            # Get all activities for period
            response = api.get_work_history(days=days)
            print(f"Period history response: {response}")
            
            if 'error' in response:
                error_msg = parse_error_message(response)
                flash(f'API Error: {error_msg}', 'danger')
                print(f"API error: {error_msg}")
            elif isinstance(response, list):
                # Backend returns list of ActivityResponse directly for /period endpoint
                activities = response
                total = len(activities)
                print(f"Got {total} activities as list")
            else:
                print(f"Unexpected response type: {type(response)}")
        
        # Filter activities by user for engineers (if not admin)
        if not is_admin and activities:
            # Engineers should only see their own activities
            original_total = len(activities)
            activities = [a for a in activities if a.get('user_id') == user_id]
            total = len(activities)
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f'Exception fetching work history: {error_trace}')
        flash(f'Error fetching work history: {str(e)}', 'danger')
        activities = []
        total = 0
    
    # Get list of works for filtering dropdown
    try:
        if is_admin:
            # Admin gets all works
            works_response = api.admin_get_all_works(skip=0, limit=500)
            works = works_response.get('works', []) if isinstance(works_response, dict) else []
        else:
            # Engineers get their assigned works (backend already filters by collaborators)
            works_response = api.get_works(skip=0, limit=500)
            works = works_response.get('works', []) if isinstance(works_response, dict) else []
    except Exception as e:
        flash(f'Error fetching works list: {str(e)}', 'warning')
        works = []
    
    # Get users list for username mapping (only for admins or current user)
    users_map = {}
    try:
        if is_admin:
            users_response = api.get_users()
            users_list = users_response.get('users', []) if isinstance(users_response, dict) else []
            users_map = {u.get('id'): u.get('username', f"User #{u.get('id')}") for u in users_list}
        # Always add current user
        users_map[user_id] = current_user.get('username', f"User #{user_id}")
    except Exception as e:
        print(f'Error fetching users: {e}')
        users_map = {user_id: current_user.get('username', f"User #{user_id}")}
    
    # Apply username filter for admins (after users_map is built)
    if is_admin and filter_username and activities:
        activities = [a for a in activities if users_map.get(a.get('user_id')) == filter_username]
        total = len(activities)
    
    # Implement pagination
    total_activities = len(activities)
    total_pages = (total_activities + per_page - 1) // per_page  # Ceiling division
    
    # Ensure page is within bounds
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Slice activities for current page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_activities = activities[start_idx:end_idx]
    
    return render_template(
        'works/history.html',
        activities=paginated_activities,
        days=days,
        total=total,
        selected_work_id=work_id,
        works=works,
        users_map=users_map,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_activities=total_activities,
        filter_username=filter_username,
        users_list=list(set(users_map.values())),
        is_admin=is_admin
    )
