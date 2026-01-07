"""
Authentication Routes
Login, Register, Logout
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.api_client import BackendAPI
from utils.helpers import parse_error_message

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    # Redirect if already logged in
    if 'token' in session:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate input
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/login.html')
        
        # Call backend API
        api = BackendAPI()
        response = api.login(username, password)
        
        if 'error' in response:
            flash(parse_error_message(response), 'danger')
            return render_template('auth/login.html')
        
        # Store token and user info in session
        session['token'] = response.get('access_token')
        session['user'] = {
            'id': response.get('user', {}).get('id'),
            'username': response.get('user', {}).get('username'),
            'email': response.get('user', {}).get('email'),
            'role': response.get('user', {}).get('role')
        }
        
        flash('Login successful!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    # Redirect if already logged in
    if 'token' in session:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not all([full_name, username, email, role, password, confirm_password]):
            flash('Please fill in all fields.', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/register.html')
        
        # Call backend API
        api = BackendAPI()
        response = api.register(username, email, password, full_name, role)
        
        # Debug: print the full response
        print(f"Registration response: {response}")
        
        if 'error' in response:
            error_msg = parse_error_message(response)
            print(f"Registration error: {error_msg}")
            flash(error_msg, 'danger')
            return render_template('auth/register.html')
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
