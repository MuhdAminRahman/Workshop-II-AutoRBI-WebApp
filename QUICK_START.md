# Quick Start Guide - Running Frontend with Deployed Backend

## Prerequisites
- Python 3.8+ installed
- pip installed

## Setup Steps

### 1. Install Dependencies

```bash
cd frontend
pip install -r requirements.txt
```

Or install manually:
```bash
pip install flask flask-session flask-cors python-dotenv werkzeug jinja2 requests flask-socketio
```

### 2. Create Environment File

Create a `.env` file in the `frontend` directory:

```plaintext
SECRET_KEY=your-generated-secret-key-here
FLASK_APP=app.py
FLASK_ENV=development
DEBUG=True
BACKEND_API_URL=https://workshop-ii-autorbi-webapp.onrender.com
BACKEND_WS_URL=wss://workshop-ii-autorbi-webapp.onrender.com
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Run the Frontend

```bash
# From the frontend directory
python app.py
```

Or using Flask CLI:
```bash
flask run
```

The app will be available at: **http://localhost:5000**

## Accessing Work History

1. **Login** to the application
2. **Navigate** to "Work History" from the sidebar
3. **Filter** activities by:
   - Time period (1, 7, 14, 30, 90 days)
   - Specific work

## Testing Backend Connection

Run the test script from the project root:
```bash
python test_history_api.py
```

## Default Ports
- Frontend: `http://localhost:5000`
- Backend (Deployed): `https://workshop-ii-autorbi-webapp.onrender.com`

## Troubleshooting

### Issue: Module not found
```bash
pip install -r requirements.txt
```

### Issue: Port already in use
Change the port in `app.py`:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5001)
```

### Issue: Backend connection error
- Check internet connection
- Verify backend URL in config.py
- Check if deployed backend is running

## Features Available

✅ User Authentication  
✅ Works Management  
✅ Equipment Management  
✅ Data Extraction  
✅ Reports Generation  
✅ Analytics Dashboard  
✅ **Work History** (Activity Logs)  
✅ Admin Panel (for Admin users)

## Login Credentials

You'll need to create a user account or use existing credentials. Contact the admin if you need access.

## Need Help?

- Check `FRONTEND_SETUP.md` for detailed setup instructions
- Check `WORK_HISTORY_IMPLEMENTATION.md` for work history feature details
- Review the backend API docs at: `https://workshop-ii-autorbi-webapp.onrender.com/docs`
