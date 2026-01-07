# AutoRBI Flask Frontend

Web frontend for the AutoRBI RBI Data Extraction Platform built with Flask.

## Features

- 🔐 User authentication (login/register with username & password)
- 📁 Works management (CRUD operations)
- 📤 PDF upload & AI-powered data extraction
- 📊 Real-time extraction progress via WebSocket
- 📄 Excel & PowerPoint report generation
- ✏️ In-browser Excel data editor
- 📈 Analytics dashboard with charts
- 📱 Responsive design with Bootstrap 5

## Tech Stack

- **Backend**: Flask 3.0
- **Frontend**: Bootstrap 5, jQuery, Chart.js
- **Real-time**: Flask-SocketIO
- **API Client**: Python requests library

## Project Structure

```
frontend/
├── app.py                  # Main Flask application
├── config.py               # Configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
│
├── routes/                 # Flask blueprints
│   ├── main.py             # Landing page, dashboard
│   ├── auth.py             # Login, register, logout
│   ├── works.py            # Works CRUD
│   ├── extract.py          # File upload & extraction
│   ├── reports.py          # Reports & downloads
│   └── analytics.py        # Analytics dashboard
│
├── utils/                  # Utility modules
│   ├── api_client.py       # Backend API wrapper
│   ├── auth_middleware.py  # Authentication decorators
│   └── helpers.py          # Helper functions
│
├── templates/              # Jinja2 templates
│   ├── base.html           # Base layout
│   ├── index.html          # Landing page
│   ├── auth/               # Login, register
│   ├── dashboard/          # Dashboard
│   ├── works/              # Works management
│   ├── extract/            # Upload & extraction
│   ├── reports/            # Reports & editor
│   └── analytics/          # Analytics dashboard
│
└── static/                 # Static files
    ├── css/
    │   └── style.css       # Custom styles
    └── js/
        └── main.js         # Common JavaScript
```

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- Backend FastAPI server running on http://localhost:8000

### 2. Installation

```bash
# Navigate to frontend directory
cd frontend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
BACKEND_API_URL=http://localhost:8000
BACKEND_WS_URL=ws://localhost:8000
ENVIRONMENT=development
```

### 4. Run the Application

```bash
# Development mode
python app.py

# Or using Flask CLI
flask run
```

The application will be available at: http://localhost:5000

## Usage

### 1. Register & Login

- Navigate to http://localhost:5000
- Click "Register" and create an account with:
  - Full Name
  - Username
  - Email
  - Password
  - Role (Engineer/Admin)
- Login with your username and password

### 2. Create Work Project

- Go to "Works" in the sidebar
- Click "Create New Work"
- Enter work name and description

### 3. Upload & Extract

- Go to "Upload & Extract"
- Select a work project
- Drag & drop or browse for a PDF file
- Click "Start Extraction"
- Watch real-time progress

### 4. View Reports

- Go to "Reports"
- Select a work project
- Download Excel or PowerPoint files
- Edit data in-browser

### 5. View Analytics

- Go to "Analytics"
- Select a work project
- View health score, charts, and metrics

## API Integration

The frontend communicates with the FastAPI backend via:

- **REST API**: For CRUD operations
- **WebSocket**: For real-time extraction progress
- **File Downloads**: For Excel/PowerPoint downloads

All API calls are handled through `utils/api_client.py`.

## Authentication Flow

1. User logs in with username/password
2. Backend returns JWT token
3. Token stored in Flask session
4. Token sent in Authorization header for all API requests
5. Middleware validates token on protected routes

## Development

### Adding New Pages

1. Create route in `routes/` directory
2. Create template in `templates/` directory
3. Register blueprint in `app.py`
4. Add navigation link in `templates/base.html`

### Styling

- Custom CSS in `static/css/style.css`
- Bootstrap 5 classes for components
- Bootstrap Icons for icons

### JavaScript

- Common functions in `static/js/main.js`
- Page-specific JS in template `extra_js` blocks

## Troubleshooting

### Backend Connection Error

- Ensure FastAPI backend is running on http://localhost:8000
- Check `BACKEND_API_URL` in `.env`

### WebSocket Connection Failed

- Ensure `BACKEND_WS_URL` is correct (ws:// not http://)
- Check backend WebSocket endpoint is accessible

### Session Errors

- Clear browser cookies
- Restart Flask application
- Check `SECRET_KEY` in `.env`

## Deployment

### Production Settings

Update `.env`:

```env
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=<strong-random-key>
BACKEND_API_URL=https://your-backend-url.com
BACKEND_WS_URL=wss://your-backend-url.com
```

### Using Gunicorn

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## License

MIT License - see LICENSE file for details

## Support

For issues or questions, please open an issue on GitHub.
