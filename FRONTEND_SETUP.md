# Frontend Setup Guide - AutoRBI Web App

This guide will help you set up and run the AutoRBI Web Application frontend (Review Data UI).

## Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **pip** - Python package manager (comes with Python)
- **Git** - [Download Git](https://git-scm.com/downloads)

## Quick Start

### 1. Clone the Repository (If Not Already Done)

```bash
git clone <repository-url>
cd Workshop-II-AutoRBI-WebApp
```

### 2. Navigate to Project Directory

```bash
cd "Workshop-II-AutoRBI-WebApp"
```

### 3. Install Dependencies

**Option A: Without Virtual Environment (Quick Method)**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
pip install -r requirements.txt

# Or install manually
pip install flask flask-session flask-cors python-dotenv werkzeug jinja2 requests
```

**Option B: With Virtual Environment (Recommended)**
```bash
# Navigate to frontend directory
cd frontend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Generate SECRET_KEY

The SECRET_KEY is required for Flask session management and security. Generate one using Python:

**Method 1: Quick Command (Recommended)**
```bash
# Generate a secure random key
python -c "import secrets; print(secrets.token_hex(32))"
```

This will output something like:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

**Method 2: Generate with UUID**
```bash
python -c "import uuid; print(uuid.uuid4().hex)"
```

**Method 3: Using Python Interactive Shell**
```bash
# Start Python
python

# Then run:
>>> import secrets
>>> secrets.token_hex(32)
'your-generated-secret-key-here'
>>> exit()
```

**Copy the generated key** - you'll need it in the next step!

### 5. Set Up Environment Variables

Create a `.env` file in the `frontend` directory:(refer.env.example)

**Option A: Create Manually**

Create a file named `.env` in the `frontend` folder with the following content:

```plaintext
SECRET_KEY=<paste-your-generated-key-here>
FLASK_APP=app.py
FLASK_ENV=development
BACKEND_URL=http://localhost:8000
SESSION_TYPE=filesystem
```

**Option B: Quick Creation (PowerShell)**
```powershell
# Navigate to frontend directory
cd frontend

# Create .env file with generated SECRET_KEY
$secretKey = python -c "import secrets; print(secrets.token_hex(32))"
@"
SECRET_KEY=$secretKey
FLASK_APP=app.py
FLASK_ENV=development
BACKEND_URL=http://localhost:8000
SESSION_TYPE=filesystem
"@ | Out-File -FilePath .env -Encoding utf8
```

**Option C: Quick Creation (Command Prompt)**
```bash
cd frontend
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32) + '\nFLASK_APP=app.py\nFLASK_ENV=development\nBACKEND_URL=http://localhost:8000\nSESSION_TYPE=filesystem')" > .env
```

Verify the `.env` file was created:
```bash
type .env
```

### 6. Run the Frontend Application

```bash
# Make sure you're in the frontend directory
cd frontend

# If using virtual environment, activate it first
venv\Scripts\activate

# Run the application
python app.py
```

Alternative methods:
```bash
# Method 2: Using Flask CLI
flask run

# Method 3: Run on specific port
flask run --port 5001
```

### 7. Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```
or
```
http://127.0.0.1:5000
```

## Environment Variables Explained

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Secret key for Flask session encryption | `a1b2c3d4e5f6...` |
| `FLASK_APP` | Entry point for Flask application | `app.py` |
| `FLASK_ENV` | Environment mode (development/production) | `development` |
| `BACKEND_URL` | Backend API base URL | `http://localhost:8000` |
| `SESSION_TYPE` | Session storage type | `filesystem` |

## Testing the Review Data Page

### Accessing the Page

1. Open browser to `http://localhost:5000`
2. Login with your credentials
3. Navigate to **Works** section
4. Select a work project
5. Click on **"Review Data"** button

### Features to Test

#### 1. **Data Tables**
- Each equipment has its own table
- Tables display components and their data
- Yellow-themed table headers
- Horizontal scrolling for wide tables

#### 2. **Editable Fields** (Engineer Role)
- Click on any field to edit
- Fields change color when modified (yellow background)
- Valid entries show green border
- Invalid entries show red border

#### 3. **Statistics Card**
- Shows total equipment items
- Displays total components
- Shows fields to fill
- Shows fields corrected
- Progress bar indicates completion percentage

#### 4. **Save Changes Button**
- Click to save all modified data
- Shows loading spinner while saving
- Displays success/error notification

#### 5. **Validate Data Button**
- Validates all fields before saving
- Shows list of issues if any
- Highlights problematic fields
- Auto-scrolls to first error

#### 6. **Keyboard Shortcuts**
- `Ctrl + S` - Save changes
- `Ctrl + Shift + V` - Validate data

## Project Structure

```
Workshop-II-AutoRBI-WebApp/
├── frontend/
│   ├── app.py                      # Main Flask application
│   ├── config.py                   # Configuration settings
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Environment variables (create this)
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── works/
│   │       └── review_data.html    # Review Data page
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── main.js
│   │   └── images/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── main.py
│   │   └── works.py
│   └── utils/
│       ├── __init__.py
│       ├── api_client.py
│       ├── auth_middleware.py
│       └── helpers.py
└── backend/
    └── ... (backend files)
```

## Common Issues & Solutions

### Issue: "Port already in use"
```bash
# Solution: Use different port
flask run --port 5001

# Or find and kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Issue: "Module not found" errors
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt

# Or install missing packages individually
pip install flask flask-session flask-cors python-dotenv
```

### Issue: "Template not found"
```bash
# Solution: Verify template path
# Ensure review_data.html is in: frontend/templates/works/review_data.html

# Check if file exists
dir frontend\templates\works\review_data.html
```

### Issue: "SECRET_KEY not found"
```bash
# Solution: Ensure .env file exists and is in the correct location
cd frontend
type .env

# If missing, create it with:
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" > .env
```

### Issue: "Database error"
```bash
# Solution: Check backend connection
# Verify BACKEND_URL in .env file
# Ensure backend server is running
```

### Issue: "Static files not loading"
```bash
# Solution: Clear browser cache
# Press Ctrl + Shift + R (hard refresh)

# Verify static folder path
dir frontend\static
```

### Issue: "Cannot connect to backend"
```bash
# Solution: Start the backend server first
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Then start frontend
cd ..\frontend
python app.py
```

## Development Tips

### Hot Reload
Flask automatically reloads when you save files in development mode:
```bash
# Already enabled when FLASK_ENV=development
flask run --reload
```

### Debug Mode
Enable debug mode for detailed error messages:
```bash
# In .env file
FLASK_ENV=development
FLASK_DEBUG=1
```

### Browser Console
- Press `F12` to open Developer Tools
- Check **Console** tab for JavaScript errors
- Check **Network** tab for API call issues
- Check **Application** tab for session data

### Test Different User Roles
The Review Data page has role-based features:
- **Admin**: Can view all data (read-only)
- **Engineer**: Can edit and save data
- **Viewer**: Read-only access

## Backend API Endpoints Used

The Review Data page communicates with these backend endpoints:

```plaintext
GET  /works/{work_id}/review-data          # Get review page data
GET  /api/works/{work_id}/components       # Get components data
POST /api/works/{work_id}/components/bulk  # Save multiple components
POST /api/works/{work_id}/validate         # Validate all data
```

## Security Best Practices

### SECRET_KEY Security
⚠️ **Important:**
1. **Never commit** your SECRET_KEY to Git
2. **Use different keys** for development and production
3. **Keep it long** (at least 32 characters)
4. **Keep it random** (don't use predictable values like "mysecretkey")
5. **Regenerate** if you suspect it's been compromised

### .gitignore
Ensure your `.gitignore` includes:
```gitignore
# Environment variables
.env
.env.local
.env.production

# Python
__pycache__/
*.pyc
*.pyo
venv/
```

## Stopping the Application

Press `Ctrl + C` in the terminal to stop the Flask server.

If using virtual environment, deactivate it:
```bash
deactivate
```

## Full Setup Script (Copy & Paste)

**For Quick Setup - Run all at once:**

```powershell
# Navigate to project
cd "Workshop-II-AutoRBI-WebApp\frontend"

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate and create .env file
$secretKey = python -c "import secrets; print(secrets.token_hex(32))"
@"
SECRET_KEY=$secretKey
FLASK_APP=app.py
FLASK_ENV=development
BACKEND_URL=http://localhost:8000
SESSION_TYPE=filesystem
"@ | Out-File -FilePath .env -Encoding utf8

# Run the application
python app.py
```

## Next Steps

1. ✅ Run the frontend application
2. ✅ Test the Review Data page
3. ✅ Try editing fields (as Engineer)
4. ✅ Save changes
5. ✅ Validate data
6. 🔄 Ensure backend is running
7. 🔄 Test API integration
8. 🔄 Add real database data
9. 🔄 Test with multiple equipment/components

## Need Help?

### Check Logs
```bash
# View Flask logs in terminal
# Check for error messages and stack traces
```

### Common Debug Commands
```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check if Flask is installed
pip show flask

# Check environment variables
type .env

# Test SECRET_KEY is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('SECRET_KEY:', 'Found' if os.getenv('SECRET_KEY') else 'Not Found')"
```

### View Application Configuration
```bash
# Start Python
python

# Check config
>>> from app import app
>>> print(app.config['SECRET_KEY'][:10] + '...')  # First 10 chars
>>> exit()
```

## Notes for Backend Developer

### Important Files
- **Main App**: `frontend/app.py`
- **Template**: `frontend/templates/works/review_data.html`
- **Routes**: `frontend/routes/works.py`
- **API Client**: `frontend/utils/api_client.py`

### API Integration Points
The frontend expects these API responses:

**GET /works/{work_id}/review-data**
```json
{
  "work": {
    "id": 1,
    "name": "Plant A - 2024 Inspection",
    "status": "in_progress"
  },
  "equipment_list": [
    {
      "equipment_number": "EQ-001",
      "equipment_description": "Heat Exchanger",
      "components": [
        {
          "id": 1,
          "component_name": "Shell",
          "phase": "Liquid",
          "fluid": "Water",
          "material_type": "Carbon Steel",
          "material_spec": "ASTM A516",
          "material_grade": "Grade 70",
          "insulation": true,
          "design_temp": 350,
          "design_pressure": 15.5,
          "operating_temp": 280,
          "operating_pressure": 12.0
        }
      ]
    }
  ]
}
```

**POST /api/works/{work_id}/components/bulk**
```json
{
  "components": [
    {
      "id": 1,
      "fluid": "Water",
      "material_type": "Carbon Steel",
      "design_temp": 350
      // ... other modified fields
    }
  ]
}
```

---

**Last Updated**: January 7, 2026  
**Version**: 1.0  
**Maintained by**: Frontend Development Team  
**Contact**: [Your Contact Information]
